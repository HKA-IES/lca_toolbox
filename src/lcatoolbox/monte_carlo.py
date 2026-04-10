# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict

# import third-party modules
import bw2data as bd
import pandas as pd
import numpy as np
from bw2data.parameters import ProjectParameter
import stats_arrays

# import your own module
from .compute import calculate_scores
from .types import (ScoresDict, ParametersDict, ImpactCategoryTuple, concat_scores_dicts, concat_parameters_dicts,
                    act_tuple)


# TODO: support providing arrays of parameters (for use with Saltelli sampling, for example)
def run_monte_carlo(activities: List[bd.backends.proxies.Activity],
                    impact_categories: List[ImpactCategoryTuple],
                    n_iterations: int,
                    foreground_db_name: str = "foreground",
                    progress_bar: bool = True) -> Tuple[ScoresDict, ScoresDict, ParametersDict]:
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

    # We instantiate one sampler for all parameters to save time on initiating the sampler and generating samples.
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

    # first iteration to generate scores, parameters
    scores, parameters = calculate_scores(activities + background_activities,
                                          impact_categories,
                                          param_values,
                                          use_exchange_distributions=True,
                                          use_parameters_distributions=True)
    if progress_bar:
        _print_monte_carlo_progress(0, n_iterations)

    # subsequent iterations
    for i in range(1, n_iterations):
        if len(project_params) > 0:
            param_values = {param.name: value for param, value in zip(project_params, params_array[:, i])}
        scores_i, parameters_i = calculate_scores(activities + background_activities,
                                                  impact_categories,
                                                  param_values,
                                                  use_exchange_distributions=True,
                                                  use_parameters_distributions=True)

        scores = concat_scores_dicts(scores, scores_i)
        parameters = concat_parameters_dicts(parameters, parameters_i)

        if progress_bar:
            _print_monte_carlo_progress(i, n_iterations)

    scores_background = {}
    for bact in background_activities:
        bact_tuple = act_tuple(bact)
        scores_background[bact_tuple] = scores[bact_tuple]
        del scores[bact_tuple]

    return scores, scores_background, parameters

def discernability_analysis(scores: ScoresDict) -> Dict[str, pd.DataFrame]:
    if len(scores) < 2:
        raise ValueError("scores must contain scores for at least two activities.")

    impact_categories = list(list(scores.values())[0].keys())
    activities = list(scores.keys())
    n_iterations = len(scores[activities[0]][impact_categories[0]])

    results = {}
    for ic in impact_categories:
        arr = np.zeros((len(activities), len(activities)))
        for i, act_i in enumerate(activities):
            for j, act_j in enumerate(activities):
                arr[i, j] = np.sum(np.array(scores[act_i][ic]) > np.array(scores[act_j][ic]))
        results[ic] = arr/n_iterations

    return results

def _print_monte_carlo_progress(iteration: int, total: int):
    # Adapted from https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    length = 50
    fill = '█'
    filledLength = int(length * (iteration+1) // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\rMonte Carlo: |{bar}| {iteration+1}/{total}')
    # Print New Line on Complete
    if iteration == total:
        print()
