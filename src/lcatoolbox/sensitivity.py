# -*- coding: utf-8 -*-

# import built-in module
from typing import List, Dict, Union, Tuple, Literal
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

# import your own module
from .compute import calculate_scores
from .types import (ScoresDict, ParametersDict, ActivityTuple, ImpactCategoryTuple, act_tuple, concat_scores_dicts,
                    concat_parameters_dicts)
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
    alg: Literal[1, 2] = 1 # 1 or 2
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
    M: int = 4
    print_to_console: bool = False

Method = Union[SobolSaltelliMethod, SobolLi2016Method, FASTMethod, RBDFASTMethod]


# TODO: Support PAWN
# TODO: Unified formatting of UA results
def uncertainty_apportioning(activities: List[bd.backends.proxies.Activity],
                             impact_categories: List[ImpactCategoryTuple],
                             method: Method,
                             progress_bar: bool = True)  -> Tuple[Dict[ActivityTuple, Dict[ImpactCategoryTuple, Dict]],
ScoresDict, ParametersDict]:
    if isinstance(method, SobolSaltelliMethod) or isinstance(method, FASTMethod) or isinstance(method, RBDFASTMethod):
        project_params = [p for p in ProjectParameter.select() if p.formula is None]
        if len(project_params) == 0:
            raise RuntimeError("No parameters in project, so not possible to do uncertainty apportioning.")

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
                # TODO: Check that these are the proper parameters
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
        elif isinstance(method, RBDFASTMethod):
            salib_param_values = salib_sample_latin.sample(salib_problem,
                                                          N=method.N,
                                                          seed=method.seed, )

        n_iterations = len(salib_param_values)

        # first iteration to generate scores, parameters
        start_time = time.time()
        param_values = {name: values for name, values in zip(salib_problem["names"], salib_param_values[0])}
        scores, parameters = calculate_scores(activities,
                                              impact_categories,
                                              param_values)
        elapsed = time.time() - start_time
        remaining = elapsed / 1 * n_iterations
        if progress_bar:
            _print_uncertainty_apportioning_progress(0, n_iterations, elapsed, remaining)

        for i in range(1, len(salib_param_values)):
            param_values = {name: values for name, values in zip(salib_problem["names"], salib_param_values[i])}

            scores_i, parameters_i = calculate_scores(activities,
                                                      impact_categories,
                                                      param_values)

            scores = concat_scores_dicts(scores, scores_i)
            parameters = concat_parameters_dicts(parameters, parameters_i)

            elapsed = time.time() - start_time
            remaining = elapsed / (i+1) * (n_iterations - i + 1)
            if progress_bar:
                _print_uncertainty_apportioning_progress(i, n_iterations, elapsed, remaining)

        ua_results = {}
        for act in scores.keys():
            ua_results[act] = {}
            for ic in scores[act].keys():
                salib_Y = np.array(scores[act][ic])
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
                elif isinstance(method, FASTMethod):
                    salib_Si = salib_analyze_fast.analyze(salib_problem, salib_Y,
                                                          M=method.M,
                                                          num_resamples=method.num_resamples,
                                                          conf_level=method.conf_level,
                                                          print_to_console=method.print_to_console,
                                                          seed=method.seed,)
                elif isinstance(method, RBDFASTMethod):
                    salib_Si = salib_analyze_rbd_fast.analyze(salib_problem,
                                                              salib_param_values,
                                                              salib_Y,
                                                          M=method.M,
                                                          print_to_console=method.print_to_console,
                                                          seed=method.seed,)
                ua_results[act][ic] = salib_Si
        return ua_results, scores, parameters
    elif isinstance(method, SobolLi2016Method):
        # TODO: Integrate the Monte-Carlo-based estimations more cleanly.
        if method.alg == 1:
            alg_fn = _main_effect_li_2016_alg_1
        elif method.alg == 2:
            alg_fn = _main_effect_li_2016_alg_2

        scores, scores_background, parameters = run_monte_carlo(activities,
                                                                impact_categories,
                                                                n_iterations=method.N,
                                                                progress_bar=progress_bar,)
        activities = list(scores.keys())
        background_activities = list(scores_background.keys())
        impact_categories = list(scores[activities[0]].keys())

        ua_results = {}

        for act in activities:
            ua_results[act] = {}
            for ic in impact_categories:
                raw_df = []
                y = scores[act][ic]
                for bact in background_activities:
                    x = scores_background[bact][ic]
                    s = alg_fn(np.array(x), np.array(y), method.n_bins)
                    raw_df.append({"name": str(bact),
                                   "type": "background",
                                   "value": s})
                for param in parameters.keys():
                    if method.ignore_dependent and parameters[param]["type"] == "dependent":
                        continue

                    x = parameters[param]["values"]
                    s = alg_fn(np.array(x), np.array(y), method.n_bins)
                    raw_df.append({"name": param,
                                   "type": "parameter",
                                   "value": s})
                ua_results[act][ic] = pd.DataFrame(raw_df)

        scores_combined = dict(scores)
        scores_combined.update(scores_background)
        return ua_results, scores_combined, parameters
    else:
        raise ValueError("Unsupported method. Should be one of SobolSaltelliMethod, SobolLi2016Method, FASTMethod.")

def local_sensitivity_analysis(activities: List[bd.backends.proxies.Activity],
                               impact_categories: List[ImpactCategoryTuple],
                               parameters: List[str],
                               perturbation_size: float = 0.01) -> Dict[ActivityTuple, Dict[ImpactCategoryTuple, Dict[str, Dict[str, float]]]]:
    """
    For each parameter and each score, we compute the sensitivity and elasticity according to the following formulas:

    sensitivity = (score_perturbed - score_nominal) / (parameter_perturbed - parameter_nominal)
    elasticity = (parameter_nominal / score_nominal) * sensitivity
    """
    # First compute nominal scores
    scores_nominal, parameters_nominal = calculate_scores(activities,
                                  impact_categories,
                                  parameters={},
                                  use_exchange_distributions=False,
                                  use_parameters_distributions=False,)

    results = {}
    for act in activities:
        results[act_tuple(act)] = {}
        for ic in impact_categories:
            results[act_tuple(act)][ic] = {}

    for param in parameters:
        if not param in list(parameters_nominal.keys()):
            raise ValueError(f"Parameter {param} not found in the model.")

        param_nominal = parameters_nominal[param]["values"][0]
        param_perturbed = (1+perturbation_size) * param_nominal

        scores_perturbed, _ = calculate_scores(activities,
                                                impact_categories,
                                                parameters={param: param_perturbed},
                                                use_exchange_distributions=False,
                                                use_parameters_distributions=False,)

        for act in activities:
            for ic in impact_categories:
                score_nominal = scores_nominal[act_tuple(act)][ic][0]
                score_perturbed = scores_perturbed[act_tuple(act)][ic][0]
                sensitivity = ((score_perturbed - score_nominal)
                               / (param_perturbed - param_nominal))
                elasticity = (param_nominal / score_nominal) * sensitivity
                results[act_tuple(act)][ic][param] = {"sensitivity": sensitivity,
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
