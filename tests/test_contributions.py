# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2data as bd
import pytest
import pandas as pd

# import your own module
from lcatoolbox import contributions_tree, grouped_contributions
from setup_bw_project import *

class TestContributions:


    def test_contributions_tree(self, fruit_salad):
        impact_category = ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)')
        expected_df = pd.read_excel("tests/test_contributions_tree_expected_dataframe.ods",
                                    sheet_name="DataFrame",
                                    dtype={"amount": float})
        actual_df = contributions_tree(activity=fruit_salad,
                                       amount=1,
                                       impact_category=impact_category,
                                       max_depth=2)
        actual_df.to_excel("tests/test_contributions_tree_actual_dataframe.ods")

        # Do not care about row order
        expected_df = expected_df.sort_values(by=['contribution'], ascending=False)
        actual_df = actual_df.sort_values(by=['contribution'], ascending=False)
        expected_df = expected_df.reset_index(drop=True)
        actual_df = actual_df.reset_index(drop=True)

        pd.testing.assert_frame_equal(actual_df,
                                      expected_df,
                                      check_like=True)

    def test_contributions_tree_max_depth(self, fruit_salad):
        impact_category = ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)')
        expected_df = pd.read_excel("tests/test_contributions_tree_expected_dataframe.ods",
                                    sheet_name="DataFrame",
                                    dtype={"amount": float})
        expected_df = expected_df[expected_df["depth"] < 2]
        actual_df = contributions_tree(activity=fruit_salad,
                                       amount=1,
                                       impact_category=impact_category,
                                       max_depth=1)
        # actual_df.to_excel("tests/test_contributions_tree_actual_dataframe.ods")

        # Do not care about row order
        expected_df = expected_df.sort_values(by=['contribution'], ascending=False)
        actual_df = actual_df.sort_values(by=['contribution'], ascending=False)
        expected_df = expected_df.reset_index(drop=True)
        actual_df = actual_df.reset_index(drop=True)

        pd.testing.assert_frame_equal(actual_df,
                                      expected_df,
                                      check_like=True)

    def test_grouped_contributions(self, fruit_salad):
        impact_category = ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)')
        expected_df = pd.read_excel("tests/test_grouped_contributions_expected_dataframe.ods",
                                    sheet_name="DataFrame",
                                    dtype={"score": float})
        actual_df = grouped_contributions(activity=fruit_salad,
                                          amount=1,
                                          impact_category=impact_category,
                                          max_depth=2)
        actual_df.to_excel("tests/test_grouped_contributions_actual_dataframe.ods")

        # Do not care about row order
        expected_df = expected_df.sort_values(by=['contribution'], ascending=False)
        actual_df = actual_df.sort_values(by=['contribution'], ascending=False)
        expected_df = expected_df.reset_index(drop=True)
        actual_df = actual_df.reset_index(drop=True)

        pd.testing.assert_frame_equal(actual_df,
                                      expected_df,
                                      check_like=True)

    def test_grouped_contributions_group_not_found(self, fruit_salad):
        impact_category = ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)')
        with pytest.raises(RuntimeError):
            _ = grouped_contributions(activity=fruit_salad,
                                              amount=1,
                                              impact_category=impact_category,
                                              max_depth=0)
