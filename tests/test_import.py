# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2data as bd
import pytest
import stats_arrays
import numpy as np

# import your own module
from lcatoolbox import import_foreground
from setup_bw_project import *

class TestImport:
    FILE_PATH = "tests/test_import_foreground.ods"

    def test_import_foreground(self):
        activities = import_foreground(self.FILE_PATH)

        fruit_salad = bd.get_activity(name="fruit_salad", location="DE")
        juice = bd.get_activity(name="juice", location="GLO")

        apple = bd.get_activity(name="apple production", location="IT")
        kiwi = bd.get_activity(name="kiwi production", location="GLO")
        anchovy = bd.get_activity(name="anchovy, capture by wooden purse seiner and landing whole, fresh",
                                  location="PE")
        biowaste = bd.get_activity(name="market for biowaste, kitchen and garden waste", location="GLO")
        container = bd.get_activity(name="beverage carton production, 1 L, for juice (ambient)", location="RER")
        orange = bd.get_activity(name="orange production, processing grade", location="RoW")
        water = bd.get_activity(name="Water, unspecified natural origin", categories=('natural resource', 'in water'))

        # Number of activities
        assert len(activities) == 2
        assert activities[0] == fruit_salad
        assert activities[1] == juice

        # Activities content
        assert fruit_salad["name"] == "fruit_salad"
        assert fruit_salad["unit"] == "item(s)"
        assert fruit_salad["location"] == "DE"
        assert juice["name"] == "juice"
        assert juice["unit"] == "liter"
        assert juice["location"] == "GLO"

        # Exchanges
        fruit_salad_exchanges = list(fruit_salad.exchanges())
        juice_exchanges = list(juice.exchanges())
        assert len(fruit_salad_exchanges) == 6
        assert len(juice_exchanges) == 4

        assert fruit_salad_exchanges[0]["amount"] == 1
        assert fruit_salad_exchanges[0]["unit"] == "item(s)"
        assert fruit_salad_exchanges[0].input == fruit_salad
        with pytest.raises(KeyError):
            _ = fruit_salad_exchanges[0]["formula"]

        assert fruit_salad_exchanges[1]["unit"] == "kilogram"
        assert fruit_salad_exchanges[1]["formula"] == f"exc_{apple.id}_{fruit_salad.id}"
        assert fruit_salad_exchanges[1].input == apple

        assert fruit_salad_exchanges[2]["unit"] == "kilogram"
        assert fruit_salad_exchanges[2]["formula"] == f"exc_{kiwi.id}_{fruit_salad.id}"
        assert fruit_salad_exchanges[2].input == kiwi

        assert fruit_salad_exchanges[3]["unit"] == "kilogram"
        assert fruit_salad_exchanges[3]["formula"] == f"exc_{anchovy.id}_{fruit_salad.id}"
        assert fruit_salad_exchanges[3].input == anchovy

        assert fruit_salad_exchanges[4]["unit"] == "liter"
        assert fruit_salad_exchanges[4]["formula"] == f"exc_{juice.id}_{fruit_salad.id}"
        assert fruit_salad_exchanges[4].input == juice

        assert fruit_salad_exchanges[5]["unit"] == "kilogram"
        assert fruit_salad_exchanges[5]["formula"] == f"exc_{biowaste.id}_{fruit_salad.id}"
        assert fruit_salad_exchanges[5].input == biowaste

        assert juice_exchanges[0]["unit"] == "liter"
        assert juice_exchanges[0]["amount"] == 1
        assert juice_exchanges[0].input == juice
        with pytest.raises(KeyError):
            _ = juice_exchanges[0]["formula"]

        assert juice_exchanges[1]["unit"] == "unit"
        assert juice_exchanges[1]["formula"] == f"exc_{container.id}_{juice.id}"
        assert juice_exchanges[1].input == container

        assert juice_exchanges[2]["unit"] == "kilogram"
        assert juice_exchanges[2]["formula"] == f"exc_{orange.id}_{juice.id}"
        assert juice_exchanges[2].input == orange

        assert juice_exchanges[3]["unit"] == "cubic meter"
        assert juice_exchanges[3]["formula"] == f"exc_{water.id}_{juice.id}"
        assert juice_exchanges[3].input == water

        # Parameters
        expected_parameters = []
        uncertainty_dq = stats_arrays.UncertaintyBase.from_dicts(
            {"loc": 0.,
             "scale": 0.5198473117654913,
             "uncertainty_type": stats_arrays.LognormalUncertainty.id})

        uncertainty_amount_apple = stats_arrays.UncertaintyBase.from_dicts(
            {"minimum": 0.25,
             "maximum": 0.75,
             "uncertainty_type": stats_arrays.UniformUncertainty.id})
        expected_parameters += [{"name": f"exc_{apple.id}_{fruit_salad.id}",
                                 "formula": f"exc_dq_{apple.id}_{fruit_salad.id}*exc_amount_{apple.id}_{fruit_salad.id}",},
                                {"name": f"exc_dq_{apple.id}_{fruit_salad.id}",
                                 "amount": 1.,
                                 "uncertainty": uncertainty_dq,},
                                {"name": f"exc_amount_{apple.id}_{fruit_salad.id}",
                                 "amount": 0.5,
                                 "uncertainty": uncertainty_amount_apple,}]

        uncertainty_amount_kiwi = stats_arrays.UncertaintyBase.from_dicts(
            {"loc": 0.125,
             "scale": 0.025,
             "uncertainty_type": stats_arrays.NormalUncertainty.id})
        expected_parameters += [{"name": f"exc_{kiwi.id}_{fruit_salad.id}",
                                 "formula": f"exc_dq_{kiwi.id}_{fruit_salad.id}*"
                                            f"exc_amount_{kiwi.id}_{fruit_salad.id}", },
                                {"name": f"exc_dq_{kiwi.id}_{fruit_salad.id}",
                                 "amount": 1.,
                                 "uncertainty": uncertainty_dq, },
                                {"name": f"exc_amount_{kiwi.id}_{fruit_salad.id}",
                                 "amount": 0.125,
                                 "uncertainty": uncertainty_amount_kiwi, }]

        uncertainty_amount_anchovy = stats_arrays.UncertaintyBase.from_dicts(
            {"loc": 0.,
             "uncertainty_type": stats_arrays.NoUncertainty.id})
        expected_parameters += [{"name": f"exc_{anchovy.id}_{fruit_salad.id}",
                                 "formula": f"exc_dq_{anchovy.id}_{fruit_salad.id}*"
                                            f"exc_amount_{anchovy.id}_{fruit_salad.id}", },
                                {"name": f"exc_dq_{anchovy.id}_{fruit_salad.id}",
                                 "amount": 1.,
                                 "uncertainty": uncertainty_dq, },
                                {"name": f"exc_amount_{anchovy.id}_{fruit_salad.id}",
                                 "amount": 0.,
                                 "uncertainty": uncertainty_amount_anchovy, }]

        uncertainty_amount_juice = stats_arrays.UncertaintyBase.from_dicts(
            {"loc": 0.1,
             "uncertainty_type": stats_arrays.NoUncertainty.id})
        expected_parameters += [{"name": f"exc_{juice.id}_{fruit_salad.id}",
                                 "formula": f"exc_dq_{juice.id}_{fruit_salad.id}*"
                                            f"exc_amount_{juice.id}_{fruit_salad.id}", },
                                {"name": f"exc_dq_{juice.id}_{fruit_salad.id}",
                                 "amount": 1.,
                                 "uncertainty": uncertainty_dq, },
                                {"name": f"exc_amount_{juice.id}_{fruit_salad.id}",
                                 "amount": 0.1,
                                 "uncertainty": uncertainty_amount_juice, }]

        uncertainty_amount_biowaste = stats_arrays.UncertaintyBase.from_dicts(
            {"loc": -0.1,
             "uncertainty_type": stats_arrays.NoUncertainty.id})
        expected_parameters += [{"name": f"exc_{biowaste.id}_{fruit_salad.id}",
                                 "formula": f"exc_dq_{biowaste.id}_{fruit_salad.id}*"
                                            f"exc_amount_{biowaste.id}_{fruit_salad.id}", },
                                {"name": f"exc_dq_{biowaste.id}_{fruit_salad.id}",
                                 "amount": 1.,
                                 "uncertainty": uncertainty_dq, },
                                {"name": f"exc_amount_{biowaste.id}_{fruit_salad.id}",
                                 "amount": -0.1,
                                 "uncertainty": uncertainty_amount_biowaste, }]

        expected_parameters += [{"name": f"exc_{container.id}_{juice.id}",
                                 "formula": f"exc_dq_{container.id}_{juice.id}*"
                                            f"exc_amount_{container.id}_{juice.id}", },
                                {"name": f"exc_dq_{container.id}_{juice.id}",
                                 "amount": 1.,
                                 "uncertainty": uncertainty_dq, },
                                {"name": f"exc_amount_{container.id}_{juice.id}",
                                 "formula": "amount_beverage_carton", }]

        uncertainty_amount_orange = stats_arrays.UncertaintyBase.from_dicts(
            {"loc": 3.,
             "scale": 0.5,
             "uncertainty_type": stats_arrays.NormalUncertainty.id})
        expected_parameters += [{"name": f"exc_{orange.id}_{juice.id}",
                                 "formula": f"exc_dq_{orange.id}_{juice.id}*"
                                            f"exc_amount_{orange.id}_{juice.id}", },
                                {"name": f"exc_dq_{orange.id}_{juice.id}",
                                 "amount": 1.,
                                 "uncertainty": uncertainty_dq, },
                                {"name": f"exc_amount_{orange.id}_{juice.id}",
                                 "amount": 3.,
                                 "uncertainty": uncertainty_amount_orange, }]

        uncertainty_amount_water = stats_arrays.UncertaintyBase.from_dicts(
            {"loc": 0.0005,
             "uncertainty_type": stats_arrays.NoUncertainty.id})
        expected_parameters += [{"name": f"exc_{water.id}_{juice.id}",
                                 "formula": f"exc_dq_{water.id}_{juice.id}*"
                                            f"exc_amount_{water.id}_{juice.id}", },
                                {"name": f"exc_dq_{water.id}_{juice.id}",
                                 "amount": 1.,
                                 "uncertainty": uncertainty_dq, },
                                {"name": f"exc_amount_{water.id}_{juice.id}",
                                 "amount": 0.0005,
                                 "uncertainty": uncertainty_amount_water, }]

        expected_parameters.append({"name": "some_random_value",
                                    "amount": 2.,
                                    "uncertainty": stats_arrays.UncertaintyBase.from_dicts(
                                        {"minimum": 1.5,
                                         "maximum": 2.5,
                                         "uncertainty_type": stats_arrays.UniformUncertainty.id})})
        expected_parameters.append({"name": "amount_beverage_carton",
                                    "formula": "0.5*some_random_value",})

        actual_parameters = {param.name: param.dict for param in ProjectParameter.select()}
        assert len(actual_parameters) == len(expected_parameters)
        for e_param in expected_parameters:
            for key, value in e_param.items():
                if key == "uncertainty":
                    expected_uncertainty = e_param["uncertainty"]
                    actual_uncertainty = actual_parameters[e_param["name"]]["uncertainty"]

                    assert np.array_equal(actual_uncertainty["loc"], expected_uncertainty["loc"], equal_nan=True)
                    assert np.array_equal(actual_uncertainty["scale"], expected_uncertainty["scale"], equal_nan=True)
                    assert np.array_equal(actual_uncertainty["shape"], expected_uncertainty["shape"], equal_nan=True)
                    assert np.array_equal(actual_uncertainty["minimum"], expected_uncertainty["minimum"], equal_nan=True)
                    assert np.array_equal(actual_uncertainty["maximum"], expected_uncertainty["maximum"], equal_nan=True)
                    assert np.array_equal(actual_uncertainty["negative"], expected_uncertainty["negative"], equal_nan=True)
                    assert np.array_equal(actual_uncertainty["uncertainty_type"], expected_uncertainty["uncertainty_type"], equal_nan=True)
                else:
                    assert actual_parameters[e_param["name"]][key] == value
