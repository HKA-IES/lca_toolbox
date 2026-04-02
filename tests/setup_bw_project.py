# -*- coding: utf-8 -*-

# import built-in module

# import third-party modules
import bw2io as bi
import bw2data as bd
import stats_arrays
from bw2data.parameters import ActivityParameter
import pytest

# import your own module


@pytest.fixture(scope="session", autouse=True)
def setup_brightway():
    bd.projects.set_current("lca_toolbox_tests")
    if 'ecoinvent-3.12-cutoff' in bd.databases:
        print('ecoinvent 3.12 is already present in the project')
        # del bd.databases['ecoinvent-3.12-cutoff']
        # del bd.databases['ecoinvent-3.12-biosphere']
    else:
        bi.import_ecoinvent_release(
            version='3.12',
            system_model='cutoff',  # can be cutoff / apos / consequential / EN15804
        )


@pytest.fixture
def fruit_salad():
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
                   formula="amount_beverage_carton",
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

    bd.parameters.new_project_parameters([{"name": "amount_beverage_carton",
                                             "formula": "0.5*some_random_value",},
                                          {"name": "some_random_value",
                                           "amount": 2,
                                           "uncertainty": stats_arrays.UncertaintyBase.from_dicts({"minimum": 1.5,
                                                                                                   "maximum": 2.5,
                                                                                                   "uncertainty_type": stats_arrays.UniformUncertainty.id,})},])

    bd.parameters.add_exchanges_to_group("group", fruit_salad)
    ActivityParameter.recalculate_exchanges("group")

    return fruit_salad
