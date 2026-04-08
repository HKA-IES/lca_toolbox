# -*- coding: utf-8 -*-

# import built-in module
from typing import List

# import third-party modules
import bw2data as bd

# import your own module
from .types import ImpactCategoryTuple

def get_impact_categories(method: str) -> List[ImpactCategoryTuple]:
    impact_categories = []
    for ic in bd.methods:
        if ic[1] == method:
            impact_categories.append(ic)
    return impact_categories
