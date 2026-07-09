# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2data as bd
from bw2data.parameters import ProjectParameter
import pytest

# import your own module
from lcatoolbox import calculate_scores, activity_string
from setup_bw_project import setup_brightway, imported_activities

class TestCompute:


    def test_calculate_scores(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        df_scores, df_parameters = calculate_scores(activities,
                                                    impact_categories,)

        # Expected length
        assert len(df_scores) == len(activities) * len(impact_categories)
        assert set(df_scores.columns) == {"activity", "impact_category", "value_0"}
        assert set(df_scores["activity"].unique()) == {activity_string(act) for act in activities}
        assert set(df_scores["impact_category"].unique()) == {str(ic) for ic in impact_categories}

        assert len(df_parameters) == len(ProjectParameter.select())
        assert set(df_parameters.columns) == {"parameter", "type", "value_0"}

        # Scores differ from one activity to the other
        df_scores_act_0 = df_scores[df_scores["activity"] == activity_string(activities[0])]
        df_scores_act_1 = df_scores[df_scores["activity"] == activity_string(activities[1])]
        assert not df_scores_act_0.equals(df_scores_act_1)

        # Scores differ from one impact category to the other
        df_scores_ic_0 = df_scores[df_scores["impact_category"] == str(impact_categories[0])]
        df_scores_ic_1 = df_scores[df_scores["impact_category"] == str(impact_categories[1])]
        assert not df_scores_ic_0.equals(df_scores_ic_1)

        df_scores_repeat, df_parameters_repeat = calculate_scores(activities,
                                                    impact_categories, )

        # Scores are equivalent when re-calculated
        assert df_scores.equals(df_scores_repeat)
        assert df_parameters.equals(df_parameters_repeat)

    def test_calculate_scores_use_exchange_distributions(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        df_scores_1, df_parameters_1 = calculate_scores(activities,
                                                    impact_categories,
                                                    use_exchange_distributions=True)
        df_scores_2, df_parameters_2 = calculate_scores(activities,
                                                    impact_categories,
                                                    use_exchange_distributions=True)

        # Scores differ from one iteration to the other
        assert not df_scores_1.equals(df_scores_2)

        # Parameters are the same from one iteration to the other
        assert df_parameters_1.equals(df_parameters_2)

    def test_calculate_scores_use_parameters_distributions(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        df_scores_1, df_parameters_1 = calculate_scores(activities,
                                                        impact_categories,
                                                        use_parameters_distributions=True)
        df_scores_2, df_parameters_2 = calculate_scores(activities,
                                                        impact_categories,
                                                        use_parameters_distributions=True)

        # Scores differ from one iteration to the other
        assert not df_scores_1.equals(df_scores_2)

        # Parameters differ from one iteration to the other
        assert not df_parameters_1.equals(df_parameters_2)

    def test_calculate_scores_set_parameters(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        df_scores_1, df_parameters_1 = calculate_scores(activities,
                                                        impact_categories,
                                                        parameters={"some_random_value": 2})
        df_scores_2, df_parameters_2 = calculate_scores(activities,
                                                        impact_categories,
                                                        parameters={"some_random_value": 3})

        # Parameter value is reflected in parameters
        assert df_parameters_1[df_parameters_1["parameter"] == "some_random_value"]["value_0"].values[0] == 2
        assert df_parameters_2[df_parameters_2["parameter"] == "some_random_value"]["value_0"].values[0] == 3

        # Scores differ from one iteration to the other
        assert not df_scores_1.equals(df_scores_2)

        # Parameters differ from one iteration to the other
        assert not df_parameters_1.equals(df_parameters_2)

    def test_calculate_scores_set_parameters_do_not_exist(self, imported_activities):
        activities = imported_activities

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

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

        with pytest.raises(ValueError):
            _, _ = calculate_scores(activities,
                                                            impact_categories,
                                                            parameters={"amount_beverage_carton": 2})

    def test_calculate_scores_no_parameters(self):
        # Ensure that everything runs smoothly when no ProjectParameters have been defined.
        activities = [bd.get_activity(name="apple production", location="IT")]
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        _, df_parameters = calculate_scores(activities,
                                              impact_categories, )

        assert len(df_parameters) == 0

    def test_calculate_scores_negative_reference_amount(self):
        # When the reference amount is negative, the calculated amount should also be negative
        # (and the impacts, positive.)
        activities = [bd.get_activity(name="treatment of waste yarn and waste textile, unsanitary landfill",
                                      location="IN")]
        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]
        df_scores, _ = calculate_scores(activities,
                                              impact_categories, )
        assert (df_scores["value_0"] >= 0).all()

    def test_calculate_scores_no_activities(self):
        activities = []

        impact_categories = [('ecoinvent-3.12', 'EF v3.1', 'acidification', 'accumulated exceedance (AE)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'climate change', 'global warming potential (GWP100)'),
                             ('ecoinvent-3.12', 'EF v3.1', 'water use',
                              'user deprivation potential (deprivation-weighted water consumption)')]

        with pytest.raises(ValueError):
            _, _ = calculate_scores(activities, impact_categories,)

    def test_calculate_scores_no_impact_categories(self, imported_activities):
        activities = imported_activities

        impact_categories = []

        with pytest.raises(ValueError):
            _, _ = calculate_scores(activities, impact_categories,)
