# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import pandas as pd
import numpy as np

# import your own module
from lcatoolbox import global_sensitivity_analysis, run_monte_carlo
from setup_bw_project import *

class TestGlobalSensitivityAnalysis:

    @staticmethod
    def _generate_test_data(fruit_salad):
        foreground = bd.Database("foreground")
        big_fruit_salad = foreground.new_node(name="big_fruit_salad",
                                              unit="unit",
                                              location="GLO",
                                              type=bd.labels.chimaera_node_default)
        big_fruit_salad.save()
        big_fruit_salad.new_edge(amount=1,
                                 unit=big_fruit_salad["unit"],
                                 input=big_fruit_salad,
                                 type=bd.labels.production_edge_default).save()
        big_fruit_salad.new_edge(amount=1.5,
                                 unit=fruit_salad["unit"],
                                 input=fruit_salad,
                                 type=bd.labels.consumption_edge_default).save()

        activities = [fruit_salad, big_fruit_salad]
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        n_iterations = 100
        scores_df, scores_background_df, parameters_df = run_monte_carlo(activities=activities,
                                                                         impact_categories=impact_categories,
                                                                         n_iterations=n_iterations, )
        scores_df.to_csv("tests/test_gsa_scores_df.csv", index=False)
        scores_background_df.to_csv("tests/test_gsa_scores_background_df.csv", index=False)
        parameters_df.to_csv("tests/test_gsa_parameters_df.csv", index=False)

    @pytest.fixture
    def scores_df(self, fruit_salad) -> pd.DataFrame:
        try:
            scores_df = pd.read_csv("tests/test_gsa_scores_df.csv")
        except FileNotFoundError:
            print("Test data test_gsa_scores_df.csv not found. Generating new test data, please wait...")
            self._generate_test_data(fruit_salad)
            scores_df = pd.read_csv("tests/test_gsa_scores_df.csv")

        return scores_df

    @pytest.fixture
    def scores_background_df(self, fruit_salad) -> pd.DataFrame:
        try:
            scores_background_df = pd.read_csv("tests/test_gsa_scores_background_df.csv")
        except FileNotFoundError:
            print("Test data test_gsa_scores_background_df.csv not found. Generating new test data, please wait...")
            self._generate_test_data(fruit_salad)
            scores_background_df = pd.read_csv("tests/test_gsa_scores_background_df.csv")

        return scores_background_df

    @pytest.fixture
    def parameters_df(self, fruit_salad) -> pd.DataFrame:
        try:
            parameters_df = pd.read_csv("tests/test_gsa_parameters_df.csv")
        except FileNotFoundError:
            print("Test data test_gsa_parameters_df.csv not found. Generating new test data, please wait...")
            self._generate_test_data(fruit_salad)
            parameters_df = pd.read_csv("tests/test_gsa_parameters_df.csv")

        return parameters_df

    def test_global_sensitivity_analysis(self, scores_df, scores_background_df, parameters_df):
        results_df = global_sensitivity_analysis(scores_df=scores_df,
                                                 scores_background_df=scores_background_df,
                                                 parameters_df=parameters_df,
                                                 algorithm="main_effect_li_2016_alg_1",
                                                 n_bins=10)

        # Validation of results_df
        activities = list(scores_df["activity"].unique())
        impact_categories = list(scores_df.columns)[2:]
        background = list(scores_background_df["activity"].unique())
        parameters = list(parameters_df["name"].unique())

        # Correct number of rows
        assert len(results_df) == (len(background) + len(parameters)) * len(activities)

        # Correct columns
        expected_columns = ["activity", "type", "name"] + impact_categories
        expected_column_dtypes = [object, object, object] + [float]*len(impact_categories)
        assert list(results_df.columns) == expected_columns
        # assert list(results_df.dtypes) == expected_column_dtypes

        # Values differ from one activity to the other
        with pytest.raises(AssertionError):
            np.testing.assert_array_equal(np.array(results_df[results_df["activity"] == activities[0]][impact_categories[0]]),
                                                 np.array(results_df[results_df["activity"] == activities[1]][
                                                              impact_categories[0]]))

        # Values differ from one impact category to the other
        with pytest.raises(AssertionError):
            np.testing.assert_array_equal(np.array(results_df[results_df["activity"] == activities[0]][impact_categories[0]]),
                                                 np.array(results_df[results_df["activity"] == activities[0]][
                                                              impact_categories[1]]))
