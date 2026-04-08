# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import numpy as np
import bw2data as bd
from bw2data.parameters import ProjectParameter

# import your own module
from lcatoolbox import run_monte_carlo, discernability_analysis, act_tuple
from setup_bw_project import imported_activities, setup_brightway

class TestMonteCarlo:


    def test_run_monte_carlo(self, imported_activities):
        activities = imported_activities
        background_activities = [bd.get_activity(name="beverage carton production, 1 L, for juice (ambient)",
                                                 location="RER"),
                                 bd.get_activity(name="orange production, processing grade",
                                                 location="RoW"),
                                 bd.get_activity(name="kiwi production", location="GLO"),
                                 bd.get_activity(name="apple production", location="IT"),
                                 bd.get_activity(name="anchovy, capture by wooden purse seiner and landing whole, fresh",
                                                 location="PE"),
                                 bd.get_activity(name="market for biowaste, kitchen and garden waste", location="GLO")
                                 ]

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use', 'user deprivation potential (deprivation-weighted water consumption)')]
        n_iterations = 5
        scores, scores_background, parameters = run_monte_carlo(activities=activities,
                                               impact_categories=impact_categories,
                                               n_iterations=n_iterations,)

        # Validation of scores
        assert set(scores.keys()) == set([act_tuple(act) for act in activities])
        for act_scores in scores.values():
            assert set(act_scores.keys()) == set(impact_categories)
            for ic_scores in act_scores.values():
                assert len(ic_scores) == n_iterations

        # Values differ from one iteration to the other
        assert (scores[act_tuple(activities[0])][impact_categories[0]][0]
                != scores[act_tuple(activities[0])][impact_categories[0]][1])

        # Values differ from one activity to the other
        assert (scores[act_tuple(activities[0])][impact_categories[0]][0]
                != scores[act_tuple(activities[1])][impact_categories[0]][0])

        # Values differ from one impact category to the other
        assert (scores[act_tuple(activities[0])][impact_categories[0]][0]
                != scores[act_tuple(activities[0])][impact_categories[1]][0])

        # Validation of scores_background
        assert (set(scores_background.keys())
                == set([act_tuple(bact) for bact in background_activities]))
        for act_scores_background in scores_background.values():
            assert set(act_scores_background.keys()) == set(impact_categories)
            for ic_scores_background in act_scores_background.values():
                assert len(ic_scores_background) == n_iterations

        # Values differ from one iteration to the other
        assert (scores_background[act_tuple(background_activities[0])][impact_categories[0]][0]
                != scores_background[act_tuple(background_activities[0])][impact_categories[0]][1])

        # Values differ from one activity to the other
        assert (scores_background[act_tuple(background_activities[0])][impact_categories[0]][0]
                != scores_background[act_tuple(background_activities[1])][impact_categories[0]][0])

        # Values differ from one impact category to the other
        assert (scores_background[act_tuple(background_activities[0])][impact_categories[0]][0]
                != scores_background[act_tuple(background_activities[0])][impact_categories[1]][0])

        # Validation of parameters
        assert len(parameters) == len(ProjectParameter.select())
        for param in ProjectParameter.select():
            assert param.name in list(parameters.keys())
            if param.formula is not None:
                assert parameters[param.name]["type"] == "dependent"
            else:
                assert parameters[param.name]["type"] == "independent"

            assert len(parameters[param.name]["values"]) == n_iterations

        # Correct values
        assert set(parameters.keys()) == {param.name for param in ProjectParameter.select()}

        # Values differ from one iteration to the other
        assert (parameters["some_random_value"]["values"][0]
                != parameters["some_random_value"]["values"][1])

        # Values differ from one parameter to the other
        assert (parameters["some_random_value"]["values"][0]
                != parameters["amount_beverage_carton"]["values"][0])

    def test_discernability_analysis(self):
        scores_act0_ic0 = [0, 1, 2, 3, 4]
        scores_act0_ic1 = [0, 1, 2, 3, 4]
        scores_act1_ic0 = [4, 3, 2, 1, 0]
        scores_act1_ic1 = [4, 3, 2, 1, 0]
        scores_act2_ic0 = [1, 2, 3, 4, 5]
        scores_act2_ic1 = [1, 2, 3, 4, 5]

        activities = [("act0", "loc0"),
                      ("act1", "loc1"),
                      ("act2", "loc2")]
        impact_categories = [("ic0_0", "ic0_1", "ic0_2", "ic0_3"),
                             ("ic1_0", "ic1_1", "ic1_2", "ic1_3"),]

        scores = {}
        scores[activities[0]] = {}
        scores[activities[0]][impact_categories[0]] = scores_act0_ic0
        scores[activities[0]][impact_categories[1]] = scores_act0_ic1
        scores[activities[1]] = {}
        scores[activities[1]][impact_categories[0]] = scores_act1_ic0
        scores[activities[1]][impact_categories[1]] = scores_act1_ic1
        scores[activities[2]] = {}
        scores[activities[2]][impact_categories[0]] = scores_act2_ic0
        scores[activities[2]][impact_categories[1]] = scores_act2_ic1

        expected_results = {}
        expected_results[impact_categories[0]] = np.array([[0/5, 2/5, 0/5],
                                                           [2/5, 0/5, 2/5],
                                                           [5/5, 3/5, 0/5]])
        expected_results[impact_categories[1]] = np.array([[0/5, 2/5, 0/5],
                                                           [2/5, 0/5, 2/5],
                                                           [5/5, 3/5, 0/5]])

        actual_results = discernability_analysis(scores)

        assert set(actual_results.keys()) == set(expected_results.keys())
        for actual_arr, expected_arr in zip(actual_results.values(),
                                            expected_results.values()):
            np.testing.assert_array_equal(actual_arr, expected_arr)
