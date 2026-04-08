# -*- coding: utf-8 -*-

# import built-in module
from typing import List, Dict

# import third-party modules
import bw2data as bd
import pandas as pd
import numpy as np

# import your own module
from .compute import calculate_scores
from .types import ScoresDict, ParametersDict, ActivityTuple, ImpactCategoryTuple, act_tuple


def global_sensitivity_analysis(scores: ScoresDict,
                                scores_background: ScoresDict,
                                parameters: ParametersDict,
                                algorithm: str,
                                n_bins: int,
                                ignore_dependent: bool = True) -> Dict[ActivityTuple, Dict[ImpactCategoryTuple, pd.DataFrame]]:
    alg_map = {"main_effect_li_2016_alg_1": li_2016_main_effect_alg_1,
                     "main_effect_li_2016_alg_2": li_2016_main_effect_alg_2}

    if algorithm not in list(alg_map.keys()):
        raise ValueError(f"algorithm {algorithm} is not supported.")

    activities = list(scores.keys())
    background_activities = list(scores_background.keys())
    impact_categories = list(scores[activities[0]].keys())

    results = {}

    for act in activities:
        results[act] = {}
        for ic in impact_categories:
            raw_df = []
            y = scores[act][ic]
            for bact in background_activities:
                x = scores_background[bact][ic]
                s = alg_map[algorithm](np.array(x), np.array(y), n_bins)
                raw_df.append({"name": str(bact),
                               "type": "background",
                               "value": s})
            for param in parameters.keys():
                x = parameters[param]["values"]
                s = alg_map[algorithm](np.array(x), np.array(y), n_bins)
                raw_df.append({"name": param,
                               "type": "parameter",
                               "value": s})
            results[act][ic] = pd.DataFrame(raw_df)

    return results

def li_2016_main_effect_alg_1(x, y, M):
    """
    Algorithm 1 from [1]

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

def li_2016_main_effect_alg_2(x, y, M):
    """
    Algorithm 2 from [1]

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
