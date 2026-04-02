# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict, Any

# import third-party modules
import bw2data as bd
import bw2calc as bc
import pandas as pd

# import your own module

def contributions_tree(activity: bd.backends.proxies.Activity,
                       amount: float,
                       impact_category: Tuple[str, str, str, str],
                       max_depth: int) -> pd.DataFrame:
    """
    [...]

    Parameters
    ----------
    activity: bd.backends.proxies.Activity
        Activity for which the contributions should be analyzed.
    amount: float
        Amount of the activity to consider.
    impact_category: Tuple[str, str, str, str]
        Brightway tuple of the impact category to consider.
    max_depth: int
        Maximum depth to consider. Must be an integer higher than 0. max_depth=0 considers only the provided activity,
        max_depth=1 the contributions of the exchanges of activity, etc.

    Returns
    -------
    contributions_tree: pd.DataFrame
        Contributions tree in the form of a pandas DataFrame. Each contribution is a row and the columns are [...].
    """
    # TODO: Enforce ordering of contributions same as openLCA?
    # implementation adapted from https://github.com/brightway-lca/brightway2/blob/master/notebooks/Contribution%20analysis%20and%20comparison.ipynb

    # First generate demands for all activities down to max_depth, so that we can compute the scores all at once. This saves a lot of time.
    demands = {str(activity.id): {activity.id: 1}}
    def generate_demands_from_exchanges(activity, max_depth: int) -> Dict[str, Dict[str, int]]:
        demands = {}

        for exc in activity.technosphere():
            if list(exc.input.production())[0].amount > 0:
                demands[str(exc.input.id)] = {exc.input.id: 1}
            else:
                # Account for waste activities whose reference amount is negative.
                demands[str(exc.input.id)] = {exc.input.id: -1}

            if max_depth > 0:
                demands.update(generate_demands_from_exchanges(exc.input, max_depth-1))
        return demands
    demands.update(generate_demands_from_exchanges(activity, max_depth))

    method_config = {"impact_categories": [impact_category]}
    data_objs = bd.get_multilca_data_objs(functional_units=demands,
                                          method_config=method_config)
    lca = bc.MultiLCA(demands=demands,
                  method_config=method_config,
                  data_objs=data_objs)
    lca.lci()
    lca.lcia()

    def get_contributions(parent_act: bd.backends.proxies.Activity,
                          act: bd.backends.proxies.Activity,
                          amount: float,
                          depth: int,
                          max_depth: int) -> List[Dict[str, Any]]:
        # Account for waste activities whose reference amount is negative.
        production_amount = list(act.production())[0].amount
        if production_amount < 0:
            amount *= -1

        if amount == 0:
            return []
        contributions = []

        if parent_act is None:
            contributions.append({"activity_name": act["name"],
                                       "activity_location": act["location"],
                                       "parent_name": None,
                                       "parent_location": None,
                                       "depth": depth,
                                       "amount": amount,
                                       "unit": act["unit"],
                                       "score": amount*lca.scores[impact_category, str(act.id)]})
        else:
            contributions.append({"activity_name": act["name"],
                                       "activity_location": act["location"],
                                       "parent_name": parent_act["name"],
                                       "parent_location": parent_act["location"],
                                       "depth": depth,
                                       "amount": amount,
                                       "unit": act["unit"],
                                       "score": amount*lca.scores[impact_category, str(act.id)]})

        if depth < max_depth:
            for exc in act.technosphere():
                contributions += get_contributions(act, exc.input, amount*exc.amount/abs(production_amount), depth + 1, max_depth)
        return contributions

    contributions = get_contributions(None, activity, amount, 0, max_depth)
    df = pd.DataFrame(contributions)
    total_score = amount*lca.scores[impact_category, str(activity.id)]
    df["contribution"] = df["score"] / total_score

    return df

def grouped_contributions(activity: bd.backends.proxies.Activity,
                       amount: float,
                       impact_category: Tuple[str, str, str, str],
                       max_depth: int) -> pd.DataFrame:
    """
    [...]

    Parameters
    ----------
    activity: bd.backends.proxies.Activity
        Activity for which the contributions should be analyzed.
    amount: float
        Amount of the activity to consider.
    impact_category: Tuple[str, str, str, str]
        Brightway tuple of the impact category to consider.
    max_depth: int
        Maximum depth to consider. Must be an integer higher than 0. max_depth=0 considers only the provided activity,
        max_depth=1 the contributions of the exchanges of activity, etc.

    Returns
    -------
    grouped_contributions: pd.DataFrame
        Grouped contributions in the form of a pandas DataFrame. Each group is a row and the columns are [...].
    """
    # TODO: Enforce ordering of contributions?
    # implementation adapted from https://github.com/brightway-lca/brightway2/blob/master/notebooks/Contribution%20analysis%20and%20comparison.ipynb

    # First generate demands for all activities down to max_depth, so that we can compute the scores all at once. This saves a lot of time.

    # Note: this is NOT the same function as in contributions_tree
    demands = {str(activity.id): {activity.id: 1}}
    def generate_demands_from_exchanges(activity, max_depth: int) -> Dict[str, Dict[str, int]]:
        demands = {}

        for exc in activity.technosphere():
            if exc["group"] is not None:
                if list(exc.input.production())[0].amount > 0:
                    demands[str(exc.input.id)] = {exc.input.id: 1}
                else:
                    # Account for waste activities whose reference amount is negative.
                    demands[str(exc.input.id)] = {exc.input.id: -1}
            else:
                if max_depth == 0:
                    raise RuntimeError(f"Max depth reached but no group found.")
                else:
                    demands.update(generate_demands_from_exchanges(exc.input, max_depth-1))
        return demands
    demands.update(generate_demands_from_exchanges(activity, max_depth))

    method_config = {"impact_categories": [impact_category]}
    data_objs = bd.get_multilca_data_objs(functional_units=demands,
                                          method_config=method_config)
    lca = bc.MultiLCA(demands=demands,
                  method_config=method_config,
                  data_objs=data_objs)
    lca.lci()
    lca.lcia()

    # Note: this is NOT the same function as in contributions_tree
    def get_contributions(act: bd.backends.proxies.Activity,
                          amount: float,
                          max_depth: int = 5) -> Dict[str, Any]:
        # Account for waste activities whose reference amount is negative.
        production_amount = list(act.production())[0].amount
        if production_amount < 0:
            amount *= -1

        if amount == 0:
            return {}
        grouped_contributions = {}

        for exc in act.technosphere():
            if exc["group"] is not None:
                exc_amount = exc.amount
                exc_production_amount = list(exc.input.production())[0].amount
                if exc_production_amount < 0:
                    exc_amount *= -1
                try:
                    grouped_contributions[exc["group"]] += lca.scores[impact_category, str(exc.input.id)]*amount*exc_amount/abs(production_amount)
                except KeyError:
                    grouped_contributions[exc["group"]] = lca.scores[impact_category, str(exc.input.id)]*amount*exc_amount/abs(production_amount)
            else:
                new_grouped_contributions = get_contributions(exc.input, exc.amount*amount/abs(production_amount), max_depth-1)
                for key, value in new_grouped_contributions.items():
                    try:
                        grouped_contributions[key] += value
                    except KeyError:
                        grouped_contributions[key] = value
        return grouped_contributions

    grouped_contributions = get_contributions(activity, amount, max_depth)
    df = pd.DataFrame(list(grouped_contributions.items()), columns=["group", "score"])
    total_score = amount*lca.scores[impact_category, str(activity.id)]
    df["contribution"] = df["score"] / total_score

    return df
