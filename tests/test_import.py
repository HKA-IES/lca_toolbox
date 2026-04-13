# -*- coding: utf-8 -*-

# import built-in module
import itertools

# import third-party modules
import bw2data as bd
from bw2data.parameters import ProjectParameter
import pytest
import stats_arrays
import numpy as np

# import your own module
from lcatoolbox import import_foreground, copy_ecoinvent_activity
from setup_bw_project import setup_brightway

class TestImport:


    def test_import_foreground(self):
        activities = import_foreground("test_import_foreground.ods",
                                       "ciroth2016")

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

        expected_parameters += [{"name": f"exc_{biowaste.id}_{fruit_salad.id}",
                                 "formula": f"exc_dq_{biowaste.id}_{fruit_salad.id}*"
                                            f"exc_amount_{biowaste.id}_{fruit_salad.id}", },
                                {"name": f"exc_dq_{biowaste.id}_{fruit_salad.id}",
                                 "amount": 1.,
                                 "uncertainty": uncertainty_dq, },
                                {"name": f"exc_amount_{biowaste.id}_{fruit_salad.id}",
                                 "formula": "-what_a_waste"}]

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
        expected_parameters.append({"name": "what_a_waste",
                                    "amount": 0.1,
                                    "uncertainty": stats_arrays.UncertaintyBase.from_dicts(
                                        {"loc": 0.1,
                                         "scale": 0.02,
                                         "uncertainty_type": stats_arrays.NormalUncertainty.id})})

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

    # TODO: Write better tests
    def test_copy_ecoinvent_activity(self):
        activity = bd.get_activity(name="transport, freight, train, diesel",
                                   location="CN")
        activity_copy = copy_ecoinvent_activity(activity)

        # Activity data
        assert activity_copy["name"] == activity["name"]
        assert activity_copy["unit"] == activity["unit"]
        assert activity_copy["location"] == activity["location"]
        assert activity_copy.id != activity.id
        assert activity_copy["database"] == "foreground"

        # Production exchange
        assert len(activity.production()) == len(activity_copy.production())
        for exc, exc_copy in zip(activity.production(), activity_copy.production()):
            assert exc_copy.id != exc.id
            assert exc_copy.amount == exc.amount
            assert exc_copy.input == activity_copy
            assert exc_copy.unit == exc.unit
            assert exc_copy["type"] == exc["type"]

        # Technosphere and biosphere exchanges
        assert len(activity_copy.technosphere()) == len(activity.technosphere())
        assert len(activity_copy.biosphere()) == len(activity.biosphere())
        expected_params = []
        for exc, exc_copy in zip(itertools.chain(activity.technosphere(), activity.biosphere()),
                                 itertools.chain(activity_copy.technosphere(), activity_copy.biosphere())):
            assert exc_copy.id != exc.id
            assert exc_copy.amount == exc.amount
            assert exc_copy.input == exc.input
            assert exc_copy.uncertainty == {}
            assert exc_copy.uncertainty_type == stats_arrays.UndefinedUncertainty
            assert exc_copy.unit == exc.unit
            assert exc_copy["formula"] == f"exc_{exc_copy.input.id}_{activity_copy.id}"

            data_quality_uncertainty = {"uncertainty_type": stats_arrays.LognormalUncertainty.id,
                                        "loc": 0.0,
                                        "scale": np.sqrt(exc["scale"]**2 - exc["scale without pedigree"]**2)}
            expected_param_data_quality = {"name": f"exc_dq_{exc.input.id}_{activity_copy.id}",
                                           "amount": 1.0,
                                           "nominal": 1.0,
                                           "uncertainty": stats_arrays.UncertaintyBase.from_dicts(data_quality_uncertainty)}
            if exc["scale without pedigree"] > 0:
                amount_uncertainty = {"uncertainty_type": stats_arrays.LognormalUncertainty.id,
                                            "loc": np.log(exc["amount"]),
                                            "scale": exc["scale without pedigree"]}
            else:
                amount_uncertainty = {"uncertainty_type": stats_arrays.NoUncertainty.id,
                                      "loc": exc["amount"]}
            expected_param_amount = {"name": f"exc_amount_{exc.input.id}_{activity_copy.id}",
                                     "amount": exc["amount"],
                                     "nominal": exc["amount"],
                                     "uncertainty": stats_arrays.UncertaintyBase.from_dicts(amount_uncertainty)}
            expected_param_exc = {"name": f"exc_{exc.input.id}_{activity_copy.id}",
                                  "amount": exc["amount"],
                                  "formula": f"{expected_param_data_quality["name"]}*{expected_param_amount["name"]}",}
            expected_params += [expected_param_data_quality,
                                expected_param_amount,
                                expected_param_exc]

        # Parameters
        assert (len(ProjectParameter.select()) ==
                (len(activity_copy.technosphere()) + len(activity_copy.biosphere())) * 3)
        for actual_param, expected_param in zip(ProjectParameter.select(), expected_params):
            assert set(actual_param.dict.keys()) == set(expected_param.keys())
            for key in actual_param.dict.keys():
                if key == "uncertainty":
                    assert np.allclose(actual_param.dict[key]["loc"], expected_param[key]["loc"], equal_nan=True)
                    assert np.allclose(actual_param.dict[key]["scale"], expected_param[key]["scale"], equal_nan=True)
                    assert np.allclose(actual_param.dict[key]["shape"], expected_param[key]["shape"], equal_nan=True)
                    assert np.allclose(actual_param.dict[key]["minimum"], expected_param[key]["minimum"],
                                          equal_nan=True)
                    assert np.allclose(actual_param.dict[key]["maximum"], expected_param[key]["maximum"],
                                          equal_nan=True)
                    assert np.allclose(actual_param.dict[key]["negative"], expected_param[key]["negative"],
                                          equal_nan=True)
                    assert np.array_equal(actual_param.dict[key]["uncertainty_type"],
                                          expected_param[key]["uncertainty_type"], equal_nan=True)
                else:
                    assert actual_param.dict[key] == expected_param[key]

    def test_copy_ecoinvent_activity_pedigree_missing(self):
        """
        If no pedigree is specified for an exchange,
        dq uncertainty is NoUncertainty.
        """
        activity = bd.get_activity(name="market for biowaste, kitchen and garden waste",
                                   location="GLO")
        activity_copy = copy_ecoinvent_activity(activity)

        # TODO: Check contents

    def test_copy_ecoinvent_activity_negative_scale(self):
        """
        Ensure that no negative scale is created.
        """
        activity = bd.get_activity(name="board, softwood, raw, kiln drying to u=10%",
                                   location="CA-QC")
        activity_copy = copy_ecoinvent_activity(activity)

        # TODO: Check contents

    def test_copy_ecoinvent_activity_normal_uncertainty(self):
        """
        Ensure that no negative scale is created.
        """
        activity = bd.get_activity(name="pea production, organic, hill region",
                                   location="CH")
        activity_copy = copy_ecoinvent_activity(activity)

        # TODO: Check contents

    def test_copy_ecoinvent_activity_edge_case_1(self):
        activity = bd.get_activity(name="petroleum and gas production, offshore",
                                   location="IN",
                                   product="natural gas, high pressure")
        activity_copy = copy_ecoinvent_activity(activity)
        # TODO: problem is scale for exchange bGas, natural (is null)

    def test_copy_ecoinvent_activity_edge_case_2(self):
        activity = bd.get_activity(name="treatment of waste reinforced plasterboard, sorting plant",
                                   location="CH",
                                   product="waste reinforced plasterboard")
        activity_copy = copy_ecoinvent_activity(activity)

        # TODO: problem is scale for exchange ?? (is null)

    def test_copy_ecoinvent_activity_edge_case_3(self):
        activity = bd.get_activity(name="treatment of waste polyurethane, municipal incineration",
                                   location="GLO",
                                   product="waste polyurethane")
        activity_copy = copy_ecoinvent_activity(activity)

        # TODO: problem is scale for exchange ?? (is null)
