# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict
import ast

# import third-party modules
import bw2data as bd
from bw2data.parameters import ActivityParameter
import pandas as pd
import stats_arrays
import numpy as np
import pyexcel
from stats_arrays import UncertaintyBase

# import your own module


def _uncertainty_from_pedigree_matrix(pedigree: Tuple[int, int, int, int, int]) -> Dict[str, float]:
    # According to stats_array (https://stats-arrays.readthedocs.io/en/latest/), loc and scale contain the mean and standard deviation of the underlying normal distribution respectively.
    # This aligns with Ecospold2DataExtractor.extract_uncertainty_dict which defined loc as log(mu) and scale as sqrt(varianceWithPedigreeUncertainty), where mu and varianceWithPedigreeUncertainty are from the ecoinvent database.
    # However, the pedigree matrix factors are not given as variances.
    # We calculate the scale as in pedigree-matrix.PedigreeMatrix
    lognormal_location = np.log(1)

    # A. Ciroth, S. Muller, B. Weidema, and P. Lesage, “Empirically based uncertainty factors for the pedigree matrix in ecoinvent,” Int J Life Cycle Assess, vol. 21, no. 9, pp. 1338–1348, Sep. 2016, doi: 10.1007/s11367-013-0670-5.
    PEDIGREE_RELIABILITY = {1: 1.00,
                            2: 1.54,
                            3: 1.61,
                            4: 1.69,
                            5: 25.0}
    PEDIGREE_COMPLETENESS = {1: 1.0,
                             2: 1.03,
                             3: 1.04,
                             4: 1.08,
                             5: 25.0}
    PEDIGREE_TEMPORAL = {1: 1.0,
                         2: 1.03,
                         3: 1.10,
                         4: 1.19,
                         5: 1.29}
    PEDIGREE_GEOGRAPHICAL = {1: 1.0,
                             2: 1.04,
                             3: 1.08,
                             4: 1.11,
                             5: 25.0}
    PEDIGREE_TECHNOLOGICAL = {1: 1.0,
                              2: 1.18,
                              3: 1.65,
                              4: 2.08,
                              5: 2.8}

    pm_scores = np.array([PEDIGREE_RELIABILITY[pedigree[0]],
                          PEDIGREE_COMPLETENESS[pedigree[1]],
                          PEDIGREE_TEMPORAL[pedigree[2]],
                          PEDIGREE_GEOGRAPHICAL[pedigree[3]],
                          PEDIGREE_TECHNOLOGICAL[pedigree[4]]])
    lognormal_scale = np.sqrt(np.sum(np.log(pm_scores) ** 2)) / 2

    uncertainty = stats_arrays.UncertaintyBase.from_dicts({"loc": lognormal_location,
                                                           "scale": lognormal_scale,
                                                           "uncertainty_type": stats_arrays.LognormalUncertainty.id})
    return uncertainty

def import_foreground(file_path: str,
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
            uncertainty_map = {"Undefined": stats_arrays.UndefinedUncertainty.id,
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

            param = {"name": row["Name"]}
            try:
                param["amount"] = float(row["Value"])
                param["uncertainty"] = UncertaintyBase.from_dicts({"uncertainty_type": uncertainty_map[row["Uncertainty Type"]],
                                                                          "loc": row["Uncertainty Location"],
                                                                          "scale": row["Uncertainty Scale"],
                                                                          "shape": row["Uncertainty Shape"],
                                                                          "minimum": row["Uncertainty Minimum"],
                                                                          "maximum": row["Uncertainty Maximum"],})
            except ValueError:
                param["formula"] = row["Value"]
                param["uncertainty"] = None

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
                                 f"with activity {exc_act} does not match the activity's unit ({act["unit"]}).")

            if row["Group"] is np.nan:
                exc_group = None
            else:
                exc_group = row["Group"]
            # Create parameters for the exchange amount
            # Consist of an amount and a data quality component.
            # Data quality is defined from pedigree matrix
            # Amount is defined either from numerical value and uncertainty distribution OR formula
            param_data_quality = {"name": f"exc_dq_{exc_act.id}_{act.id}",
                                  "amount": 1,
                                  "uncertainty": _uncertainty_from_pedigree_matrix(ast.literal_eval(row["Data Quality"])),}

            uncertainty_map = {"Undefined": stats_arrays.UndefinedUncertainty.id,
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

            param_amount = {"name": f"exc_amount_{exc_act.id}_{act.id}",}
            try:
                param_amount["amount"] = float(row["Amount"])
                if uncertainty_map[row["Uncertainty Type"]] in [stats_arrays.UndefinedUncertainty.id,
                                                                stats_arrays.NoUncertainty.id,]:
                    loc = param_amount["amount"]
                else:
                    loc = row["Uncertainty Location"]
                param_amount["uncertainty"] = UncertaintyBase.from_dicts({"uncertainty_type": uncertainty_map[row["Uncertainty Type"]],
                                                                          "loc": loc,
                                                                          "scale": row["Uncertainty Scale"],
                                                                          "shape": row["Uncertainty Shape"],
                                                                          "minimum": row["Uncertainty Minimum"],
                                                                          "maximum": row["Uncertainty Maximum"],})
            except ValueError:
                param_amount["formula"] = row["Amount"]
                param_amount["uncertainty"] = None

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
