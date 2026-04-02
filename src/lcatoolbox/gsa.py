# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict, Any

# import third-party modules
import bw2data as bd
import stats_arrays
from bw2data.parameters import ProjectParameter, ActivityParameter, Group
import bw2calc as bc
import pandas as pd
import stats_arrays
import numpy as np

# import your own module


def global_sensitivity_analysis(scores_df: pd.DataFrame,
                                scores_background_df: pd.DataFrame,
                                parameters_df: pd.DataFrame,
                                algorithm: str,
                                n_bins: int) -> pd.DataFrame:
    alg_map = {"main_effect_li_2016_alg_1": li_2016_main_effect_alg_1,
                     "main_effect_li_2016_alg_2": li_2016_main_effect_alg_2}

    if algorithm not in list(alg_map.keys()):
        raise ValueError(f"algorithm {algorithm} is not supported.")

    impact_categories = list(scores_df.columns)[2:]

    results = []

    if scores_background_df is not None:
        for act in scores_df["activity"].unique():
            for bact in scores_background_df["activity"].unique():
                row = {"activity": act,
                       "type": "background",
                                "name": bact}
                for ic in impact_categories:
                    value = alg_map[algorithm](np.array(scores_background_df[scores_background_df["activity"] == bact][ic]),
                                                      np.array(scores_df[scores_df["activity"] == act][ic]),
                                                      M = n_bins)
                    row[ic] = value
                results.append(row)

    if parameters_df is not None:
        for act in scores_df["activity"].unique():
            for param in parameters_df["name"].unique():
                row = {"activity": act,
                       "type": "parameter",
                       "name": param}
                for ic in impact_categories:
                    value = alg_map[algorithm](np.array(parameters_df[parameters_df["name"] == param]["value"]),
                                                      np.array(scores_df[scores_df["activity"] == act][ic]),
                                                      M = n_bins)
                    row[ic] = value
                results.append(row)

    results_df = pd.DataFrame(results)
    return results_df

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
