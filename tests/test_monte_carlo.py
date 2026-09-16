# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2data as bd
from bw2data.parameters import ProjectParameter
import pandas as pd

# import your own module
from lcatoolbox import run_monte_carlo, discernibility_analysis, activity_string
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
                                 bd.get_activity(name="market for biowaste, kitchen and garden waste", location="GLO"),
                                 bd.get_activity(name="industrial gases production, cryogenic air separation",
                                                 location="Asia without China",
                                                 product="oxygen, liquid")
                                 ]

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use', 'user deprivation potential (deprivation-weighted water consumption)')]
        n_iterations = 5
        df_scores, df_scores_background, df_parameters = run_monte_carlo(activities=activities,
                                               impact_categories=impact_categories,
                                               n_iterations=n_iterations,)

        # Validation of df_scores
        assert len(df_scores) == len(activities) * len(impact_categories)
        assert set(df_scores.columns) == {"activity", "impact_category", "values"}
        assert set(df_scores["activity"].unique()) == {activity_string(act) for act in activities}
        assert set(df_scores["impact_category"].unique()) == {str(ic) for ic in impact_categories}
        assert len(df_scores["values"][0]) == n_iterations

        # Values differ from one iteration to the other
        assert df_scores["values"][0][0] != df_scores["values"][0][1]

        # Values differ from one activity to the other
        df_scores_act_0 = df_scores[df_scores["activity"] == activity_string(activities[0])]
        df_scores_act_1 = df_scores[df_scores["activity"] == activity_string(activities[1])]
        assert not df_scores_act_0.equals(df_scores_act_1)

        # Values differ from one impact category to the other
        df_scores_ic_0 = df_scores[df_scores["impact_category"] == str(impact_categories[0])]
        df_scores_ic_1 = df_scores[df_scores["impact_category"] == str(impact_categories[1])]
        assert not df_scores_ic_0.equals(df_scores_ic_1)

        # Validation of df_scores_background
        assert len(df_scores_background) == len(background_activities) * len(impact_categories)
        assert set(df_scores_background.columns) == {"activity", "impact_category", "values"}
        assert set(df_scores_background["activity"].unique()) == {activity_string(act) for act in background_activities}
        assert set(df_scores_background["impact_category"].unique()) == {str(ic) for ic in impact_categories}
        assert len(df_scores_background["values"][0]) == n_iterations

        # Values differ from one iteration to the other
        assert df_scores_background["values"][0][0] != df_scores_background["values"][0][1]

        # Values differ from one activity to the other
        df_scores_background_act_0 = df_scores_background[df_scores_background["activity"] == activity_string(background_activities[0])]
        df_scores_background_act_1 = df_scores_background[df_scores_background["activity"] == activity_string(background_activities[1])]
        assert not df_scores_background_act_0.equals(df_scores_background_act_1)

        # Values differ from one impact category to the other
        df_scores_background_ic_0 = df_scores_background[df_scores_background["impact_category"] == str(impact_categories[0])]
        df_scores_background_ic_1 = df_scores_background[df_scores_background["impact_category"] == str(impact_categories[1])]
        assert not df_scores_background_ic_0.equals(df_scores_background_ic_1)

        # Validation of df_parameters
        assert len(df_parameters) == len(ProjectParameter.select())
        assert set(df_parameters.columns) == {"parameter", "type", "values"}
        assert len(df_parameters["values"][0]) == n_iterations

        # Correct values
        assert set(df_parameters["parameter"].unique()) == {param.name for param in ProjectParameter.select()}

        # Values differ from one iteration to the other
        assert df_parameters["values"][0][0] != df_parameters["values"][0][1]

    def test_run_monte_carlo_no_parameters(self):
        # Ensure that everything runs smoothly when no ProjectParameters have been defined.
        activities = [bd.get_activity(name="apple production", location="IT")]
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        n_iterations = 5
        _, _, df_parameters = run_monte_carlo(activities=activities,
                                  impact_categories=impact_categories,
                                  n_iterations=n_iterations, )

        assert len(df_parameters) == 0


    def test_monte_carlo_one_iteration(self, imported_activities):
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        n_iterations = 1
        df_scores, df_scores_background, _ = run_monte_carlo(activities=imported_activities,
                                  impact_categories=impact_categories,
                                  n_iterations=n_iterations, )

        assert len(df_scores) == len(imported_activities) * len(impact_categories)
        assert len(df_scores["values"][0]) == 1


    def test_discernibility_analysis(self):
        scores = [{"activity": "act_0", "impact_category": "ic_0",
                   "values": [0, 1, 2, 3, 4],},
                  {"activity": "act_0", "impact_category": "ic_1",
                   "values": [0, 1, 2, 3, 4],},
                  {"activity": "act_1", "impact_category": "ic_0",
                   "values": [4, 3, 2, 1, 0], },
                  {"activity": "act_1", "impact_category": "ic_1",
                   "values": [4, 3, 2, 1, 0], },
                  {"activity": "act_2", "impact_category": "ic_0",
                   "values": [1, 2, 3, 4, 5], },
                  {"activity": "act_2", "impact_category": "ic_1",
                   "values": [1, 2, 3, 4, 5], },
                  ]
        df_scores = pd.DataFrame(scores)

        expected_results = [{"activity_A": "act_0", "activity_B": "act_0", "impact_category": "ic_0",
                             "P_A>B": 0/5, "discernibility": 1.0,},
                            {"activity_A": "act_0", "activity_B": "act_1", "impact_category": "ic_0",
                             "P_A>B": 2/5, "discernibility": 0.2,},
                            {"activity_A": "act_0", "activity_B": "act_2", "impact_category": "ic_0",
                             "P_A>B": 0/5, "discernibility": 1.0,},
                            {"activity_A": "act_1", "activity_B": "act_0", "impact_category": "ic_0",
                             "P_A>B": 2/5, "discernibility": 0.2,},
                            {"activity_A": "act_1", "activity_B": "act_1", "impact_category": "ic_0",
                             "P_A>B": 0/5, "discernibility": 1.0,},
                            {"activity_A": "act_1", "activity_B": "act_2", "impact_category": "ic_0",
                             "P_A>B": 2/5, "discernibility": 0.2,},
                            {"activity_A": "act_2", "activity_B": "act_0", "impact_category": "ic_0",
                             "P_A>B": 5/5, "discernibility": 1.0,},
                            {"activity_A": "act_2", "activity_B": "act_1", "impact_category": "ic_0",
                             "P_A>B": 3/5, "discernibility": 0.2,},
                            {"activity_A": "act_2", "activity_B": "act_2", "impact_category": "ic_0",
                             "P_A>B": 0/5, "discernibility": 1.0,},
                            {"activity_A": "act_0", "activity_B": "act_0", "impact_category": "ic_1",
                             "P_A>B": 0/5, "discernibility": 1.0,},
                            {"activity_A": "act_0", "activity_B": "act_1", "impact_category": "ic_1",
                             "P_A>B": 2/5, "discernibility": 0.2,},
                            {"activity_A": "act_0", "activity_B": "act_2", "impact_category": "ic_1",
                             "P_A>B": 0/5, "discernibility": 1.0,},
                            {"activity_A": "act_1", "activity_B": "act_0", "impact_category": "ic_1",
                             "P_A>B": 2/5, "discernibility": 0.2,},
                            {"activity_A": "act_1", "activity_B": "act_1", "impact_category": "ic_1",
                             "P_A>B": 0/5, "discernibility": 1.0,},
                            {"activity_A": "act_1", "activity_B": "act_2", "impact_category": "ic_1",
                             "P_A>B": 2/5, "discernibility": 0.2,},
                            {"activity_A": "act_2", "activity_B": "act_0", "impact_category": "ic_1",
                             "P_A>B": 5/5, "discernibility": 1.0,},
                            {"activity_A": "act_2", "activity_B": "act_1", "impact_category": "ic_1",
                             "P_A>B": 3/5, "discernibility": 0.2,},
                            {"activity_A": "act_2", "activity_B": "act_2", "impact_category": "ic_1",
                             "P_A>B": 0/5, "discernibility": 1.0,},
                            ]
        df_expected_results = pd.DataFrame(expected_results)

        df_actual_results = discernibility_analysis(df_scores)

        pd.testing.assert_frame_equal(df_expected_results, df_actual_results)
