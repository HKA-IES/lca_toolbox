# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2data as bd
import pytest

# import your own module
from lcatoolbox import get_impact_categories

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

    def test_get_impact_categories(self):
        expected_impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'climate change: biogenic', 'global warming potential (GWP100)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'climate change: fossil', 'global warming potential (GWP100)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'climate change: land use and land use change', 'global warming potential (GWP100)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'ecotoxicity: freshwater', 'comparative toxic unit for ecosystems (CTUe)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'ecotoxicity: freshwater, inorganics', 'comparative toxic unit for ecosystems (CTUe)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'ecotoxicity: freshwater, organics', 'comparative toxic unit for ecosystems (CTUe)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'energy resources: non-renewable', 'abiotic depletion potential (ADP): fossil fuels'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'eutrophication: freshwater', 'fraction of nutrients reaching freshwater end compartment (P)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'eutrophication: marine', 'fraction of nutrients reaching marine end compartment (N)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'eutrophication: terrestrial', 'accumulated exceedance (AE)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'human toxicity: carcinogenic', 'comparative toxic unit for human (CTUh)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'human toxicity: carcinogenic, inorganics', 'comparative toxic unit for human (CTUh)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'human toxicity: carcinogenic, organics', 'comparative toxic unit for human (CTUh)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'human toxicity: non-carcinogenic', 'comparative toxic unit for human (CTUh)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'human toxicity: non-carcinogenic, inorganics', 'comparative toxic unit for human (CTUh)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'human toxicity: non-carcinogenic, organics', 'comparative toxic unit for human (CTUh)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'ionising radiation: human health', 'human exposure efficiency relative to u235'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'land use', 'soil quality index'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'material resources: metals/minerals', 'abiotic depletion potential (ADP): elements (ultimate reserves)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'ozone depletion', 'ozone depletion potential (ODP)'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'particulate matter formation', 'impact on human health'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'photochemical oxidant formation: human health', 'tropospheric ozone concentration increase'),
                                      ('ecoinvent-3.12', 'EF v3.1', 'water use', 'user deprivation potential (deprivation-weighted water consumption)')]
        actual_impact_categories = get_impact_categories(method="EF v3.1")
        assert expected_impact_categories == actual_impact_categories
        