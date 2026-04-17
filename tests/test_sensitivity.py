# -*- coding: utf-8 -*-

# import built-in module
import pickle

# import third-party modules
import pandas as pd
import numpy as np
import bw2calc as bc
import pytest

# import your own module
from lcatoolbox import (global_sensitivity_analysis, run_monte_carlo, local_sensitivity_analysis, import_foreground,
                        ScoresDict, ParametersDict, act_tuple)
from setup_bw_project import setup_brightway, imported_activities

class TestSensitivity:

    def _generate_test_data(self, activities):
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        n_iterations = 100
        scores, scores_background, parameters = run_monte_carlo(activities=activities,
                                                                         impact_categories=impact_categories,
                                                                         n_iterations=n_iterations, )
        with open("test_sensitivity_gsa_scores.pickle", "wb") as f:
            pickle.dump(scores, f)
        with open("test_sensitivity_gsa_scores_background.pickle", "wb") as f:
            pickle.dump(scores_background, f)
        with open("test_sensitivity_gsa_parameters.pickle", "wb") as f:
            pickle.dump(parameters, f)

    @pytest.fixture
    def scores(self, imported_activities) -> ScoresDict:
        try:
            with open("test_sensitivity_gsa_scores.pickle", "rb") as f:
                scores = pickle.load(f)
        except FileNotFoundError:
            print("Test data test_sensitivity_gsa_scores.pickle not found. Generating new test data, please wait...")
            self._generate_test_data(imported_activities)
            with open("test_sensitivity_gsa_scores.pickle", "rb") as f:
                scores = pickle.load(f)

        return scores

    @pytest.fixture
    def scores_background(self, imported_activities) -> ScoresDict:
        try:
            with open("test_sensitivity_gsa_scores_background.pickle", "rb") as f:
                scores_background = pickle.load(f)
        except FileNotFoundError:
            print("Test data test_sensitivity_gsa_scores_background.pickle not found. Generating new test data, please wait...")
            self._generate_test_data(imported_activities)
            with open("test_sensitivity_gsa_scores_background.pickle", "rb") as f:
                scores_background = pickle.load(f)

        return scores_background

    @pytest.fixture
    def parameters(self, imported_activities) -> ParametersDict:
        try:
            with open("test_sensitivity_gsa_parameters.pickle", "rb") as f:
                parameters = pickle.load(f)
        except FileNotFoundError:
            print("Test data test_sensitivity_gsa_parameters.pickle not found. Generating new test data, please wait...")
            self._generate_test_data(imported_activities)
            with open("test_sensitivity_gsa_parameters.pickle", "rb") as f:
                parameters = pickle.load(f)

        return parameters

    def test_global_sensitivity_analysis(self, scores, scores_background, parameters):
        results = global_sensitivity_analysis(scores, scores_background, parameters,
                                                 algorithm="main_effect_li_2016_alg_1",
                                                 n_bins=10)
        activities = list(scores.keys())
        background_activities = list(scores_background.keys())
        impact_categories = list(scores[activities[0]].keys())

        expected_df_columns = ["name", "type", "value"]
        expected_df_column_dtypes = [pd.StringDtype(na_value=np.nan), pd.StringDtype(na_value=np.nan), float]

        # Formatting of results
        assert set(results.keys()) == set(activities)
        for act_results in results.values():
            assert set(act_results.keys()) == set(impact_categories)
            for ic_results in act_results.values():
                assert len(ic_results) == (len(background_activities) + len(parameters))
                assert list(ic_results.columns) == expected_df_columns
                assert list(ic_results.dtypes) == expected_df_column_dtypes

        # Values differ from one activity to the other
        with pytest.raises(AssertionError):
            pd.testing.assert_frame_equal(results[activities[0]][impact_categories[0]],
                                          results[activities[1]][impact_categories[0]])

        # Values differ from one impact category to the other
        with pytest.raises(AssertionError):
            pd.testing.assert_frame_equal(results[activities[0]][impact_categories[0]],
                                          results[activities[0]][impact_categories[1]])

        # Values differ from one input to the other
        assert (list(results[activities[0]][impact_categories[0]]["value"])[0]
                != list(results[activities[0]][impact_categories[0]]["value"])[1])

    def test_global_sensitivity_analysis_ignore_dependent(self, scores, scores_background, parameters):
        activities_tuples = list(scores.keys())
        impact_categories = list(scores[activities_tuples[0]].keys())

        results = global_sensitivity_analysis(scores, scores_background, parameters,
                                                 algorithm="main_effect_li_2016_alg_1",
                                                 n_bins=10,
                                              ignore_dependent=False)

        assert len(results[activities_tuples[0]][impact_categories[0]]) == 33

        results_ignore_dependent = global_sensitivity_analysis(scores, scores_background, parameters,
                                              algorithm="main_effect_li_2016_alg_1",
                                              n_bins=10,
                                              ignore_dependent=True)

        assert len(results_ignore_dependent[activities_tuples[0]][impact_categories[0]]) == 22

    def test_local_sensitivity_analysis(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        parameters = ["some_random_value", "what_a_waste"]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        results = local_sensitivity_analysis(activities,
                                                impact_categories,
                                                parameters)

        # Check format
        assert set(results.keys()) == set([act_tuple(act) for act in activities])
        for act_results in results.values():
            assert set(act_results.keys()) == set(impact_categories)
            for ic_results in act_results.values():
                assert set(ic_results.keys()) == set(parameters)
                for param_results in ic_results.values():
                    assert set(param_results.keys()) == {"sensitivity", "elasticity"}

        # Sensitivity and elasticity differ
        assert (results[act_tuple(activities[0])][impact_categories[0]][parameters[0]]["sensitivity"] !=
                results[act_tuple(activities[0])][impact_categories[0]][parameters[0]]["elasticity"])

        # Different values for different activities
        assert (results[act_tuple(activities[0])][impact_categories[0]][parameters[0]]["sensitivity"] !=
                results[act_tuple(activities[1])][impact_categories[0]][parameters[0]]["sensitivity"])
        assert (results[act_tuple(activities[0])][impact_categories[0]][parameters[0]]["elasticity"] !=
                results[act_tuple(activities[1])][impact_categories[0]][parameters[0]]["elasticity"])

        # Different values for different impact categories
        assert (results[act_tuple(activities[0])][impact_categories[0]][parameters[0]]["sensitivity"] !=
                results[act_tuple(activities[0])][impact_categories[1]][parameters[0]]["sensitivity"])
        assert (results[act_tuple(activities[0])][impact_categories[0]][parameters[0]]["elasticity"] !=
                results[act_tuple(activities[0])][impact_categories[1]][parameters[0]]["elasticity"])

        # Different values for different parameters
        assert (results[act_tuple(activities[0])][impact_categories[0]][parameters[0]]["sensitivity"] !=
                results[act_tuple(activities[0])][impact_categories[0]][parameters[1]]["sensitivity"])
        assert (results[act_tuple(activities[0])][impact_categories[0]][parameters[0]]["elasticity"] !=
                results[act_tuple(activities[0])][impact_categories[0]][parameters[1]]["elasticity"])
