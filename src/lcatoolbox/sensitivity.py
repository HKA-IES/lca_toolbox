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

Method = Union[SobolSaltelliMethod, SobolLi2016Method, FASTMethod, RBDFASTMethod, PAWNMethod]

def uncertainty_apportioning(activities: List[bd.backends.proxies.Activity],
                             impact_categories: List[ImpactCategoryTuple],
                             method: Method,
                             progress_bar: bool = True)  -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if (isinstance(method, SobolSaltelliMethod) or
            isinstance(method, FASTMethod) or
            isinstance(method, RBDFASTMethod) or
            isinstance(method, PAWNMethod)):
        project_params = [p for p in ProjectParameter.select() if p.formula is None]
        if len(project_params) == 0:
            raise RuntimeError("No df_parameters in project, so not possible to do uncertainty apportioning.")

        salib_problem = {
            'names': [],
            'num_vars': 0,
            'bounds': [],
            'dists': []
        }

        for p in project_params:
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

        if isinstance(method, SobolSaltelliMethod):
            salib_param_values = salib_sample_sobol.sample(salib_problem,
                                                           N=method.N,
                                                           calc_second_order=method.calc_second_order,
                                                           scramble=method.scramble,
                                                           skip_values=method.skip_values,
                                                           seed=method.seed,)
        elif isinstance(method, FASTMethod):
            salib_param_values = salib_sample_fast.sample(salib_problem,
                                                          N=method.N,
                                                          M=method.M,
                                                          seed=method.seed,)
        elif isinstance(method, RBDFASTMethod) or isinstance(method, PAWNMethod):
            salib_param_values = salib_sample_latin.sample(salib_problem,
                                                          N=method.N,
                                                          seed=method.seed, )

        n_iterations = len(salib_param_values)

        # first iteration to generate df_scores, df_parameters
        start_time = time.time()
        param_values = {name: values for name, values in zip(salib_problem["names"], salib_param_values[0])}
        df_scores, df_parameters = calculate_scores(activities,
                                              impact_categories,
                                              param_values)
        elapsed = time.time() - start_time
        remaining = elapsed / 1 * n_iterations
        if progress_bar:
            _print_uncertainty_apportioning_progress(0, n_iterations, elapsed, remaining)

        for i in range(1, len(salib_param_values)):
            param_values = {name: values for name, values in zip(salib_problem["names"], salib_param_values[i])}

            df_scores_i, df_parameters_i = calculate_scores(activities,
                                                      impact_categories,
                                                      param_values)

            df_scores[f"value_{i}"] = df_scores_i["value_0"]
            df_parameters[f"value_{i}"] = df_parameters_i["value_0"]

            elapsed = time.time() - start_time
            remaining = elapsed / (i+1) * (n_iterations - i + 1)
            if progress_bar:
                _print_uncertainty_apportioning_progress(i, n_iterations, elapsed, remaining)

        ua_results = []
        value_cols = [f"value_{i}" for i in range(n_iterations)]
        for act in df_scores["activity"].unique():
            for ic in df_scores["impact_category"].unique():
                criteria = (df_scores["activity"] == act) & (df_scores["impact_category"] == ic)
                salib_Y = np.array(df_scores[criteria][value_cols]).flatten()
                if isinstance(method, SobolSaltelliMethod):
                    salib_Si = salib_analyze_sobol.analyze(salib_problem, salib_Y,
                                                           calc_second_order=method.calc_second_order,
                                                           num_resamples=method.num_resamples,
                                                           conf_level=method.conf_level,
                                                           print_to_console=method.print_to_console,
                                                           parallel=method.parallel,
                                                           n_processors=method.n_processors,
                                                           keep_resamples=method.keep_resamples,
                                                           seed=method.seed,)
                    S2_symmetric = np.nansum(np.dstack([salib_Si["S2"].T, salib_Si["S2"]]), 2)
                    S2_conf_symmetric = np.nansum(np.dstack([salib_Si["S2_conf"].T, salib_Si["S2_conf"]]), 2)
                    df = pd.DataFrame(data=np.concatenate([np.stack([salib_Si["S1"], salib_Si["S1_conf"], salib_Si["ST"],
                                                                      salib_Si["ST_conf"]], axis=-1), S2_symmetric, S2_conf_symmetric], axis=1),
                                                       columns=["S1", "S1_conf", "ST", "ST_conf"] +
                                                               [f"S2_{name}" for name in salib_Si.problem["names"]] +
                                                               [f"S2_{name}_conf" for name in salib_Si.problem["names"]])
                    df["S1_rank"] = df["S1"].rank(ascending=False)
                    df["ST_rank"] = df["ST"].rank(ascending=False)
                    for name in salib_Si.problem["names"]:
                        df[f"S2_{name}_rank"] = df[f"S2_{name}"].rank(ascending=False)
                    df["parameter"] = salib_Si.problem["names"]
                elif isinstance(method, FASTMethod):
                    salib_Si = salib_analyze_fast.analyze(salib_problem, salib_Y,
                                                          M=method.M,
                                                          num_resamples=method.num_resamples,
                                                          conf_level=method.conf_level,
                                                          print_to_console=method.print_to_console,
                                                          seed=method.seed,)
                    df = pd.DataFrame(data=np.stack([salib_Si["S1"], salib_Si["S1_conf"], salib_Si["ST"],
                                                                      salib_Si["ST_conf"]], axis=-1),
                                                       columns=["S1", "S1_conf", "ST", "ST_conf"])
                    df["S1_rank"] = df["S1"].rank(ascending=False)
                    df["ST_rank"] = df["ST"].rank(ascending=False)
                    df["parameter"] = salib_Si["names"]
                elif isinstance(method, RBDFASTMethod):
                    salib_Si = salib_analyze_rbd_fast.analyze(salib_problem,
                                                              salib_param_values,
                                                              salib_Y,
                                                          M=method.M,
                                                          print_to_console=method.print_to_console,
                                                          seed=method.seed,)
                    df = pd.DataFrame(
                        data=np.stack([salib_Si["S1"], salib_Si["S1_conf"]], axis=-1),
                        columns=["S1", "S1_conf"])
                    df["S1_rank"] = df["S1"].rank(ascending=False)
                    df["parameter"] = salib_Si["names"]
                elif isinstance(method, PAWNMethod):
                    salib_Si = salib_analyze_pawn.analyze(salib_problem,
                                                              salib_param_values,
                                                              salib_Y,
                                                          S=method.S,
                                                          print_to_console=method.print_to_console,
                                                          seed=method.seed,)
                    df = pd.DataFrame(
                        data=np.stack([salib_Si["minimum"], salib_Si["mean"], salib_Si["median"],
                                       salib_Si["maximum"], salib_Si["CV"], salib_Si["stdev"]], axis=-1),
                        columns=["minimum", "mean", "median", "maximum", "CV", "stdev"])
                    df["median_rank"] = df["median"].rank(ascending=False)
                    df["maximum_rank"] = df["maximum"].rank(ascending=False)
                    df["parameter"] = salib_Si["names"]
                df["activity"] = act
                df["impact_category"] = str(ic)
                ua_results.append(df)

        ua_df = pd.concat(ua_results, ignore_index=True)
        return ua_df, df_scores, df_parameters
    elif isinstance(method, SobolLi2016Method):
        # TODO: Integrate the Monte-Carlo-based estimations more cleanly.
        df_scores, df_scores_background, df_parameters = run_monte_carlo(activities,
                                                                impact_categories,
                                                                n_iterations=method.N,
                                                                progress_bar=progress_bar,)
        #activities = list(df_scores.keys())
        #background_activities = list(df_scores_background.keys())
        #impact_categories = list(df_scores[activities[0]].keys())

        ua_results = []
        value_cols = [f"value_{i}" for i in range(method.N)]

        for act in df_scores["activity"].unique():
            for ic in df_scores["impact_category"].unique():
                data = []
                index = []
                criteria = (df_scores["activity"] == act) & (df_scores["impact_category"] == ic)
                y = np.array(df_scores[criteria][value_cols]).flatten()
                for param in df_parameters["parameter"].unique():

                    if method.ignore_dependent and df_parameters[df_parameters["parameter"] == param]["type"].values[0] == "dependent":
                        continue

                    x = df_parameters[df_parameters["parameter"] == param][[f"value_{i}" for i in range(method.N)]].values.flatten()
                    S1_alg_1 = _main_effect_li_2016_alg_1(np.array(x), np.array(y), method.n_bins)
                    S1_alg_2 = _main_effect_li_2016_alg_2(np.array(x), np.array(y), method.n_bins)
                    index.append(param)
                    data.append({"S1_alg_1": S1_alg_1,
                                   "S1_alg_2": S1_alg_2,})
                for bact in df_scores_background["activity"].unique():
                    criteria = (df_scores_background["activity"] == bact) & (df_scores_background["impact_category"] == ic)
                    x = np.array(df_scores_background[criteria][value_cols]).flatten()
                    S1_alg_1 = _main_effect_li_2016_alg_1(np.array(x), np.array(y), method.n_bins)
                    S1_alg_2 = _main_effect_li_2016_alg_2(np.array(x), np.array(y), method.n_bins)
                    index.append(str(bact))
                    data.append({"S1_alg_1": S1_alg_1,
                                   "S1_alg_2": S1_alg_2,})
                df = pd.DataFrame(data)
                df["S1_alg_1_rank"] = df["S1_alg_1"].rank(ascending=False)
                df["S1_alg_2_rank"] = df["S1_alg_2"].rank(ascending=False)
                df["activity"] = act
                df["impact_category"] = str(ic)
                df["parameter"] = index
                ua_results.append(df)

        df_scores_combined = pd.concat([df_scores, df_scores_background])
        ua_df = pd.concat(ua_results, ignore_index=True)
        return ua_df, df_scores_combined, df_parameters
    else:
        raise ValueError("Unsupported method. Should be one of SobolSaltelliMethod, SobolLi2016Method, FASTMethod.")

def local_sensitivity_analysis(activities: List[bd.backends.proxies.Activity],
                               impact_categories: List[ImpactCategoryTuple],
                               parameters: List[str],
                               perturbation_size: float = 0.01) -> Dict[str, Dict[ImpactCategoryTuple, Dict[str, Dict[str, float]]]]:
    """
    For each parameter and each score, we compute the sensitivity and elasticity according to the following formulas:

    sensitivity = (score_perturbed - score_nominal) / (parameter_perturbed - parameter_nominal)
    elasticity = (parameter_nominal / score_nominal) * sensitivity
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
