# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2data as bd
import pytest
import pandas as pd

# import your own module
from lcatoolbox import contributions_tree, grouped_contributions

class TestContributions:
    @pytest.fixture(scope="session", autouse=True)
    def setup_brightway(self):
        if "lca_toolbox_tests" not in bd.projects:
            raise RuntimeError("Brightway project for tests has not been set-up. Run setup_bw_project.py.")

        bd.projects.set_current("lca_toolbox_tests")
        if 'ecoinvent-3.12-cutoff' not in bd.databases:
            raise RuntimeError("Database ecoinvent-3.12-cutoff is missing. Run setup_bw_project.py.")
        if 'ecoinvent-3.12-biosphere' not in bd.databases:
            raise RuntimeError("Database ecoinvent-3.12-biosphere is missing. Run setup_bw_project.py.")

    @pytest.fixture
    def fruit_salad(self):
        try:
            del bd.databases["foreground"]
        except KeyError:
            pass
        foreground = bd.Database("foreground")
        foreground.register()

        juice = foreground.new_node(name="juice",
                                    unit="cubic meter",
                                    location="GLO",
                                    type=bd.labels.chimaera_node_default)
        juice.save()
        juice.new_edge(amount=0.001,
                       unit=juice["unit"],
                       input=juice,
                       type=bd.labels.production_edge_default).save()

        beverage_carton = bd.get_activity(name="beverage carton production, 1 L, for juice (ambient)",
                                          location="RER")
        orange = bd.get_activity(name="orange production, processing grade",
                                 location="RoW")
        water = bd.get_activity(name="Water, unspecified natural origin", categories=('natural resource', 'in water'))

        juice.new_edge(input=beverage_carton,
                             amount=1,
                             unit=beverage_carton["unit"],
                             type=bd.labels.consumption_edge_default,
                             group="waste").save()
        juice.new_edge(input=orange,
                       amount=3,
                       unit=orange["unit"],
                       type=bd.labels.consumption_edge_default,
                       group="fruit").save()
        juice.new_edge(input=water,
                       amount=0.5,
                       unit=water["unit"],
                       type=bd.labels.biosphere_edge_default).save()


        fruit_salad = foreground.new_node(name="fruit_salad",
                                             unit="unit",
                                             location="GLO",
                                             type=bd.labels.chimaera_node_default)
        fruit_salad.save()
        fruit_salad.new_edge(amount=1,
                             unit=fruit_salad["unit"],
                             input=fruit_salad,
                             type=bd.labels.production_edge_default).save()

        kiwi = bd.get_activity(name="kiwi production", location="GLO")
        apple = bd.get_activity(name="apple production", location="IT")
        anchovy = bd.get_activity(name="anchovy, capture by wooden purse seiner and landing whole, fresh",
                                  location="PE")
        biowaste = bd.get_activity(name="market for biowaste, kitchen and garden waste", location="GLO")

        fruit_salad.new_edge(input=kiwi,
                             amount=-0.125,
                             unit=kiwi["unit"],
                             type=bd.labels.consumption_edge_default,
                             group="fruit").save()
        fruit_salad.new_edge(input=apple,
                             amount=0.5,
                             unit=apple["unit"],
                             type=bd.labels.consumption_edge_default,
                             group="fruit").save()
        fruit_salad.new_edge(input=anchovy,
                             amount=0,
                             unit=anchovy["unit"],
                             type=bd.labels.consumption_edge_default,
                             group="fish").save()
        fruit_salad.new_edge(input=juice,
                             amount=0.0001,
                             unit=juice["unit"],
                             type=bd.labels.consumption_edge_default,
                             group=None).save()
        fruit_salad.new_edge(input=biowaste,
                             amount=-0.1,
                             unit=biowaste["unit"],
                             type=bd.labels.consumption_edge_default,
                             group="waste").save()

        return fruit_salad

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
                                          impact_category=impact_category)
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
