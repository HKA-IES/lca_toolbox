# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2calc as bc
from bw2data.parameters import ProjectParameter
import pytest

# import your own module
from lcatoolbox import calculate_scores, act_tuple
from setup_bw_project import setup_brightway, imported_activities

class TestCompute:


    def test_calculate_scores(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        scores, parameters = calculate_scores(activities,
                                                    impact_categories,)

        # Expected length
        assert len(scores) == len(activities)
        for act_scores in scores.values():
            assert len(act_scores) == len(impact_categories)
            for ic_scores in act_scores.values():
                assert len(ic_scores) == 1
        assert len(parameters) == len(ProjectParameter.select())
        for param_data in parameters.values():
            _ = param_data["type"]
            assert len(param_data["values"]) == 1

        # Scores differ from one activity to the other
        assert (scores[act_tuple(activities[0])][impact_categories[0]]
                != scores[act_tuple(activities[1])][impact_categories[0]])

        # Scores differ from one impact category to the other
        assert (scores[act_tuple(activities[0])][impact_categories[0]]
                != scores[act_tuple(activities[0])][impact_categories[1]])

        scores_repeat, parameters_repeat = calculate_scores(activities,
                                                    impact_categories, )

        # Scores are equivalent when re-calculated
        assert scores == scores_repeat
        assert parameters == parameters_repeat

    def test_calculate_scores_use_exchange_distributions(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        scores_1, parameters_1 = calculate_scores(activities,
                                                    impact_categories,
                                                    use_exchange_distributions=True)
        scores_2, parameters_2 = calculate_scores(activities,
                                                    impact_categories,
                                                    use_exchange_distributions=True)

        # Scores differ from one iteration to the other
        assert scores_1 != scores_2

        # Parameters are the same from one iteration to the other
        assert parameters_1 == parameters_2

    def test_calculate_scores_use_parameters_distributions(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        scores_1, parameters_1 = calculate_scores(activities,
                                                        impact_categories,
                                                        use_parameters_distributions=True)
        scores_2, parameters_2 = calculate_scores(activities,
                                                        impact_categories,
                                                        use_parameters_distributions=True)

        # Scores differ from one iteration to the other
        assert scores_1 != scores_2

        # Parameters differ from one iteration to the other
        assert parameters_1 != parameters_2

    def test_calculate_scores_set_parameters(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        scores_1, parameters_1 = calculate_scores(activities,
                                                        impact_categories,
                                                        parameters={"some_random_value": 2})
        scores_2, parameters_2 = calculate_scores(activities,
                                                        impact_categories,
                                                        parameters={"some_random_value": 3})

        # Parameter value is reflected in parameters
        assert parameters_1["some_random_value"]["values"] == [2]
        assert parameters_2["some_random_value"]["values"] == [3]

        # Scores differ from one iteration to the other
        assert scores_1 != scores_2

        # Parameters differ from one iteration to the other
        assert parameters_1 != parameters_2

    def test_calculate_scores_set_parameters_do_not_exist(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        with pytest.raises(ValueError):
            _, _ = calculate_scores(activities,
                                                            impact_categories,
                                                            parameters={"bad_parameter": 2})

    def test_calculate_scores_set_parameters_dependent_parameter(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
        # Why? I don't know...
        _ = bc.LCA(demand={activities[0]: 1}, method=impact_categories[1])

        with pytest.raises(ValueError):
            _, _ = calculate_scores(activities,
                                                            impact_categories,
                                                            parameters={"amount_beverage_carton": 2})
