# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict

# import third-party modules
import bw2data as bd
import bw2io as bi
import pandas as pd
import numpy as np
from bw2data.parameters import ProjectParameter
import stats_arrays
import bw2calc as bc

# import your own module
import lcatoolbox

if __name__ == "__main__":
    """
    This script tries to run functions of this package on all the ecoinvent activities and identify special cases where 
    an error occurs.
    """

    bd.projects.set_current("lca_toolbox_tests")
    if 'ecoinvent-3.12-cutoff' in bd.databases:
        print('ecoinvent 3.12 is already present in the project')
        # del bd.databases['ecoinvent-3.12-cutoff']
        # del bd.databases['ecoinvent-3.12-biosphere']
    else:
        bi.import_ecoinvent_release(
            version='3.12',
            system_model='cutoff',  # can be cutoff / apos / consequential / EN15804
        )
    try:
        del bd.databases["foreground"]
        ProjectParameter.drop_table(safe=True, drop_sequences=True)
        ProjectParameter.create_table()
    except KeyError:
        pass
    foreground = bd.Database("foreground")
    foreground.register()

    ecoinvent = bd.Database("ecoinvent-3.12-cutoff")
    impact_categories = lcatoolbox.get_impact_categories("EF v3.1")

    n_activities = len(ecoinvent)

    for i, act in enumerate(ecoinvent):
        print(f"Activity {i+1}/{n_activities}: {act["name"]} - {act["location"]} - {act["reference product"]}")

        # Reset foreground
        del bd.databases["foreground"]
        ProjectParameter.drop_table(safe=True, drop_sequences=True)
        ProjectParameter.create_table()
        foreground = bd.Database("foreground")
        foreground.register()

        # Original activity
        try:
            scores, parameters = lcatoolbox.calculate_scores([act], impact_categories)
            mc_scores, mc_scores_background, mc_parameters = lcatoolbox.run_monte_carlo([act], impact_categories, 1, progress_bar=False)
            # contributions = lcatoolbox.contributions_tree(act, 1, impact_categories[0], max_depth=1)
        except Exception:
            pass

        # Copy
        try:
            act_copy = lcatoolbox.copy_ecoinvent_activity(act)
            # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
            # Why? I don't know...
            _ = bc.LCA(demand={act_copy.id: 1}, method=impact_categories[0])
            scores_copy, parameters_copy = lcatoolbox.calculate_scores([act_copy], impact_categories)
            mc_scores_copy, mc_scores_background_copy, mc_parameters_copy = lcatoolbox.run_monte_carlo([act_copy], impact_categories, 1, progress_bar=False)
            # contributions_copy = lcatoolbox.contributions_tree(act_copy, 1, impact_categories[0], max_depth=1)
        except Exception:
            pass
