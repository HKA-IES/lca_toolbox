# -*- coding: utf-8 -*-

# import built-in module
import time

# import third-party modules
import bw2data as bd
import pytest
import pandas as pd

# import your own module
from lcatoolbox import run_monte_carlo, discernability_analysis
from setup_bw_project import *

class TestMonteCarlo:


    def test_run_monte_carlo(self, fruit_salad):
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
                             ('ecoinvent-3.12', 'EF v3.1', 'water use', 'user deprivation potential (deprivation-weighted water consumption)')]
        n_iterations = 5
        scores_df, scores_background_df, parameters_df = run_monte_carlo(activities=activities,
                                               impact_categories=impact_categories,
                                               n_iterations=n_iterations,)

        # Validation of scores_df
        # Correct number of rows
        assert len(scores_df) == len(activities) * n_iterations

        # Correct columns
        expected_columns = ["iteration", "activity", impact_categories[0], impact_categories[1], impact_categories[2], ]
        expected_column_dtypes = [int, object, float, float, float]
        assert list(scores_df.columns) == expected_columns
        assert list(scores_df.dtypes) == expected_column_dtypes

        # Values differ from one iteration to the other
        assert (scores_df[(scores_df["iteration"] == 0) &
                          (scores_df["activity"] == (activities[0]["name"], activities[0]["location"]))]
                [impact_categories[0]].item()
                != scores_df[(scores_df["iteration"] == 1) &
                             (scores_df["activity"] == (activities[0]["name"], activities[0]["location"]))]
                [impact_categories[0]].item() )

        # Values differ from one activity to the other
        assert (scores_df[(scores_df["iteration"] == 0) &
                          (scores_df["activity"] == (activities[0]["name"], activities[0]["location"]))]
                [impact_categories[0]].item()
                != scores_df[(scores_df["iteration"] == 0) &
                             (scores_df["activity"] == (activities[1]["name"], activities[1]["location"]))]
                [impact_categories[0]].item() )

        # Values differ from one impact category to the other
        assert (scores_df[(scores_df["iteration"] == 0) &
                          (scores_df["activity"] == (activities[0]["name"], activities[0]["location"]))]
                [impact_categories[0]].item()
                != scores_df[(scores_df["iteration"] == 0) &
                             (scores_df["activity"] == (activities[0]["name"], activities[0]["location"]))]
                [impact_categories[1]].item() )

        # Validation of scores_background_df
        # Correct number of rows
        n_background_activities = 6
        assert len(scores_background_df) == n_background_activities * n_iterations

        # Correct columns
        expected_columns = ["iteration", "activity", impact_categories[0], impact_categories[1], impact_categories[2], ]
        expected_column_dtypes = [int, object, float, float, float]
        assert list(scores_background_df.columns) == expected_columns
        assert list(scores_background_df.dtypes) == expected_column_dtypes

        # Values differ from one iteration to the other
        assert (scores_background_df[(scores_background_df["iteration"] == 0) &
                          (scores_background_df["activity"] == list(scores_background_df["activity"].unique())[0])]
                [impact_categories[0]].item()
                != scores_background_df[(scores_background_df["iteration"] == 1) &
                          (scores_background_df["activity"] == list(scores_background_df["activity"].unique())[0])]
                [impact_categories[0]].item() )

        # Values differ from one background to the other
        assert (scores_background_df[(scores_background_df["iteration"] == 0) &
                          (scores_background_df["activity"] == list(scores_background_df["activity"].unique())[0])]
                [impact_categories[0]].item()
                != scores_background_df[(scores_background_df["iteration"] == 0) &
                             (scores_background_df["activity"] == list(scores_background_df["activity"].unique())[1])]
                [impact_categories[0]].item())

        # Values differ from one impact category to the other
        assert (scores_background_df[(scores_background_df["iteration"] == 0) &
                          (scores_background_df["activity"] == list(scores_background_df["activity"].unique())[0])]
                [impact_categories[0]].item()
                != scores_background_df[(scores_df["iteration"] == 0) &
                             (scores_background_df["activity"] == list(scores_background_df["activity"].unique())[0])]
                [impact_categories[1]].item() )

        # Validation of parameters_df
        # Correct number of rows
        n_parameters = 2
        assert len(parameters_df) == n_parameters * n_iterations

        # Correct columns
        expected_columns = ["iteration", "name", "type", "value"]
        expected_column_dtypes = [int, pd.StringDtype, pd.StringDtype, float]
        assert list(parameters_df.columns) == expected_columns
        # assert list(parameters_df.dtypes) == expected_column_dtypes

        # Correct values
        assert set(parameters_df["name"].unique()) == {"some_random_value", "amount_beverage_carton"}

        # Values differ from one iteration to the other
        assert (parameters_df[(parameters_df["iteration"] == 0) &
                                     (parameters_df["name"] ==
                                      list(parameters_df["name"].unique())[0])]
                ["value"].item()
                != parameters_df[(parameters_df["iteration"] == 1) &
                                        (parameters_df["name"] ==
                                         list(parameters_df["name"].unique())[0])]
                ["value"].item())

        # Values differ from one parameter to the other
        assert (parameters_df[(parameters_df["iteration"] == 0) &
                              (parameters_df["name"] ==
                               list(parameters_df["name"].unique())[0])]
                ["value"].item()
                != parameters_df[(parameters_df["iteration"] == 0) &
                                 (parameters_df["name"] ==
                                  list(parameters_df["name"].unique())[1])]
                ["value"].item())

    def test_run_monte_carlo_multiple_jobs(self, fruit_salad):
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
                             ('ecoinvent-3.12', 'EF v3.1', 'water use', 'user deprivation potential (deprivation-weighted water consumption)')]
        n_iterations = 10

        start_time = time.time()
        _, _, _ = run_monte_carlo(activities=activities,
                                               impact_categories=impact_categories,
                                               n_iterations=n_iterations,
                                  n_jobs=1,)
        single_job_duration = time.time() - start_time

        start_time = time.time()
        _, _, _ = run_monte_carlo(activities=activities,
                                               impact_categories=impact_categories,
                                               n_iterations=n_iterations,
                                  n_jobs=2,)
        multiple_job_duration = time.time() - start_time

        assert multiple_job_duration < (single_job_duration*1.5)

    def test_discernability_analysis(self):
        scores_act1_ic1 = [0, 1, 2, 3, 4]
        scores_act1_ic2 = [0, 1, 2, 3, 4]
        scores_act2_ic1 = [4, 3, 2, 1, 0]
        scores_act2_ic2 = [4, 3, 2, 1, 0]
        scores_act3_ic1 = [1, 2, 3, 4, 5]
        scores_act3_ic2 = [1, 2, 3, 4, 5]

        n_iterations = len(scores_act1_ic1)
        activities = [("act1", "loc1"),
                      ("act2", "loc2"),
                      ("act3", "loc3")]

        scores = []
        for i in range(n_iterations):
            scores.append({"iteration": i,
                           "activity": activities[0],
                           ("m1", "ic1"): scores_act1_ic1[i],
                           ("m1", "ic2"): scores_act1_ic2[i],})
            scores.append({"iteration": i,
                           "activity": activities[1],
                           ("m1", "ic1"): scores_act2_ic1[i],
                           ("m1", "ic2"): scores_act2_ic2[i], })
            scores.append({"iteration": i,
                           "activity": activities[2],
                           ("m1", "ic1"): scores_act3_ic1[i],
                           ("m1", "ic2"): scores_act3_ic2[i], })
        scores_df = pd.DataFrame(scores)

        expected = {}
        expected[("m1", "ic1")] = pd.DataFrame([[0/5, 2/5, 0/5],
                                                [2/5, 0/5, 2/5],
                                                [5/5, 3/5, 0/5]],
                                               index=activities,
                                               columns=activities)
        expected[("m1", "ic2")] = pd.DataFrame([[0/5, 2/5, 0/5],
                                                [2/5, 0/5, 2/5],
                                                [5/5, 3/5, 0/5]],
                                               index=activities,
                                               columns=activities)

        actual = discernability_analysis(scores_df)

        assert set(actual.keys()) == set(expected.keys())
        for key in expected.keys():
            pd.testing.assert_frame_equal(actual[key],
                                      expected[key])
