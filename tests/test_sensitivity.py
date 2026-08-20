# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import pandas as pd
import numpy as np
import bw2calc as bc

# import your own module
from lcatoolbox import (uncertainty_apportioning, local_sensitivity_analysis, activity_string, SobolSaltelliMethod,
                        SobolLi2016Method, FASTMethod, RBDFASTMethod, PAWNMethod, DeltaMomentIndependentMethod,
                        SpearmanRankCorrelationMethod, GradientBoostingMethod)
from setup_bw_project import setup_brightway, imported_activities

class TestSensitivity:

    def test_uncertainty_apportioning_sobol_saltelli(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        df_ua, _, _ = uncertainty_apportioning(activities,
                                            impact_categories,
                                            SobolSaltelliMethod(N=2))

        assert set(df_ua["activity"]) == set([activity_string(act) for act in activities])
        assert set(df_ua["impact_category"]) == set([str(ic) for ic in impact_categories])
        assert len(df_ua.index) == len(activities) * len(impact_categories) * 23
        expected_cols = {"parameter", "type", "activity", "impact_category", "S1", "S1_conf", "S1_rank", "ST", "ST_conf",
                         "ST_rank"}
        expected_cols |= {f"S2_{param}" for param in df_ua["parameter"]}
        expected_cols |= {f"S2_{param}_conf" for param in df_ua["parameter"]}
        expected_cols |= {f"S2_{param}_rank" for param in df_ua["parameter"]}
        assert set(df_ua.columns) == expected_cols
        assert set(df_ua["type"].unique()) == {"foreground", }

    def test_uncertainty_apportioning_fast(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        df_ua, _, _ = uncertainty_apportioning(activities,
                                            impact_categories,
                                            FASTMethod(N=5, M=1))

        assert set(df_ua["activity"]) == set([activity_string(act) for act in activities])
        assert set(df_ua["impact_category"]) == set([str(ic) for ic in impact_categories])
        assert len(df_ua.index) == len(activities) * len(impact_categories) * 23
        expected_cols = {"parameter", "type", "activity", "impact_category", "S1", "S1_conf", "S1_rank", "ST", "ST_conf",
                         "ST_rank"}
        assert set(df_ua.columns) == expected_cols
        assert set(df_ua["type"].unique()) == {"foreground", }

    def test_uncertainty_apportioning_rbd_fast(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        df_ua, _, _ = uncertainty_apportioning(activities,
                                            impact_categories,
                                            RBDFASTMethod(N=30, M=5))

        assert set(df_ua["activity"]) == set([activity_string(act) for act in activities])
        assert set(df_ua["impact_category"]) == set([str(ic) for ic in impact_categories])
        assert len(df_ua.index) == len(activities) * len(impact_categories) * 30
        expected_cols = {"parameter", "type", "activity", "impact_category", "S1", "S1_conf", "S1_rank"}
        assert set(df_ua.columns) == expected_cols
        assert set(df_ua["type"].unique()) == {"foreground", "background"}

    def test_uncertainty_apportioning_pawn(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        df_ua, _, _ = uncertainty_apportioning(activities,
                                            impact_categories,
                                            PAWNMethod(N=20))

        assert set(df_ua["activity"]) == set([activity_string(act) for act in activities])
        assert set(df_ua["impact_category"]) == set([str(ic) for ic in impact_categories])
        assert len(df_ua.index) == len(activities) * len(impact_categories) * 30
        expected_cols = {"parameter", "type", "activity", "impact_category", "minimum", "mean", "median", "maximum", "CV",
                         "stdev", "median_rank", "maximum_rank"}
        assert set(df_ua.columns) == expected_cols
        assert set(df_ua["type"].unique()) == {"foreground", "background"}

    def test_uncertainty_apportioning_deltamomentindependent(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        df_ua, _, _ = uncertainty_apportioning(activities,
                                            impact_categories,
                                            DeltaMomentIndependentMethod(N=20))

        assert set(df_ua["activity"]) == set([activity_string(act) for act in activities])
        assert set(df_ua["impact_category"]) == set([str(ic) for ic in impact_categories])
        assert len(df_ua.index) == len(activities) * len(impact_categories) * 30
        expected_cols = {"parameter", "type", "activity", "impact_category", "delta", "delta_conf",
                         "delta_rank", "S1", "S1_conf", "S1_rank"}
        assert set(df_ua.columns) == expected_cols
        assert set(df_ua["type"].unique()) == {"foreground", "background"}

    def test_uncertainty_apportioning_sobol_li_2016(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        df_ua, scores, parameters = uncertainty_apportioning(activities,
                                            impact_categories,
                                            SobolLi2016Method(N=25,
                                                              n_bins=5))

        assert set(df_ua["activity"]) == set([activity_string(act) for act in activities])
        assert set(df_ua["impact_category"]) == set([str(ic) for ic in impact_categories])
        assert len(df_ua.index) == len(activities) * len(impact_categories) * 30
        expected_cols = {"parameter", "type", "activity", "impact_category", "S1_alg_1", "S1_alg_2", "S1_alg_1_rank", "S1_alg_2_rank"}
        assert set(df_ua.columns) == expected_cols
        assert set(df_ua["type"].unique()) == {"foreground", "background"}

    def test_uncertainty_apportioning_spearmann_rank_correlation(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        df_ua, scores, parameters = uncertainty_apportioning(activities,
                                            impact_categories,
                                            SpearmanRankCorrelationMethod(N=25))

        assert set(df_ua["activity"]) == set([activity_string(act) for act in activities])
        assert set(df_ua["impact_category"]) == set([str(ic) for ic in impact_categories])
        assert len(df_ua.index) == len(activities) * len(impact_categories) * 30
        expected_cols = {"parameter", "type", "activity", "impact_category", "spearman", "spearman_rank"}
        assert set(df_ua.columns) == expected_cols
        assert set(df_ua["type"].unique()) == {"foreground", "background"}

    def test_uncertainty_apportioning_gradient_boosting(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        df_ua, scores, parameters = uncertainty_apportioning(activities,
                                                             impact_categories,
                                                             GradientBoostingMethod(N=25))

        assert set(df_ua["activity"]) == set([activity_string(act) for act in activities])
        assert set(df_ua["impact_category"]) == set([str(ic) for ic in impact_categories])
        assert len(df_ua.index) == len(activities) * len(impact_categories) * 30
        expected_cols = {"parameter", "type", "activity", "impact_category", "feature_importance",
                         "feature_importance_rank", "mean_shap_normalized", "mean_shap_normalized_rank"}
        assert set(df_ua.columns) == expected_cols
        assert set(df_ua["type"].unique()) == {"foreground", "background"}

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
        assert set(results.keys()) == set([activity_string(act) for act in activities])
        for act_results in results.values():
            assert set(act_results.keys()) == set(impact_categories)
            for ic_results in act_results.values():
                assert set(ic_results.keys()) == set(parameters)
                for param_results in ic_results.values():
                    assert set(param_results.keys()) == {"sensitivity", "elasticity"}

        # Sensitivity and elasticity differ
        assert (results[activity_string(activities[0])][impact_categories[0]][parameters[0]]["sensitivity"] !=
                results[activity_string(activities[0])][impact_categories[0]][parameters[0]]["elasticity"])

        # Different values for different activities
        assert (results[activity_string(activities[0])][impact_categories[0]][parameters[0]]["sensitivity"] !=
                results[activity_string(activities[1])][impact_categories[0]][parameters[0]]["sensitivity"])
        assert (results[activity_string(activities[0])][impact_categories[0]][parameters[0]]["elasticity"] !=
                results[activity_string(activities[1])][impact_categories[0]][parameters[0]]["elasticity"])

        # Different values for different impact categories
        assert (results[activity_string(activities[0])][impact_categories[0]][parameters[0]]["sensitivity"] !=
                results[activity_string(activities[0])][impact_categories[1]][parameters[0]]["sensitivity"])
        assert (results[activity_string(activities[0])][impact_categories[0]][parameters[0]]["elasticity"] !=
                results[activity_string(activities[0])][impact_categories[1]][parameters[0]]["elasticity"])

        # Different values for different parameters
        assert (results[activity_string(activities[0])][impact_categories[0]][parameters[0]]["sensitivity"] !=
                results[activity_string(activities[0])][impact_categories[0]][parameters[1]]["sensitivity"])
        assert (results[activity_string(activities[0])][impact_categories[0]][parameters[0]]["elasticity"] !=
                results[activity_string(activities[0])][impact_categories[0]][parameters[1]]["elasticity"])
