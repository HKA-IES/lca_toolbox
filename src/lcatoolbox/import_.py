# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict
import ast
import itertools

# import third-party modules
import bw2data as bd
from bw2data.parameters import ActivityParameter
import pandas as pd
import stats_arrays
import numpy as np
import pyexcel
from stats_arrays import UncertaintyBase

# import your own module


UNCERTAINTY_TYPES_MAP = {"Undefined": stats_arrays.UndefinedUncertainty.id,
                         "No uncertainty": stats_arrays.NoUncertainty.id,
                         "Lognormal": stats_arrays.LognormalUncertainty.id,
                         "Normal": stats_arrays.NormalUncertainty.id,
                         "Uniform": stats_arrays.UniformUncertainty.id,
                         "Triangular": stats_arrays.TriangularUncertainty.id,
                         "Bernoulli": stats_arrays.BernoulliUncertainty.id,
                         "Discrete Uniform": stats_arrays.DiscreteUniform.id,
                         "Weibull": stats_arrays.WeibullUncertainty.id,
                         "Gamma": stats_arrays.GammaUncertainty.id,
                         "Beta": stats_arrays.BetaUncertainty.id,
                         "Generalized Extreme Value": stats_arrays.GeneralizedExtremeValueUncertainty.id,
                         "Student's T": stats_arrays.StudentsTUncertainty.id,}

def import_foreground(file_path: str,
                      data_quality_system: str,
                      foreground_db_name: str = "foreground") -> List[bd.backends.proxies.Activity]:
    foreground_db = bd.Database(foreground_db_name)
    foreground_db.register()

    wb = pyexcel.get_book(file_name=file_path)

    new_activities = []

    # Create activities (sheets beginning with a_)
    # Exchanges are added later, to avoid a case where an exchange requires an activity which was not already created.
    for ws in wb:
        if ws.name[0:2] != "a_":
            continue

        # Check that formatting is OK
        try:
            assert ws["A1"] == "Name"
            assert ws["A2"] == "Unit"
            assert ws["A3"] == "Location"
            assert ws["A4"] == "Reference Amount"
            assert ws["A5"] == "Notes"
        except AssertionError:
            raise RuntimeError(f"sheet {ws.name} not formatted properly.")

        new_act_name = ws["B1"]
        new_act_unit = ws["B2"]
        new_act_location = ws["B3"]
        new_act_ref_amount = ws["B4"]

        # Create activity
        new_act = foreground_db.new_node(name=new_act_name,
                                         unit=new_act_unit,
                                         location=new_act_location,
                                         type=bd.labels.chimaera_node_default)
        new_act.save()
        new_act.new_edge(amount=new_act_ref_amount,
                         unit=new_act_unit,
                         input=new_act,
                         type=bd.labels.production_edge_default).save()
        new_activities.append(new_act)

    # Add parameters from sheets starting with p_
    for ws in wb:
        if ws.name[0:2] != "p_":
            continue

        df = pd.read_excel(file_path,
                           sheet_name=ws.name)

        for _, row in df.iterrows():
            param = {"name": row["Name"]}
            try:
                param["amount"] = float(row["Value"])
                param["nominal"] = param["amount"]
                param["uncertainty"] = UncertaintyBase.from_dicts({"uncertainty_type": UNCERTAINTY_TYPES_MAP[row["Uncertainty Type"]],
                                                                          "loc": row["Uncertainty Location"],
                                                                          "scale": row["Uncertainty Scale"],
                                                                          "shape": row["Uncertainty Shape"],
                                                                          "minimum": row["Uncertainty Minimum"],
                                                                          "maximum": row["Uncertainty Maximum"],})
            except ValueError:
                param["formula"] = row["Value"]
                param["uncertainty"] = None
                param["nominal"] = None

            bd.parameters.new_project_parameters([param,])

    # Add all exchanges
    for ws in wb:
        if ws.name[0:2] != "a_":
            continue

        act = bd.get_activity(name=ws["B1"],
                                  location=ws["B3"],)

        df = pd.read_excel(file_path,
                       sheet_name=ws.name,
                       skiprows=6)

        for _, row in df.iterrows():
            if row["Type"] == "technosphere":
                exc_act = bd.get_activity(name=row["Activity"],
                                      location=row["Location"],)
                exc_type = bd.labels.consumption_edge_default
            elif row["Type"] == "biosphere":
                exc_act = bd.get_activity(name=row["Activity"],
                                          categories=ast.literal_eval(row["Categories"]),)
                exc_type = bd.labels.biosphere_edge_default

            if row["Unit"] != exc_act["unit"]:
                raise ValueError(f"In new activity {act}, the specified unit ({row["Unit"]}) for the exchange "
                                 f"with activity {exc_act} does not match the activity's unit ({exc_act["unit"]}).")

            if row["Group"] is np.nan:
                exc_group = None
            else:
                exc_group = row["Group"]
            # Create parameters for the exchange amount
            # Consist of an amount and a data quality component.
            # Data quality is defined from pedigree matrix
            # Amount is defined either from numerical value and uncertainty distribution OR formula
            dq_tuple = tuple(int(val) for val in row["Data Quality"].strip("()").split(";"))
            param_data_quality = {"name": f"exc_dq_{exc_act.id}_{act.id}",
                                  "amount": 1,
                                  "nominal": 1,
                                  "uncertainty": _uncertainty_from_pedigree_matrix(dq_tuple, data_quality_system),}

            param_amount = {"name": f"exc_amount_{exc_act.id}_{act.id}",}
            try:
                param_amount["amount"] = float(row["Amount"])
                param_amount["nominal"] = param_amount["amount"]
                if UNCERTAINTY_TYPES_MAP[row["Uncertainty Type"]] in [stats_arrays.UndefinedUncertainty.id,
                                                                stats_arrays.NoUncertainty.id,]:
                    loc = param_amount["amount"]
                else:
                    loc = row["Uncertainty Location"]
                param_amount["uncertainty"] = UncertaintyBase.from_dicts({"uncertainty_type": UNCERTAINTY_TYPES_MAP[row["Uncertainty Type"]],
                                                                          "loc": loc,
                                                                          "scale": row["Uncertainty Scale"],
                                                                          "shape": row["Uncertainty Shape"],
                                                                          "minimum": row["Uncertainty Minimum"],
                                                                          "maximum": row["Uncertainty Maximum"],})
            except ValueError:
                param_amount["formula"] = row["Amount"]
                param_amount["uncertainty"] = None
                param_amount["nominal"] = None

            param_exc = {"name": f"exc_{exc_act.id}_{act.id}",
                               "formula": f"{param_data_quality["name"]}*{param_amount["name"]}"}

            act.new_exchange(amount=1,
                                   formula=f"{param_exc["name"]}",
                                    unit=row["Unit"],
                                    input=exc_act,
                                    type=exc_type,
                                    group=exc_group).save()
            bd.parameters.new_project_parameters([param_data_quality,
                                                  param_amount,
                                                  param_exc])
        bd.parameters.add_exchanges_to_group("group", act)



    ActivityParameter.recalculate_exchanges("group")

    return new_activities

def copy_ecoinvent_activity(activity: bd.backends.proxies.Activity,
                      foreground_db_name: str = "foreground") -> bd.backends.proxies.Activity:
    foreground_db = bd.Database(foreground_db_name)

    new_act_data = {key: value for key, value in activity.items()
                    if key not in ["database", "id", "code"]}
    new_act = foreground_db.new_node(**new_act_data)
    new_act.save()

    for exc_prod in activity.production():
        new_act.new_edge(amount=exc_prod.amount,
                         unit=exc_prod.unit,
                         input=new_act,
                         type=bd.labels.production_edge_default).save()

    for exc in itertools.chain(activity.technosphere(), activity.biosphere()):
        dq_tuple = (exc["pedigree"]["reliability"],
                    exc["pedigree"]["completeness"],
                    exc["pedigree"]["temporal correlation"],
                    exc["pedigree"]["geographical correlation"],
                    exc["pedigree"]["further technological correlation"],)
        data_quality_uncertainty = _uncertainty_from_pedigree_matrix(dq_tuple)
        param_data_quality = {"name": f"exc_dq_{exc.input.id}_{new_act.id}",
                              "amount": 1.0,
                              "nominal": 1.0,
                              "uncertainty": data_quality_uncertainty, }
        amount_uncertainty = UncertaintyBase.from_dicts({"uncertainty_type": stats_arrays.LognormalUncertainty.id,
                                                                          "loc": exc["loc"],
                                                                          "scale": exc["scale without pedigree"],})
        param_amount = {"name": f"exc_amount_{exc.input.id}_{new_act.id}",
                        "amount": exc.amount,
                        "nominal": exc.amount,
                        "uncertainty": amount_uncertainty, }
        param_exc = {"name": f"exc_{exc.input.id}_{new_act.id}",
                     "formula": f"{param_data_quality["name"]}*{param_amount["name"]}"}
        new_act.new_edge(amount=1,
                         formula=param_exc["name"],
                         unit=exc.unit,
                         input=exc.input,
                         type=exc["type"]).save()
        bd.parameters.new_project_parameters([param_data_quality,
                                              param_amount,
                                              param_exc])

    bd.parameters.add_exchanges_to_group("group", new_act)
    ActivityParameter.recalculate_exchanges("group")
    return new_act


def _uncertainty_from_pedigree_matrix(pedigree: Tuple[int, int, int, int, int],
                                      data_quality_system: str = "ecoinvent3") -> Dict[str, float]:
    """
    data_quality_system one of "ecoinvent3" (https://support.ecoinvent.org/uncertainties) or "ciroth2016" (factors from [1] with n.a. set to 25 like in openLCA).

    [1] A. Ciroth, S. Muller, B. Weidema, and P. Lesage, “Empirically based uncertainty factors for the pedigree matrix in ecoinvent,” Int J Life Cycle Assess, vol. 21, no. 9, pp. 1338–1348, Sep. 2016, doi: 10.1007/s11367-013-0670-5.
    """
    # According to stats_array (https://stats-arrays.readthedocs.io/en/latest/), loc and scale contain the mean and standard deviation of the underlying normal distribution respectively.
    # This aligns with Ecospold2DataExtractor.extract_uncertainty_dict which defined loc as log(mu) and scale as sqrt(varianceWithPedigreeUncertainty), where mu and varianceWithPedigreeUncertainty are from the ecoinvent database.
    # However, the pedigree matrix factors are not given as variances.
    # We calculate the scale as in pedigree-matrix.PedigreeMatrix

    def ei3conv(x):
        # eq. 12.14 of [1] R. Heijungs, Probability, Statistics and Life Cycle Assessment: Guidance for Dealing with Uncertainty and Sensitivity. Cham: Springer International Publishing, 2024. doi: 10.1007/978-3-031-49317-1.
        return np.exp(np.sqrt(x))**2

    DQS = {"ecoinvent3": [{1: ei3conv(0.000), 2: ei3conv(0.0006), 3: ei3conv(0.002), 4: ei3conv(0.008), 5: ei3conv(0.04)}, # reliability
                          {1: ei3conv(0.000), 2: ei3conv(0.0001), 3: ei3conv(0.0006), 4: ei3conv(0.002), 5: ei3conv(0.008)}, # completeness
                          {1: ei3conv(0.000), 2: ei3conv(0.0002), 3: ei3conv(0.002), 4: ei3conv(0.008), 5: ei3conv(0.04)}, # temporal correlation
                          {1: ei3conv(0.000), 2: ei3conv(2.5e-5), 3: ei3conv(0.0001), 4: ei3conv(0.0006), 5: ei3conv(0.002)}, # geographical correlation
                          {1: ei3conv(0.000), 2: ei3conv(0.0006), 3: ei3conv(0.008), 4: ei3conv(0.04), 5: ei3conv(0.12)}, # further technological correlation
                          ],
           "ciroth2016": [{1: 1.00, 2: 1.54, 3: 1.61, 4: 1.69, 5: 25.0}, # reliability
                          {1: 1.00, 2: 1.03, 3: 1.04, 4: 1.08, 5: 25.0}, # completeness
                          {1: 1.00, 2: 1.03, 3: 1.10, 4: 1.19, 5: 1.29}, # temporal correlation
                          {1: 1.00, 2: 1.04, 3: 1.08, 4: 1.11, 5: 25.0}, # geographical correlation
                          {1: 1.00, 2: 1.18, 3: 1.65, 4: 2.08, 5: 2.80}, # further technological correlation
                          ],
           }

    pm_scores = np.array([DQS[data_quality_system][i][pedigree[i]] for i in range(len(pedigree))])
    scale = np.sqrt(np.sum(np.log(pm_scores) ** 2)) / 2

    uncertainty = stats_arrays.UncertaintyBase.from_dicts({"loc": np.log(1),
                                                           "scale": scale,
                                                           "uncertainty_type": stats_arrays.LognormalUncertainty.id})
    return uncertainty
