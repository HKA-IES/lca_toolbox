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
    method_config = {"impact_categories": impact_categories,}

    demands = {str(act.id): {act.id: 1} for act in activities}
    demands.update({str(bact.id): {bact.id: 1} for bact in background_activities})

    dependent_parameters = []
    independent_parameters = []
    for param in ProjectParameter.select():
        if param.formula is None:
            independent_parameters.append(param)
        else:
            dependent_parameters.append(param)

    scores = []
    scores_background = []
    parameters = []

    for i in range(n_iterations):
        # Sample parameters
        for param in ProjectParameter.select():
            if param.formula is None:
                mc_rng = stats_arrays.MCRandomNumberGenerator(param.data["uncertainty"])
                new_value = mc_rng.next()[0]
                ProjectParameter.update(amount=new_value).where(ProjectParameter.name == param.name).execute()
        Group.get(name="project").expire()
        bd.parameters.recalculate()
        ActivityParameter.recalculate_exchanges("group")

        data_objs = bd.get_multilca_data_objs(functional_units=demands,
                                          method_config=method_config)

        lca = bc.MultiLCA(demands=demands,
                          method_config=method_config,
                          data_objs=data_objs,
                          use_distributions=True)
        lca.lci()
        lca.lcia()

        for act in activities:
            row = {"iteration": i,
                   "activity": (act["name"], act["location"])}
            for ic in impact_categories:
                row[ic] = lca.scores[ic, str(act.id)]
            scores.append(row)

        for bact in background_activities:
            row = {"iteration": i,
                   "activity": (bact["name"], bact["location"])}
            for ic in impact_categories:
                row[ic] = lca.scores[ic, str(bact.id)]
            scores_background.append(row)

        for param in ProjectParameter.select():
            if param.formula is None:
                param_type = "independent"
            else:
                param_type = "dependent"
            parameters.append({"iteration": i,
                               "name": param.name,
                               "type": param_type,
                               "value": param.amount})

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
