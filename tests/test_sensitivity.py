# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import pandas as pd
import numpy as np
import bw2calc as bc
import pytest

# import your own module
from lcatoolbox import (uncertainty_apportioning, local_sensitivity_analysis, act_tuple, SobolSaltelliMethod,
                        SobolLi2016Method, FASTMethod)
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

        ua, _, _ = uncertainty_apportioning(activities,
                                            impact_categories,
                                            SobolSaltelliMethod(N=2))

        # Check format
        assert set(ua.keys()) == set([act_tuple(act) for act in activities])
        for act_ua in ua.values():
            assert set(act_ua.keys()) == set(impact_categories)
            for ic_ua in act_ua.values():
                assert set(ic_ua.keys()) == set(["S1", "S1_conf", "S2", "S2_conf", "ST", "ST_conf"])
                assert hasattr(ic_ua, "problem")

        # S1, S2, and ST differ
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S1"],
                                  ua[act_tuple(activities[0])][impact_categories[0]]["S2"])
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S1"],
                                  ua[act_tuple(activities[0])][impact_categories[0]]["ST"])
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S2"],
                                  ua[act_tuple(activities[0])][impact_categories[0]]["ST"])

        # Different values for different activities
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S1"],
                                  ua[act_tuple(activities[1])][impact_categories[0]]["S1"])
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S2"],
                                  ua[act_tuple(activities[1])][impact_categories[0]]["S2"])
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["ST"],
                                  ua[act_tuple(activities[1])][impact_categories[0]]["ST"])

        # Different values for different impact categories
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S1"],
                                  ua[act_tuple(activities[0])][impact_categories[1]]["S1"])
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S2"],
                                  ua[act_tuple(activities[0])][impact_categories[1]]["S2"])
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["ST"],
                                  ua[act_tuple(activities[0])][impact_categories[1]]["ST"])

    def test_uncertainty_apportioning_fast(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        ua, _, _ = uncertainty_apportioning(activities,
                                            impact_categories,
                                            FASTMethod(N=5, M=1))

        # Check format
        assert set(ua.keys()) == set([act_tuple(act) for act in activities])
        for act_ua in ua.values():
            assert set(act_ua.keys()) == set(impact_categories)
            for ic_ua in act_ua.values():
                assert set(ic_ua.keys()) == set(["S1", "S1_conf", "ST", "ST_conf", "names"])
                # assert hasattr(ic_ua, "problem")

        # S1 and ST differ
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S1"],
                                  ua[act_tuple(activities[0])][impact_categories[0]]["ST"])

        # Different values for different activities
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S1"],
                                  ua[act_tuple(activities[1])][impact_categories[0]]["S1"])
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["ST"],
                                  ua[act_tuple(activities[1])][impact_categories[0]]["ST"])

        # Different values for different impact categories
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["S1"],
                                  ua[act_tuple(activities[0])][impact_categories[1]]["S1"])
        assert not np.array_equal(ua[act_tuple(activities[0])][impact_categories[0]]["ST"],
                                  ua[act_tuple(activities[0])][impact_categories[1]]["ST"])

    def test_uncertainty_apportioning_sobol_li_2016(self, imported_activities):
        activities = imported_activities
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        ua, scores, parameters = uncertainty_apportioning(activities,
                                            impact_categories,
                                            SobolLi2016Method(N=25,
                                                              n_bins=5))

        expected_df_columns = ["name", "type", "value"]
        expected_df_column_dtypes = [pd.StringDtype(na_value=np.nan), pd.StringDtype(na_value=np.nan), float]

        # Formatting of results
        expected_ua_keys = set([act_tuple(act) for act in activities])
        assert set(ua.keys()) == expected_ua_keys
        for act_ua in ua.values():
            assert set(act_ua.keys()) == set(impact_categories)
            for ic_ua in act_ua.values():
                assert len(ic_ua) == 26
                assert list(ic_ua.columns) == expected_df_columns
                assert list(ic_ua.dtypes) == expected_df_column_dtypes

        # Values differ from one activity to the other
        with pytest.raises(AssertionError):
            pd.testing.assert_frame_equal(ua[act_tuple(activities[0])][impact_categories[0]],
                                          ua[act_tuple(activities[1])][impact_categories[0]])

        # Values differ from one impact category to the other
        with pytest.raises(AssertionError):
            pd.testing.assert_frame_equal(ua[act_tuple(activities[0])][impact_categories[0]],
                                          ua[act_tuple(activities[0])][impact_categories[1]])

        # Values differ from one input to the other
        assert (list(ua[act_tuple(activities[0])][impact_categories[0]]["value"])[0]
                != list(ua[act_tuple(activities[0])][impact_categories[0]]["value"])[1])

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
