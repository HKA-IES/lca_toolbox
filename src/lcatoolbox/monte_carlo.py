# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List
import time

# import third-party modules
import bw2data as bd
import pandas as pd
import numpy as np
from bw2data.parameters import ProjectParameter
import stats_arrays

# import your own module
from .compute import calculate_scores
from .types import ImpactCategoryTuple, activity_string


# TODO: support providing arrays of parameters (for use with Saltelli sampling, for example)
def run_monte_carlo(activities: List[bd.backends.proxies.Activity],
                    impact_categories: List[ImpactCategoryTuple],
                    n_iterations: int,
                    foreground_db_name: str = "foreground",
                    progress_bar: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # TODO: Handle n_jobs > 1
    n_iterations = int(n_iterations)
    if n_iterations < 1:
        raise ValueError("n_iterations must be greater than 0.")

    background_activities = []
    def get_background_activities(act: bd.backends.proxies.Activity, foreground_db_name: str) -> List[bd.backends.proxies.Activity]:
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

    # We instantiate one sampler for all df_parameters to save time on initiating the sampler and generating samples.
    project_params = [p for p in ProjectParameter.select() if p.formula is None]
    param_values = {}
    if len(project_params) > 0:
        uncertainty_params = np.array([proj_param.data["uncertainty"][0] for proj_param in project_params])
        param_sampler = stats_arrays.MCRandomNumberGenerator(uncertainty_params,
                                                         maximum_iterations=n_iterations)
        params_array = param_sampler.generate(n_iterations)
        if n_iterations == 1:
            param_values = {param.name: value for param, value in zip(project_params, params_array[:])}
        else:
            param_values = {param.name: value for param, value in zip(project_params, params_array[:, 0])}

    # first iteration to generate df_scores, df_parameters
    start_time = time.time()
    df_scores, df_parameters = calculate_scores(activities + background_activities,
                                          impact_categories,
                                          param_values,
                                          use_exchange_distributions=True,
                                          use_parameters_distributions=True)
    elapsed = time.time() - start_time
    remaining = elapsed / 1 * n_iterations
    if progress_bar:
        _print_monte_carlo_progress(0, n_iterations, elapsed, remaining)

    # subsequent iterations
    for i in range(1, n_iterations):
        if len(project_params) > 0:
            param_values = {param.name: value for param, value in zip(project_params, params_array[:, i])}
        df_scores_i, df_parameters_i = calculate_scores(activities + background_activities,
                                                  impact_categories,
                                                  param_values,
                                                  use_exchange_distributions=True,
                                                  use_parameters_distributions=True)
        df_scores[f"value_{i}"] = df_scores_i[f"value_0"]
        if len(df_parameters) > 0:
            df_parameters[f"value_{i}"] = df_parameters_i["value_0"]

        elapsed = time.time() - start_time
        remaining = elapsed / (i+1) * (n_iterations - i + 1)
        if progress_bar:
            _print_monte_carlo_progress(i, n_iterations, elapsed, remaining)

    # Separate background activities from target activities
    activities_rows_idx = df_scores["activity"].isin([activity_string(act) for act in activities])
    background_activities_rows_idx = df_scores["activity"].isin([activity_string(act) for act in background_activities])

    df_scores_background = df_scores.iloc[background_activities_rows_idx]
    df_scores = df_scores.iloc[activities_rows_idx]

    return df_scores, df_scores_background, df_parameters

def discernability_analysis(df_scores: pd.DataFrame) -> pd.DataFrame:
    activities = list(df_scores["activity"].unique())
    if len(activities) < 2:
        raise ValueError("scores must contain scores for at least two activities.")
    impact_categories = list(df_scores["impact_category"].unique())
    n_iterations = len(df_scores.columns) - 2
    value_cols = [f"value_{i}" for i in range(n_iterations)]

    results = []
    for ic in impact_categories:
        for act_A in activities:
            for act_B in activities:
                criteria_act_A = (df_scores["activity"] == act_A) & (df_scores["impact_category"] == ic)
                values_act_A = np.array(df_scores[criteria_act_A][value_cols]).flatten()
                criteria_act_B = (df_scores["activity"] == act_B) & (df_scores["impact_category"] == ic)
                values_act_B = np.array(df_scores[criteria_act_B][value_cols]).flatten()

                P_A_ov_B = np.sum(values_act_A > values_act_B) / n_iterations
                results.append({"activity_A": act_A,
                                "activity_B": act_B,
                                "impact_category": ic,
                                "P_A>B": P_A_ov_B})
    df_results = pd.DataFrame(results)
    return df_results

def _print_monte_carlo_progress(iteration: int, total: int, seconds_elapsed: float, seconds_remaining: float):
    # Adapted from https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    length = 50
    fill = '█'
    filledLength = int(length * (iteration+1) // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\rMonte Carlo: |{bar}| {iteration+1}/{total} ({seconds_elapsed:.1f} s elapsed, {seconds_remaining:.1f} s remaining)')
    # Print New Line on Complete
    if iteration == total:
        print()
