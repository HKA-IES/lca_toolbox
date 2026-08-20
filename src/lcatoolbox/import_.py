# -*- coding: utf-8 -*-

# import built-in module
from typing import Tuple, List, Dict
import ast
import itertools
from copy import deepcopy

# import third-party modules
import bw2data as bd
from bw2data.parameters import ActivityParameter, ProjectParameter
from bw2data.errors import MultipleResults, UnknownObject
import pandas as pd
import stats_arrays
import numpy as np
import bw2calc as bc
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

# TODO: create function to export activity to a spreadsheet (!!!!)

def import_foreground(file_path: str,
                      data_quality_system: str,
                      foreground_db_name: str = "foreground") -> List[bd.backends.proxies.Activity]:

    foreground_db = bd.Database(foreground_db_name)
    foreground_db.register()

    wb = pyexcel.get_book(file_name=file_path)

    new_activities = {}

    # Create activities (sheets beginning with a_)
    # Exchanges are added later, to avoid a case where an exchange requires an activity which was not already created.
    for ws in wb:
        if ws.name[0:2] != "a_":
            continue

        n_rows = 0
        for el in ws.column[0]:
            if el == "":
                break
            n_rows += 1

        df_act = pd.read_excel(io=file_path, sheet_name=ws.name, usecols="A:B",
                               nrows=n_rows, header=None, index_col=0).transpose().squeeze()

        # Create activity
        new_act = foreground_db.new_node(name=df_act["Name"],
                                         location=df_act["Location"],
                                         product=df_act["Product"],
                                         unit=df_act["Unit"],
                                         type=bd.labels.chimaera_node_default)
        new_act.save()
        new_act.new_edge(amount=df_act["Amount"],
                         unit=df_act["Unit"],
                         input=new_act,
                         type=bd.labels.production_edge_default).save()
        new_activities[ws.name] = new_act

    # Add parameters from sheets starting with p_
    for ws in wb:
        if ws.name[0:2] != "p_":
            continue

        df_params = pd.read_excel(file_path,
                           sheet_name=ws.name)

        for _, row in df_params.iterrows():
            param = {"name": row["Name"]}
            try:
                param["amount"] = float(row["Value"])
                param["nominal"] = param["amount"]
                if UNCERTAINTY_TYPES_MAP[row["Uncertainty Type"]] in [stats_arrays.UndefinedUncertainty.id,
                                                                stats_arrays.NoUncertainty.id,]:
                    loc = param["amount"]
                else:
                    loc = row["Uncertainty Location"]
                param["uncertainty"] = UncertaintyBase.from_dicts({"uncertainty_type": UNCERTAINTY_TYPES_MAP[row["Uncertainty Type"]],
                                                                          "loc": loc,
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
        act = new_activities[ws.name]

        n_rows_to_skip = 0
        for el in ws.column[0]:
            n_rows_to_skip += 1
            if el == "":
                break

        df_exchanges = pd.read_excel(file_path,
                       sheet_name=ws.name,
                       skiprows=n_rows_to_skip,)
        df_exchanges["Product"] = df_exchanges["Product"].fillna("")
        df_exchanges["Location"] = df_exchanges["Location"].fillna("")
        df_exchanges["Categories"] = df_exchanges["Categories"].fillna("")

        for _, row in df_exchanges.iterrows():
            activity_search_args = {"name": row["Activity"]}

            if row["Product"] != "":
                activity_search_args["product"] = row["Product"]

            if row["Location"] != "":
                activity_search_args["location"] = row["Location"]

            if row["Categories"] != "":
                activity_search_args["categories"] = ast.literal_eval(row["Categories"])

            try:
                exc_act = bd.get_activity(**activity_search_args)
            except MultipleResults:
                raise RuntimeError(f"Multiple activities found for criterias {activity_search_args}.")
            except UnknownObject:
                raise RuntimeError(f"No activity found for criterias {activity_search_args}.")


            if row["Type"] == "technosphere":
                exc_type = bd.labels.consumption_edge_default
            elif row["Type"] == "biosphere":
                exc_type = bd.labels.biosphere_edge_default

            try:
                amount = float(row["Amount"])
                formula = None
            except ValueError:
                amount = 1
                formula = row["Amount"]

            _create_exchange(parent_act=act, provider_act=exc_act, type_=exc_type,
                             amount=amount, unit=row["Unit"], group=row["Group"],
                             uncertainty_type=UNCERTAINTY_TYPES_MAP[row["Uncertainty Type"]],
                             uncertainty_location=row["Uncertainty Location"],
                             uncertainty_scale=row["Uncertainty Scale"],
                             uncertainty_shape=row["Uncertainty Shape"],
                             uncertainty_min=row["Uncertainty Minimum"],
                             uncertainty_max=row["Uncertainty Maximum"],
                             formula=formula,
                             data_quality_tuple=tuple(int(val) for val in row["Data Quality"].strip("()").split(";")),
                             data_quality_system=data_quality_system,
                             activity_fit_tuple=tuple(int(val) for val in row["Activity Fit"].strip("()").split(";"))
                             )

        bd.parameters.add_exchanges_to_group("group", act)

    ActivityParameter.recalculate_exchanges("group")

    # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
    # Why? I don't know...
    _ = bc.LCA(demand={act: 1 for act in new_activities.values()}, method=list(bd.methods)[0])

    return list(new_activities.values())

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
        if "pedigree" in exc:
            dq_tuple = (exc["pedigree"]["reliability"],
                        exc["pedigree"]["completeness"],
                        exc["pedigree"]["temporal correlation"],
                        exc["pedigree"]["geographical correlation"],
                        exc["pedigree"]["further technological correlation"],)
        else:
            dq_tuple = (1, 1, 1, 1, 1)

        if exc["uncertainty type"] == stats_arrays.UndefinedUncertainty.id:
            uncertainty_type = stats_arrays.NoUncertainty.id
            uncertainty_location = exc["loc"]
            uncertainty_scale = None
        elif exc["uncertainty type"] == stats_arrays.LognormalUncertainty.id:
            if exc["scale without pedigree"] > 0:
                uncertainty_type = stats_arrays.LognormalUncertainty.id
                uncertainty_location = exc["loc"]
                uncertainty_scale = exc["scale without pedigree"]
            else:
                uncertainty_type = stats_arrays.NoUncertainty.id
                uncertainty_location = exc.amount
                uncertainty_scale = None
        elif exc["uncertainty type"] == stats_arrays.NormalUncertainty.id:
            uncertainty_type = stats_arrays.NormalUncertainty.id
            uncertainty_location = exc["loc"]
            uncertainty_scale = exc["scale without pedigree"]
        else:
            raise ValueError(f"Unsupported uncertainty type: {exc["uncertainty type"]}")

        _create_exchange(parent_act=new_act, provider_act=exc.input, type_=exc["type"],
                         amount=exc.amount, unit=exc.unit,
                         uncertainty_type=uncertainty_type,
                         uncertainty_location=uncertainty_location,
                         uncertainty_scale=uncertainty_scale,
                         uncertainty_shape=None,
                         uncertainty_min=None,
                         uncertainty_max=None,
                         data_quality_tuple=dq_tuple,
                         data_quality_system="ecoinvent3")

    bd.parameters.add_exchanges_to_group("group", new_act)
    ActivityParameter.recalculate_exchanges("group")

    # To solve the NonSquareTechnosphere error which pops up when running the MultiLCA, first run the following
    # Why? I don't know...
    _ = bc.LCA(demand={new_act: 1}, method=list(bd.methods)[0])

    return new_act

def reset_foreground(foreground_db: str = "foreground"):
    try:
        del bd.databases[foreground_db]
    except KeyError:
        pass
    ProjectParameter.drop_table(safe=True, drop_sequences=True)
    ProjectParameter.create_table()
    foreground = bd.Database(foreground_db)
    foreground.register()

def apply_openlca_preprocessing_to_ecoinvent(ecoinvent_db_name: str):
    """
    Some uncertainties from ecoinvent are much too high. This function applies the same pre-processing to the ecoinvent
    database as done by GreenDelta for the OpenLCA version of Ecoinvent 3.11.

    Specifically,
    - all uncertainties in exchanges that are not log-normal are replaced by no uncertainty;
    - geometric sigma for log-normal uncertainty in exchanges are capped at 4.

    See https://www.openlca.org/ecoinvent-3-11-available-for-openlca/.
    """
    db_ei = bd.Database(ecoinvent_db_name)
    n_activities = len(db_ei)
    print(f"{n_activities} activities to update.")
    for i, act in enumerate(db_ei):
        if (i+1)%100 == 0:
            print(f"{i+1} / {n_activities}")
        for exc in act.exchanges():
            if exc["uncertainty type"] == stats_arrays.UndefinedUncertainty.id:
                pass
            elif exc["uncertainty type"] == stats_arrays.LognormalUncertainty.id:
                if exc["scale"] > np.log(4):
                    exc["scale"] = np.log(4)
                    exc.save()
            else:
                exc["uncertainty type"] = stats_arrays.UndefinedUncertainty.id
                exc.save()

def _uncertainty_from_pedigree(pedigree: Tuple[int, int, int, int, int],
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

    if scale > 0:
        uncertainty = stats_arrays.UncertaintyBase.from_dicts({"loc": np.log(1),
                                                               "scale": scale,
                                                               "uncertainty_type": stats_arrays.LognormalUncertainty.id})
    else:
        uncertainty = stats_arrays.UncertaintyBase.from_dicts({"loc": 1,
                                                               "uncertainty_type": stats_arrays.NoUncertainty.id})
    return uncertainty

def _create_exchange(parent_act: bd.backends.Activity,
                     provider_act: bd.backends.Activity,
                     type_: str,
                     amount: float,
                     unit: str,
                     uncertainty_type: int,
                     uncertainty_location: float,
                     uncertainty_scale: float,
                     uncertainty_shape: float,
                     uncertainty_min: float,
                     uncertainty_max: float,
                     group: str = None,
                     formula: str = None,
                     data_quality_tuple: Tuple[int, int, int, int, int] = (1, 1, 1, 1, 1),
                     data_quality_system: str = "ecoinvent3",
                     activity_fit_tuple: Tuple[int, int, int, int, int] = (1, 1, 1, 1, 1)):

    if unit != provider_act["unit"]:
        raise ValueError(f"Mismatch between specified unit ({unit}) and exchange activity unit ({provider_act["unit"]}) for exchange"
                         f"from {provider_act} to {parent_act}.")

    new_exc = parent_act.new_exchange(amount=1,
                               unit=unit,
                               input=provider_act,
                               type=type_,
                               group=group)
    new_exc.save()

    # Create parameters for the exchange amount
    # Consist of an amount and a data quality component.
    # Data quality is defined from pedigree matrix
    # Amount is defined either from numerical value and uncertainty distribution OR formula
    param_data_quality = {"name": f"exc_{new_exc.id}_data_quality",
                          "amount": 1,
                          "nominal": 1,
                          "uncertainty": _uncertainty_from_pedigree(data_quality_tuple, data_quality_system), }
    param_activity_fit = {"name": f"exc_{new_exc.id}_activity_fit",
                          "amount": 1,
                          "nominal": 1,
                          "uncertainty": _uncertainty_from_pedigree(activity_fit_tuple, data_quality_system), }

    param_amount = {"name": f"exc_{new_exc.id}_amount", }

    if formula is not None:
        param_amount["formula"] = formula
        param_amount["uncertainty"] = None
        param_amount["nominal"] = None
    else:
        param_amount["amount"] = amount
        param_amount["nominal"] = amount
        if uncertainty_type in [stats_arrays.UndefinedUncertainty.id,
                                                              stats_arrays.NoUncertainty.id, ]:
            loc = amount
        else:
            loc = uncertainty_location
        param_amount["uncertainty"] = UncertaintyBase.from_dicts(
            {"uncertainty_type": uncertainty_type,
             "loc": loc,
             "scale": uncertainty_scale,
             "shape": uncertainty_shape,
             "minimum": uncertainty_min,
             "maximum": uncertainty_max, })

    # using deepcopy because the parameter dictionnaries are modified by .new_project_parameters()
    bd.parameters.new_project_parameters([deepcopy(param_data_quality),
                                          deepcopy(param_activity_fit),
                                          deepcopy(param_amount)])

    new_exc["formula"] = f"{param_amount["name"]}*{param_data_quality["name"]}*{param_activity_fit["name"]}"
    new_exc.save()
