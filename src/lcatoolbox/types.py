# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple

# import third-party modules
import bw2data as bd

# import your own module

# ImpactCategoryTuple: ("database", "method", "impact_category", "metric")
ImpactCategoryTuple = Tuple[str, str, str, str]

def activity_string(activity: bd.backends.proxies.Activity) -> str:
    try:
        product = activity["reference product"]
    except KeyError:
        product = None
    act_tuple = (activity["name"], product, activity["location"], activity["database"])
    return str(act_tuple)

def get_exchange(id_: int) -> bd.backends.Exchange:
    ED = bd.backends.schema.ExchangeDataset
    qs = ED.select().where(ED.id == id_)
    exc = bd.backends.Exchange(qs[0])
    return exc
