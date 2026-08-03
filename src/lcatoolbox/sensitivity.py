# -*- coding: utf-8 -*-

# import built-in module
from typing import List, Dict, Union, Tuple
import warnings
import time
from dataclasses import dataclass

# import third-party modules
import bw2data as bd
import pandas as pd
import numpy as np
from bw2data.parameters import ProjectParameter
import stats_arrays
from SALib.sample import sobol as salib_sample_sobol
from SALib.sample import fast_sampler as salib_sample_fast
from SALib.sample import latin as salib_sample_latin
from SALib.analyze import sobol as salib_analyze_sobol
from SALib.analyze import fast as salib_analyze_fast
from SALib.analyze import rbd_fast as salib_analyze_rbd_fast
from SALib.analyze import pawn as salib_analyze_pawn
from SALib.analyze import delta as salib_analyze_delta
import scipy.stats as sp_stats

# import your own module
from .compute import calculate_scores
from .types import ImpactCategoryTuple, activity_string
from .monte_carlo import run_monte_carlo

@dataclass
class SobolSaltelliMethod:
    # See SALib documentation for parameters definition
    # https://salib.readthedocs.io/en/latest/api.html#sobol-sensitivity-analysis
    N: int
    calc_second_order: bool = True
    scramble: bool = True
    skip_values: int = 0
    seed: int | np.random.Generator | None = None
    num_resamples: int = 100
    conf_level: float = 0.95
    print_to_console: bool = False
    parallel: bool = False
    n_processors: int | None = None
    keep_resamples: bool = False

@dataclass
class SobolLi2016Method:
    """
    Estimator for the main effect proposed in [1].

    [1] C. Li and S. Mahadevan, “An efficient modularized sample-based method to estimate the first-order Sobol׳ index,” Reliability Engineering & System Safety, vol. 153, pp. 110–121, Sep. 2016, doi: 10.1016/j.ress.2016.04.012.
    """
    N: int
    n_bins: int
    seed: int | np.random.Generator | None = None
    ignore_dependent: bool = True

@dataclass
class FASTMethod:
    """
    FAST - Fast Fourier Amplitude Test
    """
    N: int
    M: int = 4
    seed: int | np.random.Generator | None = None
    num_resamples: int = 100
    conf_level: float = 0.95
    print_to_console: bool = False

@dataclass
class RBDFASTMethod:
    """
    RBD-FAST - Random Balance Designs Fourier Amplitude Test
    """
    N: int
    seed: int | np.random.Generator | None = None
    M: int = 10
    print_to_console: bool = False

@dataclass
class PAWNMethod:
    """
    PAWN Sensitivity Analysis
    """
    N: int
    seed: int | np.random.Generator | None = None
    S: int = 10
    print_to_console: bool = False

@dataclass
class DeltaMomentIndependentMethod:
    """
    Delta Moment-Independent Measure
    """
    N: int
    seed: int | np.random.Generator | None = None
    print_to_console: bool = False

@dataclass
class SpearmanRankCorrelationMethod:
    """
    Spearman Rank Correlation
    """
    N: int
    seed: int | np.random.Generator | None = None

Method = Union[SobolSaltelliMethod, SobolLi2016Method, FASTMethod, RBDFASTMethod, PAWNMethod,
DeltaMomentIndependentMethod, SpearmanRankCorrelationMethod]

# TODO: Add XGBoost feature importance, SHAP values?

def uncertainty_apportioning(activities: List[bd.backends.proxies.Activity],
                             impact_categories: List[ImpactCategoryTuple],
                             method: Method,
                             progress_bar: bool = True)  -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform uncertainty apportioning on a set of activities.

    Parameters
    ----------
    activities : List[bd.backends.proxies.Activity]
        List of activities.
    impact_categories : List[ImpactCategoryTuple]
        List of impact categories.
    method : Method
        Uncertainty apportioning method and associated parameters.
    progress_bar : bool
        If True, progress bar will be displayed.

    Returns
    -------
    results: pd.DataFrame
        Results as a DataFrame with columns "parameter" (name of the parameter), "activity", "impact_category", as well
         as the uncertainty apportioning results for a given method. Different methods yield different results. For
         each result, a column with suffix "_rank" is created with the descending rank of parameters according to this
         metric.
    scores: pd.DataFrame
        Calculate scores for each iteration of the process. Same structure as the outputs of .calculate_scores(),
        .run_monte_carlo().
    parameters: pd.DataFrame
        Parameters for each iteration of the process. Same structure as the outputs of .calculate_scores(),
        .run_monte_carlo().
    """
    project_params = [p for p in ProjectParameter.select() if p.formula is None]

    salib_problem = _get_salib_problem(project_params)

    if isinstance(method, SobolSaltelliMethod):
        salib_param_values = salib_sample_sobol.sample(salib_problem,
                                                       N=method.N,
                                                       calc_second_order=method.calc_second_order,
                                                       scramble=method.scramble,
                                                       skip_values=method.skip_values,
                                                       seed=method.seed, )
        include_background = False
    elif isinstance(method, FASTMethod):
        salib_param_values = salib_sample_fast.sample(salib_problem,
                                                      N=method.N,
                                                      M=method.M,
                                                      seed=method.seed, )
        include_background = False
    elif (isinstance(method, RBDFASTMethod) or
          isinstance(method, PAWNMethod) or
          isinstance(method, DeltaMomentIndependentMethod) or
          isinstance(method, SobolLi2016Method) or
          isinstance(method, SpearmanRankCorrelationMethod)):
        salib_param_values = salib_sample_latin.sample(salib_problem,
                                                       N=method.N,
                                                       seed=method.seed, )
        include_background = True
    if salib_problem["num_vars"] == 0 and not include_background:
        raise RuntimeError("No parameters to perform uncertainty apportioning.")

    n_iterations = len(salib_param_values)

    if include_background:
        background_activities = _get_background_activities(activities, "foreground")
    else:
        background_activities = []

    # first iteration to generate df_scores, df_parameters
    start_time = time.time()
    param_values = {name: values for name, values in zip(salib_problem["names"], salib_param_values[0])}
    df_scores, df_parameters = calculate_scores(activities+background_activities,
                                                impact_categories,
                                                param_values)
    elapsed = time.time() - start_time
    remaining = elapsed / 1 * n_iterations
    if progress_bar:
        _print_uncertainty_apportioning_progress(0, n_iterations, elapsed, remaining)

    for i in range(1, n_iterations):
        param_values = {name: values for name, values in zip(salib_problem["names"], salib_param_values[i])}

        df_scores_i, df_parameters_i = calculate_scores(activities+background_activities,
                                                        impact_categories,
                                                        param_values)

        df_scores[f"value_{i}"] = df_scores_i["value_0"]
        df_parameters[f"value_{i}"] = df_parameters_i["value_0"]

        elapsed = time.time() - start_time
        remaining = elapsed / (i + 1) * (n_iterations - i + 1)
        if progress_bar:
            _print_uncertainty_apportioning_progress(i, n_iterations, elapsed, remaining)

    if include_background:
        for bact in background_activities:
            bact_str = activity_string(bact)
            salib_problem["names"].append(bact_str)
            salib_problem["num_vars"] += 1
            salib_problem["bounds"].append(None)
            salib_problem["dists"].append(None)

    param_types = []
    for n in salib_problem["names"]:
        if n[0] == "(":
            param_types.append("background")
        else:
            param_types.append("foreground")

    ua_results = []
    value_cols = [f"value_{i}" for i in range(n_iterations)]
    for act in activities:
        act_str = activity_string(act)
        for ic in impact_categories:
            ic_str = str(ic)

            criteria = (df_scores["activity"] == act_str) & (df_scores["impact_category"] == ic_str)
            salib_Y = np.array(df_scores[criteria][value_cols]).flatten()

            salib_param_values_extended = salib_param_values
            if include_background:
                for bact in background_activities:
                    bact_str = activity_string(bact)
                    criteria = (df_scores["activity"] == bact_str) & (df_scores["impact_category"] == ic_str)

                    salib_param_values_extended = np.hstack([salib_param_values_extended,
                                                    np.swapaxes(np.array(df_scores[criteria][value_cols]), 0, 1)])


            if isinstance(method, SobolSaltelliMethod):
                salib_Si = salib_analyze_sobol.analyze(salib_problem, salib_Y,
                                                       calc_second_order=method.calc_second_order,
                                                       num_resamples=method.num_resamples,
                                                       conf_level=method.conf_level,
                                                       print_to_console=method.print_to_console,
                                                       parallel=method.parallel,
                                                       n_processors=method.n_processors,
                                                       keep_resamples=method.keep_resamples,
                                                       seed=method.seed, )
                S2_symmetric = np.nansum(np.dstack([salib_Si["S2"].T, salib_Si["S2"]]), 2)
                S2_conf_symmetric = np.nansum(np.dstack([salib_Si["S2_conf"].T, salib_Si["S2_conf"]]), 2)
                df = pd.DataFrame(data=np.concatenate([np.stack([salib_Si["S1"], salib_Si["S1_conf"], salib_Si["ST"],
                                                                 salib_Si["ST_conf"]], axis=-1), S2_symmetric,
                                                       S2_conf_symmetric], axis=1),
                                  columns=["S1", "S1_conf", "ST", "ST_conf"] +
                                          [f"S2_{name}" for name in salib_Si.problem["names"]] +
                                          [f"S2_{name}_conf" for name in salib_Si.problem["names"]])
                df["S1_rank"] = df["S1"].rank(ascending=False)
                df["ST_rank"] = df["ST"].rank(ascending=False)
                for name in salib_Si.problem["names"]:
                    df[f"S2_{name}_rank"] = df[f"S2_{name}"].rank(ascending=False)
            elif isinstance(method, FASTMethod):
                salib_Si = salib_analyze_fast.analyze(salib_problem, salib_Y,
                                                      M=method.M,
                                                      num_resamples=method.num_resamples,
                                                      conf_level=method.conf_level,
                                                      print_to_console=method.print_to_console,
                                                      seed=method.seed, )
                df = pd.DataFrame(data=np.stack([salib_Si["S1"], salib_Si["S1_conf"], salib_Si["ST"],
                                                 salib_Si["ST_conf"]], axis=-1),
                                  columns=["S1", "S1_conf", "ST", "ST_conf"])
                df["S1_rank"] = df["S1"].rank(ascending=False)
                df["ST_rank"] = df["ST"].rank(ascending=False)
            elif isinstance(method, RBDFASTMethod):
                salib_Si = salib_analyze_rbd_fast.analyze(salib_problem,
                                                          salib_param_values_extended,
                                                          salib_Y,
                                                          M=method.M,
                                                          print_to_console=method.print_to_console,
                                                          seed=method.seed, )
                df = pd.DataFrame(
                    data=np.stack([salib_Si["S1"], salib_Si["S1_conf"]], axis=-1),
                    columns=["S1", "S1_conf"])
                df["S1_rank"] = df["S1"].rank(ascending=False)
            elif isinstance(method, PAWNMethod):
                salib_Si = salib_analyze_pawn.analyze(salib_problem,
                                                      salib_param_values_extended,
                                                      salib_Y,
                                                      S=method.S,
                                                      print_to_console=method.print_to_console,
                                                      seed=method.seed, )
                df = pd.DataFrame(
                    data=np.stack([salib_Si["minimum"], salib_Si["mean"], salib_Si["median"],
                                   salib_Si["maximum"], salib_Si["CV"], salib_Si["stdev"]], axis=-1),
                    columns=["minimum", "mean", "median", "maximum", "CV", "stdev"])
                df["median_rank"] = df["median"].rank(ascending=False)
                df["maximum_rank"] = df["maximum"].rank(ascending=False)
            elif isinstance(method, DeltaMomentIndependentMethod):
                salib_Si = salib_analyze_delta.analyze(salib_problem,
                                                       salib_param_values_extended,
                                                       salib_Y,
                                                       print_to_console=method.print_to_console,
                                                       seed=method.seed, )
                df = pd.DataFrame(
                    data=np.stack([salib_Si["delta"], salib_Si["delta_conf"], salib_Si["S1"],
                                   salib_Si["S1_conf"]], axis=-1),
                    columns=["delta", "delta_conf", "S1", "S1_conf"])
                df["delta_rank"] = df["delta"].rank(ascending=False)
                df["S1_rank"] = df["S1"].rank(ascending=False)
            elif isinstance(method, SobolLi2016Method):
                data = []
                y = salib_Y
                for x in np.swapaxes(salib_param_values_extended, 0, 1):
                    S1_alg_1 = _main_effect_li_2016_alg_1(np.array(x), np.array(y), method.n_bins)
                    S1_alg_2 = _main_effect_li_2016_alg_2(np.array(x), np.array(y), method.n_bins)
                    data.append({"S1_alg_1": S1_alg_1,
                                 "S1_alg_2": S1_alg_2})
                df = pd.DataFrame(data)
                df["S1_alg_1_rank"] = df["S1_alg_1"].rank(ascending=False)
                df["S1_alg_2_rank"] = df["S1_alg_2"].rank(ascending=False)
            elif isinstance(method, SpearmanRankCorrelationMethod):
                data = []
                for x in np.swapaxes(salib_param_values_extended, 0, 1):
                    spearman = sp_stats.spearmanr(np.array(x), salib_Y)
                    data.append({"spearman": spearman.correlation})
                df = pd.DataFrame(data)
                df["spearman_rank"] = df["spearman"].rank(ascending=True)
            df["parameter"] = salib_problem["names"]
            df["type"] = param_types
            df["activity"] = act_str
            df["impact_category"] = ic_str
            ua_results.append(df)

    ua_df = pd.concat(ua_results, ignore_index=True)
    return ua_df, df_scores, df_parameters

def _get_salib_problem(project_parameters: List[ProjectParameter]) -> Dict:
    salib_problem = {
        'names': [],
        'num_vars': 0,
        'bounds': [],
        'dists': []
    }

    for p in project_parameters:
        # TODO: Verify proper conversion.
        p_uncertainty = p.data["uncertainty"]
        if p_uncertainty["uncertainty_type"] == stats_arrays.UniformUncertainty.id:
            salib_problem['dists'].append("unif")
            salib_problem['bounds'].append([p_uncertainty["minimum"][0], p_uncertainty["maximum"][0]])
        elif p_uncertainty["uncertainty_type"] == stats_arrays.TriangularUncertainty.id:
            salib_problem['dists'].append("triang")
            peak_percent = ((p_uncertainty["loc"][0] - p_uncertainty["minimum"][0]) /
                            (p_uncertainty["maximum"][0] - p_uncertainty["minimum"][0]))
            salib_problem['bounds'].append([p_uncertainty["minimum"][0], p_uncertainty["maximum"][0], peak_percent])
        elif p_uncertainty["uncertainty_type"] == stats_arrays.NormalUncertainty.id:
            if not np.isnan(p_uncertainty["minimum"]) and not np.isnan(p_uncertainty["maximum"]):
                salib_problem['dists'].append("truncnorm")
                salib_problem['bounds'].append([p_uncertainty["minimum"][0], p_uncertainty["maximum"][0],
                                                p_uncertainty["loc"][0], p_uncertainty["scale"][0]])
            else:
                salib_problem['dists'].append("norm")
                salib_problem['bounds'].append([p_uncertainty["loc"][0], p_uncertainty["scale"][0]])
        elif p_uncertainty["uncertainty_type"] == stats_arrays.LognormalUncertainty.id:
            # TODO: Check that these are the proper df_parameters
            salib_problem['dists'].append("lognorm")
            salib_problem['bounds'].append([p_uncertainty["loc"][0], p_uncertainty["scale"][0]])
        elif p_uncertainty["uncertainty_type"] == stats_arrays.WeibullUncertainty.id:
            salib_problem['dists'].append("weibull")
            salib_problem['bounds'].append([p_uncertainty["shape"][0], p_uncertainty["scale"][0],
                                            p_uncertainty["loc"][0]])
        else:
            warnings.warn(f"Parameter {p.name} ignored because it uses an unsupported uncertainty type.")
            continue
        salib_problem['names'].append(p.name)
        salib_problem["num_vars"] += 1

    return salib_problem

def _get_background_activities(activities: List[bd.backends.proxies.Activity],
                               foreground_db_name: str) -> List[bd.backends.proxies.Activity]:
    background_activities = []

    def get_background_activities(act: bd.backends.proxies.Activity, foreground_db_name: str) -> List[
        bd.backends.proxies.Activity]:
        background_activities = []
        for exc in act.technosphere():
            if exc.input["database"] == foreground_db_name:
                background_activities += get_background_activities(exc.input, foreground_db_name)
            else:
                background_activities.append(exc.input)
        return background_activities

    for act in activities:
        background_activities += get_background_activities(act, foreground_db_name)
    background_activities = list(set(background_activities))
    return background_activities

def local_sensitivity_analysis(activities: List[bd.backends.proxies.Activity],
                               impact_categories: List[ImpactCategoryTuple],
                               parameters: List[str],
                               perturbation_size: float = 0.01) -> Dict[str, Dict[ImpactCategoryTuple, Dict[str, Dict[str, float]]]]:
    """
    For each parameter and each score, we compute the sensitivity and elasticity according to the following formulas:

    sensitivity = (score_perturbed - score_nominal) / (parameter_perturbed - parameter_nominal)
    elasticity = (parameter_nominal / score_nominal) * sensitivity

    Parameters
    ----------
    activities : List[bd.backends.proxies.Activity]
        List of activities.
    impact_categories : List[ImpactCategoryTuple]
        List of impact categories.
    parameters : List[str]
        List of parameters to conduct sensitivity analysis on.
    perturbation_size: float = 0.01
        Size of the perturbation as a proportion of the nominal value.
        parameter_perturbed = (1 + perturbation_size) * parameter_nominal

    Returns
    -------
    results: Dict
        TODO: Finish doc here.
    """
    # First compute nominal scores
    df_scores_nominal, df_parameters_nominal = calculate_scores(activities,
                                  impact_categories,
                                  parameters={},
                                  use_exchange_distributions=False,
                                  use_parameters_distributions=False,)

    results = {}
    for act in activities:
        results[activity_string(act)] = {}
        for ic in impact_categories:
            results[activity_string(act)][ic] = {}

    for param in parameters:
        if not param in list(df_parameters_nominal["parameter"]):
            raise ValueError(f"Parameter {param} not found in the model.")

        param_nominal = df_parameters_nominal[df_parameters_nominal["parameter"] == param]["value_0"].values[0]
        param_perturbed = (1+perturbation_size) * param_nominal

        df_scores_perturbed, _ = calculate_scores(activities,
                                                impact_categories,
                                                parameters={param: param_perturbed},
                                                use_exchange_distributions=False,
                                                use_parameters_distributions=False,)

        for act in activities:
            for ic in impact_categories:
                criteria = (df_scores_nominal["activity"] == activity_string(act)) & (df_scores_nominal["impact_category"] == str(ic))
                score_nominal = df_scores_nominal[criteria]["value_0"].values[0]
                criteria = (df_scores_perturbed["activity"] == activity_string(act)) & (
                            df_scores_perturbed["impact_category"] == str(ic))
                score_perturbed = df_scores_perturbed[criteria]["value_0"].values[0]
                sensitivity = ((score_perturbed - score_nominal)
                               / (param_perturbed - param_nominal))
                elasticity = (param_nominal / score_nominal) * sensitivity
                results[activity_string(act)][ic][param] = {"sensitivity": sensitivity,
                                                      "elasticity": elasticity}

    return results

def discrete_sensitivity_analysis():
    raise NotImplementedError

def _print_uncertainty_apportioning_progress(iteration: int, total: int, seconds_elapsed: float, seconds_remaining: float):
    # Adapted from https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    length = 50
    fill = '█'
    filledLength = int(length * (iteration+1) // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\rUncertainty Apportioning: |{bar}| {iteration+1}/{total} ({seconds_elapsed:.1f} s elapsed, {seconds_remaining:.1f} s remaining)')
    # Print New Line on Complete
    if iteration == total:
        print()

def _main_effect_li_2016_alg_1(x: np.ndarray, y: np.ndarray, M: int):
    """
    Estimator for the main effect proposed in [1] (algorithm 1).

    [1] C. Li and S. Mahadevan, “An efficient modularized sample-based method to estimate the first-order Sobol׳ index,” Reliability Engineering & System Safety, vol. 153, pp. 110–121, Sep. 2016, doi: 10.1016/j.ress.2016.04.012.

    Parameters
    ----------
    x: np.ndarray
        random samples of x
    y: np.ndarray
        corresponding values of y
    M: int
        number of intervals
    """
    x_arg_sorted = np.argsort(x)
    intervals_length = int(np.floor(len(x_arg_sorted) / M))
    E_y = [np.mean(y[x_arg_sorted[m * intervals_length:(m+1)*intervals_length]]) for m in range(M)]
    S = np.var(E_y, ddof=1) / np.var(y[:M*intervals_length], ddof=1)
    return S

def _main_effect_li_2016_alg_2(x: np.ndarray, y: np.ndarray, M: int):
    """
    Estimator for the main effect proposed in [1] (algorithm 2).

    [1] C. Li and S. Mahadevan, “An efficient modularized sample-based method to estimate the first-order Sobol׳ index,” Reliability Engineering & System Safety, vol. 153, pp. 110–121, Sep. 2016, doi: 10.1016/j.ress.2016.04.012.

    Parameters
    ----------
    x: np.ndarray
        random samples of x
    y: np.ndarray
        corresponding values of y
    M: int
        number of intervals
    """
    x_arg_sorted = np.argsort(x)
    intervals_length = int(np.floor(len(x_arg_sorted) / M))
    V_y = [np.var(y[x_arg_sorted[m * intervals_length:(m+1)*intervals_length]], ddof=1) for m in range(M)]
    S = 1 - (np.mean(V_y) / np.var(y[:M*intervals_length], ddof=1))
    return S
