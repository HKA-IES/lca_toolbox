# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict

# import third-party modules
import bw2data as bd
import pandas as pd
import numpy as np

# import your own module
from .compute import calculate_scores
from .types import (ScoresDict, ParametersDict, ImpactCategoryTuple, concat_scores_dicts, concat_parameters_dicts,
                    act_tuple)


# TODO: support providing arrays of parameters (for use with Saltelli sampling, for example)
def run_monte_carlo(activities: List[bd.backends.proxies.Activity],
                    impact_categories: List[ImpactCategoryTuple],
                    n_iterations: int,
                    foreground_db_name: str = "foreground") -> Tuple[ScoresDict, ScoresDict, ParametersDict]:
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

    scores, parameters = calculate_scores(activities + background_activities,
                                                   impact_categories,
                                                   use_exchange_distributions=True,
                                                   use_parameters_distributions=True)
    _print_monte_carlo_progress(0, n_iterations)

    for i in range(1, n_iterations):
        scores_i, parameters_i = calculate_scores(activities + background_activities,
                                                   impact_categories,
                                                   use_exchange_distributions=True,
                                                   use_parameters_distributions=True)

        scores = concat_scores_dicts(scores, scores_i)
        parameters = concat_parameters_dicts(parameters, parameters_i)

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
