# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, Dict, List, Any
import copy

# import third-party modules
import bw2data as bd

# import your own module

# ActivityTuple: ("name", "product", "location", "database")
ActivityTuple = Tuple[str, str, str, str]

# ImpactCategoryTuple: ("database", "method", "impact_category", "metric")
ImpactCategoryTuple = Tuple[str, str, str, str]

# ScoresDict: {act0: {ic0: [0.2, ...],
#                     ic1: [0.3, ...],},}
ScoresDict = Dict[ActivityTuple, Dict[ImpactCategoryTuple, List[float]]]

# ParametersDict: {"param0": {"type": "independent" OR "dependent",
#                             "values": [3, ...]},}
ParametersDict = Dict[str, Dict[str, Any]]

def act_tuple(activity: bd.backends.proxies.Activity) -> ActivityTuple:
    try:
        product = activity["reference product"]
    except KeyError:
        product = None
    return activity["name"], product, activity["location"], activity["database"]

def concat_scores_dicts(scores_1: ScoresDict, scores_2: ScoresDict) -> ScoresDict:
    # Check that dicts have the same keys
    if scores_1.keys() != scores_2.keys():
        raise ValueError("scores_1 and scores_2 must have the same activities.")
    for act_scores_1, act_scores_2 in zip(scores_1.values(), scores_2.values()):
        if act_scores_1.keys() != act_scores_2.keys():
            raise ValueError("scores_1 and scores_2 must have the same impact categories.")

    # Concatenate
    concat_scores = copy.deepcopy(scores_1)
    for act_key in scores_2.keys():
        for ic_key, ic_scores in scores_2[act_key].items():
            concat_scores[act_key][ic_key] += ic_scores

    return concat_scores

def concat_parameters_dicts(params_1: ParametersDict, params_2: ParametersDict) -> ParametersDict:
    # Check that dicts have the same keys
    if params_1.keys() != params_2.keys():
        raise ValueError("params_1 and params_2 must have the same parameters.")

    # Concatenate
    concat_parameters = copy.deepcopy(params_1)
    for param_key in params_2.keys():
        concat_parameters[param_key]["values"] += params_2[param_key]["values"]

    return concat_parameters

def get_exchange(id_: int) -> bd.backends.Exchange:
    ED = bd.backends.schema.ExchangeDataset
    qs = ED.select().where(ED.id == id_)
    exc = bd.backends.Exchange(qs[0])
    return exc
