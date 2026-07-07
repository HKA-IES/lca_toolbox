# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, Dict, List, Any
import copy

# import third-party modules
import bw2data as bd

# import your own module

# ImpactCategoryTuple: ("database", "method", "impact_category", "metric")
ImpactCategoryTuple = Tuple[str, str, str, str]

# ScoresDict: {act0: {ic0: [0.2, ...],
#                     ic1: [0.3, ...],},}
ScoresDict = Dict[str, Dict[ImpactCategoryTuple, List[float]]]

def activity_string(activity: bd.backends.proxies.Activity) -> str:
    try:
        product = activity["reference product"]
    except KeyError:
        product = None
    act_tuple = (activity["name"], product, activity["location"], activity["database"])
    return str(act_tuple)

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

def get_exchange(id_: int) -> bd.backends.Exchange:
    ED = bd.backends.schema.ExchangeDataset
    qs = ED.select().where(ED.id == id_)
    exc = bd.backends.Exchange(qs[0])
    return exc
