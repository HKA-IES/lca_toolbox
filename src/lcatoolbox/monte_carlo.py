# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict

# import third-party modules
import bw2data as bd
import stats_arrays
from bw2data.parameters import ProjectParameter, ActivityParameter, Group
import bw2calc as bc
import pandas as pd
import stats_arrays
import numpy as np

# import your own module


def _calculate_scores(activities: List[bd.backends.proxies.Activity],
                      impact_categories: List[Tuple[str, str, str, str]],
                      parameters: Dict[str, float] = {},
                      use_exchange_distributions: bool = False,
                      use_parameters_distributions: bool = False) -> Tuple[List[Dict], List[Dict]]:
    """
    Compute scores for all activities in activities (demand=1) and all impact_categories.
    All parameters are set to the values in parameters.

    If parameters are not specified, all parameters are sampled from their distribution
    (use_parameters_distributions=True) or set to their default values.

    """
    for param in ProjectParameter.select():
        if param.formula is not None:
            if param.name in parameters.keys():
                warnings.warn(f"Parameter {param.name} is not set because it is defined by the formula "
                              f"{param.formula}. Set the value of the parameters of the formula instead.")
            continue

        if param.name in parameters.keys():
            new_value = parameters[param.name]
        elif use_parameters_distributions:
            mc_rng = stats_arrays.MCRandomNumberGenerator(param.data["uncertainty"])
            new_value = mc_rng.next()[0]
        else:
            new_value = param.data["default"]

        ProjectParameter.update(amount=new_value).where(ProjectParameter.name == param.name).execute()

    Group.get(name="project").expire()
    bd.parameters.recalculate()
    ActivityParameter.recalculate_exchanges("group")

    demands = {str(act.id): {act.id: 1} for act in activities}
    method_config = {"impact_categories": impact_categories, }
    data_objs = bd.get_multilca_data_objs(functional_units=demands,
                                          method_config=method_config)

    lca = bc.MultiLCA(demands=demands,
                      method_config=method_config,
                      data_objs=data_objs,
                      use_distributions=use_exchange_distributions, )
    lca.lci()
    lca.lcia()

    scores = []
    parameters = []

    for act in activities:
        row = {"activity": (act["name"], act["location"])}
        for ic in impact_categories:
            row[ic] = lca.scores[ic, str(act.id)]
        scores.append(row)

    for param in ProjectParameter.select():
        if param.formula is None:
            param_type = "independent"
        else:
            param_type = "dependent"
        parameters.append({"name": param.name,
                           "type": param_type,
                           "value": param.amount})

    return scores, parameters


# TODO: support providing arrays of parameters (for use with Saltelli sampling, for example)
def run_monte_carlo(activities: List[bd.backends.proxies.Activity],
                    impact_categories: List[Tuple[str, str, str, str]],
                    n_iterations: int,
                    foreground_db_name: str = "foreground") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # TODO: Handle n_jobs > 1

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

    scores = []
    scores_background = []
    parameters = []

    for i in range(n_iterations):
        scores_i, parameters_i = _calculate_scores(activities + background_activities,
                                                   impact_categories,
                                                   use_exchange_distributions=True,
                                                   use_parameters_distributions=True)
        for act in activities:
            for row in scores_i:
                if row["activity"] == (act["name"], act["location"]):
                    scores.append({"iteration": i, **row})
        for bact in background_activities:
            for row in scores_i:
                if row["activity"] == (bact["name"], bact["location"]):
                    scores_background.append({"iteration": i, **row})
        for row in parameters_i:
            parameters.append({"iteration": i, **row})
        _print_monte_carlo_progress(i, n_iterations)

    scores_df = pd.DataFrame(scores)
    scores_background_df = pd.DataFrame(scores_background)
    parameters_df = pd.DataFrame(parameters)
    return scores_df, scores_background_df, parameters_df

def discernability_analysis(scores_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    if len(scores_df["activity"].unique()) < 2:
        raise ValueError("scores_df must contain scores for at least two activities.")

    impact_categories = list(scores_df.columns)[2:]
    activities = list(scores_df["activity"].unique())
    n_iterations = scores_df["iteration"].max() + 1

    results = {}
    for ic in impact_categories:
        array = np.zeros((len(activities), len(activities)))
        for i, act_i in enumerate(activities):
            for j, act_j in enumerate(activities):
                act_i_values = np.array(scores_df[scores_df["activity"] == act_i][ic])
                act_j_values = np.array(scores_df[scores_df["activity"] == act_j][ic])
                array[i,j] = np.sum(act_i_values > act_j_values)
        results[ic] = pd.DataFrame(array/n_iterations, index=activities, columns=activities)

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