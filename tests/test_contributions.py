# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2data as bd
import pytest
import pandas as pd

# import your own module
from lcatoolbox import contributions_tree

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
        orange = bd.get_activity(name="orange production, fresh grade", location="ES")

        fruit_salad.new_edge(input=kiwi,
                             amount=0.125,
                             unit=kiwi["unit"],
                             type=bd.labels.consumption_edge_default,
                             group="kiwi").save()
        fruit_salad.new_edge(input=apple,
                             amount=0.5,
                             unit=apple["unit"],
                             type=bd.labels.consumption_edge_default,
                             group="apple").save()
        fruit_salad.new_edge(input=anchovy,
                             amount=0,
                             unit=anchovy["unit"],
                             type=bd.labels.consumption_edge_default,
                             group="anchovy").save()
        # fruit_salad.new_edge(input=orange,
        #                     amount=0.25,
        #                     unit=orange["unit"],
        #                     type=bd.labels.consumption_edge_default).save()

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

    def test_grouped_contributions(self):
        raise NotImplementedError()