import bw2data as bd
from bw2data.parameters import ProjectParameter
from lcatoolbox import run_monte_carlo, import_foreground, get_impact_categories, copy_ecoinvent_activity

bd.projects.set_current("lca_toolbox_tests")

try:
    del bd.databases["foreground"]
    ProjectParameter.drop_table(safe=True, drop_sequences=True)
    ProjectParameter.create_table()
except KeyError:
    pass
foreground = bd.Database("foreground")
foreground.register()

#activities = import_foreground("../tests/test_import_foreground.ods")
impact_categories = get_impact_categories("EF v3.1")

act_1 = bd.get_activity(name="kiwi production", location="GLO")
act_2 = bd.get_activity(name="integrated circuit production, logic type", location="GLO")
act_1_copy = copy_ecoinvent_activity(act_1)
act_2_copy = copy_ecoinvent_activity(act_2)

scores, background, parameters = run_monte_carlo([act_1_copy, act_2_copy], impact_categories, 10)
