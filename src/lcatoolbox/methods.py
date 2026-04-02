# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List

# import third-party modules
import bw2data as bd

# import your own module

def get_impact_categories(method: str) -> List[Tuple[str, str, str, str]]:
    impact_categories = []
    for ic in bd.methods:
        if ic[1] == method:
            impact_categories.append(ic)
    return impact_categories
