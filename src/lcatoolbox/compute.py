# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict

# import third-party modules
import bw2data as bd
from bw2data.parameters import ProjectParameter, ActivityParameter, Group
import bw2calc as bc
import stats_arrays

# import your own module
from .types import ScoresDict, ParametersDict, ImpactCategoryTuple, activity_string


def calculate_scores(activities: List[bd.backends.proxies.Activity],
                      impact_categories: List[ImpactCategoryTuple],
                      parameters: Dict[str, float] = {},
                      use_exchange_distributions: bool = False,
                      use_parameters_distributions: bool = False) -> Tuple[ScoresDict, ParametersDict]:
    """
    Compute scores for all activities in activities (demand=1) and all impact_categories.
    All parameters are set to the values in parameters.

    If parameters are not specified, all parameters are sampled from their distribution
    (use_parameters_distributions=True) or set to their default values.

    """
    if len(activities) == 0:
        raise ValueError("No activities provided")
    if len(impact_categories) == 0:
        raise ValueError("Must specify at least one impact category")

    project_parameters = list(ProjectParameter.select())

    # Specified parameters are invalid if 1) parameter does not exist or 2) parameter is defined by a formula
    for param in parameters.keys():
        if param not in [proj_param.name for proj_param in project_parameters]:
            raise ValueError(f"Parameter {param} does not exist in the model.")
    for proj_param in project_parameters:
        if proj_param.formula is not None and proj_param.name in parameters.keys():
            raise ValueError(f"Parameter {proj_param.name} is not set because it is defined by the formula "
                              f"{proj_param.formula}. Set the value of the parameters of the formula instead.")

    params_to_update = []
    for proj_param in project_parameters:
        if proj_param.formula is not None:
            continue

        if proj_param.name in parameters.keys():
            new_value = parameters[proj_param.name]
        elif use_parameters_distributions:
            mc_rng = stats_arrays.MCRandomNumberGenerator(proj_param.data["uncertainty"])
            new_value = mc_rng.next()[0]
        else:
            new_value = proj_param.data["nominal"]

        params_to_update.append(proj_param)
        proj_param.amount = new_value
    if len(params_to_update) > 0:
        ProjectParameter.bulk_update(params_to_update, fields=[ProjectParameter.amount])

        Group.get(name="project").expire()
        bd.parameters.recalculate()
        ActivityParameter.recalculate_exchanges("group")

    demands = {}
    for act in activities:
        if list(act.production())[0].amount >= 0:
            demands[str(act.id)] = {act.id: 1}
        else:
            demands[str(act.id)] = {act.id: -1}
    method_config = {"impact_categories": impact_categories, }
    data_objs = bd.get_multilca_data_objs(functional_units=demands,
                                          method_config=method_config)

    lca = bc.MultiLCA(demands=demands,
                      method_config=method_config,
                      data_objs=data_objs,
                      use_distributions=use_exchange_distributions, )
    lca.lci()
    lca.lcia()

    # taking a copy of lca.scores because .scores is recalculated every time it is called.
    lca_scores = lca.scores

    scores = {}
    parameters = {}

    for act in activities:
        scores[activity_string(act)] = {}
        for ic in impact_categories:
            scores[activity_string(act)][ic] = [lca_scores[ic, str(act.id)]]

    for param in ProjectParameter.select():
        if param.formula is None:
            param_type = "independent"
        else:
            param_type = "dependent"
        parameters[param.name] = {"type": param_type,
                                  "values": [param.amount]}

    return scores, parameters
