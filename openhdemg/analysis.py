"""
This module contains all the functions used to analyse the MUs properties.
"""

import pandas as pd
import numpy as np
from openhdemg.tools import showselect, compute_idr, compute_covsteady


def compute_thresholds(emgfile, event_="rt_dert", type_="abs_rel", mvif=0):
    """
    This function calculates the recruitment/derecruitment thresholds in absolute and relative therms.

    Parameters
    ----------
    emgfile: dict
        The dictionary containing the emgfile.

    event_: str, default "rt_dert"
        When to calculate the thresholds. Input parameters for event_ are:
            "rt_dert" means that both recruitment and derecruitment tresholds will be calculated.
            "rt" means that only recruitment tresholds will be calculated.
            "dert" means that only derecruitment tresholds will be calculated.

    type_: str, default "abs_rel"
        The tipe of value to calculate. Input parameters for type_ are:
            "abs_rel" means that both absolute and relative tresholds will be calculated.
            "rel" means that only relative tresholds will be calculated.
            "abs" means that only absolute tresholds will be calculated.

    mvif: float, default 0
        The maximum voluntary isometric force (MViF).
        if mvif is 0, the user is asked to input mvif; otherwise, the value passed is used.

    Returns
    -------
    mus_thresholds: pd.DataFrame
        A DataFrame containing the requested thresholds.
    """

    # Extract the variables of interest from the EMG file
    NUMBER_OF_MUS = emgfile["NUMBER_OF_MUS"]
    MUPULSES = emgfile["MUPULSES"]
    REF_SIGNAL = emgfile["REF_SIGNAL"]

    # Check that all the inputs are correct
    assert event_ in [
        "rt_dert",
        "rt",
        "dert",
    ], f"event_ must be one of the following strings: rt_dert, rt, dert. {event_} was passed instead."
    assert type_ in [
        "abs_rel",
        "rel",
        "abs",
    ], f"event_ must be one of the following strings: abs_rel, rel, abs. {event_} was passed instead."
    if not isinstance(mvif, (float, int)):
        raise Exception(
            f"mvif must be one of the following types: float, int. {type(mvif)} was passed instead."
        )

    if type_ != "rel" and mvif == 0:
        # Ask the user to input MViF
        mvif = int(
            input("--------------------------------\nEnter MVC value in newton: ")
        )

    # Create an object to append the results
    toappend = []
    # Loop all the MUs
    for i in range(NUMBER_OF_MUS):
        # Detect the first and last firing of the MU and manage the exception of a single MU
        mup_rec = MUPULSES[i][0]
        mup_derec = MUPULSES[i][-1]

        # Calculate absolute and relative RT and DERT if requested
        abs_RT = ((float(REF_SIGNAL.loc[mup_rec]) * float(mvif)) / 100) * 9.81
        abs_DERT = ((float(REF_SIGNAL.loc[mup_derec]) * float(mvif)) / 100) * 9.81
        rel_RT = float(REF_SIGNAL.loc[mup_rec])
        rel_DERT = float(REF_SIGNAL.loc[mup_derec])

        if event_ == "rt_dert" and type_ == "abs_rel":
            toappend.append(
                {
                    "abs_RT": abs_RT,
                    "abs_DERT": abs_DERT,
                    "rel_RT": rel_RT,
                    "rel_DERT": rel_DERT,
                }
            )
        elif event_ == "rt" and type_ == "abs_rel":
            toappend.append({"abs_RT": abs_RT, "rel_RT": rel_RT})
        elif event_ == "dert" and type_ == "abs_rel":
            toappend.append({"abs_DERT": abs_DERT, "rel_DERT": rel_DERT})
        elif event_ == "rt_dert" and type_ == "abs":
            toappend.append({"abs_RT": abs_RT, "abs_DERT": abs_DERT})
        elif event_ == "rt" and type_ == "abs":
            toappend.append({"abs_RT": abs_RT})
        elif event_ == "dert" and type_ == "abs":
            toappend.append({"abs_DERT": abs_DERT})
        elif event_ == "rt_dert" and type_ == "rel":
            toappend.append({"rel_RT": rel_RT, "rel_DERT": rel_DERT})
        elif event_ == "rt" and type_ == "rel":
            toappend.append({"rel_RT": rel_RT})
        elif event_ == "dert" and type_ == "rel":
            toappend.append({"rel_DERT": rel_DERT})

    mus_thresholds = pd.DataFrame(toappend)

    """ 
    print(mus_thresholds)
           abs_RT    abs_DERT    rel_RT  rel_DERT
    0  220.990703  338.584589  4.058934  6.218780
    1  342.778042  383.379447  6.295801  7.041527
    2  233.166062  215.877558  4.282559  3.965021
    3  296.928492  304.142582  5.453683  5.586184
    4  409.113920  338.584589  7.514192  6.218780
    ...
    """

    return mus_thresholds


def compute_dr(
    emgfile,
    n_firings_RecDerec=4,
    n_firings_steady=10,
    start_steady=-1,
    end_steady=-1,
    event_="rec_derec_steady",
):
    """
    This function can calculate the discharge rate (DR) at recruitment, derecruitment and during the steady-state phase.

    Parameters
    ----------
    emgfile: dict
        The dictionary containing the emgfile.

    n_firings_RecDerec: int, default 4
        The number of firings at recruitment and derecruitment to consider for the calculation of the DR.
    
    n_firings_steady: int, default 10
        The number of firings to consider for the calculation of the DR at the start and at the end
        of the steady-state phase.
    
    start_steady, end_steady: int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and end of the steady-state phase.
    
    event_: str, default "rec_derec_steady"
        When to calculate the DR. Input parameters for event_ are:
            "rec_derec_steady" means that the DR is calculated at recruitment, derecruitment and during the steady-state phase.
            "rec" means that the DR is calculated at recruitment.
            "derec" means that the DR is calculated at derecruitment.
            "rec_derec" means that the DR is calculated at recruitment and derecruitment.
            "steady" means that the DR is calculated during the steady-state phase.
    
    DR for all the contraction is automatically calculated and returned.

    Returns
    -------
    mus_dr: pd.DataFrame
        A pd.DataFrame containing the requested DR.
    """

    # Check that all the inputs are correct
    errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
    assert event_ in [
        "rec",
        "derec",
        "rec_derec",
        "steady",
        "rec_derec_steady",
    ], errormessage
    if not isinstance(n_firings_RecDerec, int):
        raise Exception(
            f"n_firings_RecDerec must be an integer. {type(n_firings_RecDerec)} was passed instead."
        )
    if not isinstance(n_firings_steady, int):
        raise Exception(
            f"n_firings_steady must be an integer. {type(n_firings_steady)} was passed instead."
        )

    idr = compute_idr(emgfile=emgfile)

    # Check if we need to manually select the area for the steady-state phase
    if event_ == "rec_derec_steady" or event_ == "steady":
        if start_steady < 0 and end_steady < 0:
            start_steady, end_steady = showselect(
                emgfile, title="Select the start/end area to consider then press enter"
            )

    # Create an object to append the results
    toappend_dr = []
    for i in range(emgfile["NUMBER_OF_MUS"]):  # Loop all the MUs

        # DR rec
        selected_idr = idr[i]["idr"].iloc[0:n_firings_RecDerec]
        drrec = selected_idr.mean()

        # DR derec
        length = len(idr[i]["idr"])
        selected_idr = idr[i]["idr"].iloc[length - n_firings_RecDerec + 1 : length]  # +1 because len() counts position 0
        drderec = selected_idr.mean()

        # Find indexes of start and end steady
        for count, pulse in enumerate(idr[i]["mupulses"]):
            if pulse >= start_steady:
                index_startsteady = count
                break

        for count, pulse in enumerate(idr[i]["mupulses"]):
            if pulse >= end_steady:
                index_endsteady = count
                break

        # DR startsteady
        selected_idr = idr[i]["idr"].loc[index_startsteady + 1 : index_startsteady + n_firings_steady]  # +1 because to work only on the steady state
        drstartsteady = selected_idr.mean()

        # DR endsteady
        selected_idr = idr[i]["idr"].loc[index_endsteady + 1 - n_firings_steady : index_endsteady]  # +1 because to work only on the steady state
        drendsteady = selected_idr.mean()

        # DR steady
        selected_idr = idr[i]["idr"].loc[index_startsteady + 1 : index_endsteady]  # +1 because to work only on the steady state
        drsteady = selected_idr.mean()

        # DR all contraction
        selected_idr = idr[i]["idr"]
        drall = selected_idr.mean()

        if event_ == "rec":
            toappend_dr.append({"DR_rec": drrec, "DR_all": drall})
        elif event_ == "derec":
            toappend_dr.append({"DR_derec": drderec, "DR_all": drall})
        elif event_ == "rec_derec":
            toappend_dr.append({"DR_rec": drrec, "DR_derec": drderec, "DR_all": drall})
        elif event_ == "steady":
            toappend_dr.append(
                {
                    "DR_start_steady": drstartsteady,
                    "DR_end_steady": drendsteady,
                    "DR_all_steady": drsteady,
                    "DR_all": drall,
                }
            )
        elif event_ == "rec_derec_steady":
            toappend_dr.append(
                {
                    "DR_rec": drrec,
                    "DR_derec": drderec,
                    "DR_start_steady": drstartsteady,
                    "DR_end_steady": drendsteady,
                    "DR_all_steady": drsteady,
                    "DR_all": drall,
                }
            )

    # Convert the dictionary in a DataFrame
    mus_dr = pd.DataFrame(toappend_dr)

    """
    print(mus_dr)
         DR_rec  DR_derec  DR_start_steady  DR_end_steady  DR_all_steady    DR_all
    0  6.139581  4.751324         8.269338       6.467472       7.308025  7.225373
    1  5.212117  4.349304         5.619159       5.386972       5.742270  5.692758
    2  6.154896  4.505799         7.613770       7.381648       7.788328  7.685846
    3  5.019371  4.023208         6.660404       5.872341       6.465086  6.374818
    4  4.304906  4.503785         5.744684       6.078921       6.428322  6.352171
    ...
    """

    return mus_dr


def basic_mus_properties(
    emgfile,
    n_firings_RecDerec=4,
    n_firings_steady=10,
    start_steady=-1,
    end_steady=-1,
    mvif=0,
):
    """
    This function can calculate all the basic properties of the MUs of a trapezoidal contraction and, in particular:
    the absolute/relative recruitment/derecruitment thresholds,
    the discharge rate at recruitment, derecruitment, during the steady-state phase and the entire contraction,
    the coefficient of variation of interspike interval
    and the coefficient of variation of force signal.

    Parameters
    ----------
    emgfile: dict
        The dictionary containing the emgfile.

    n_firings_RecDerec: int, default 4
        The number of firings at recruitment and derecruitment to consider for the calculation of the DR.
    
    n_firings_steady: int, default 10
        The number of firings to consider for the calculation of the DR at the start and at the end
        of the steady-state phase.
    
    start_steady, end_steady: int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and end of the steady-state phase.
    
    mvif: float, default 0
        The maximum voluntary isometric force (MViF). It is suggest to report MViF in Newton (N).
        If 0 (default), the user will be asked to imput it manually.
        Otherwise, the passed value will be used.

    Returns
    -------
    mus_dr: pd.DataFrame
        A pd.DataFrame containing the results of the analysis.
    
    
    
    The first argument should be the emgfile.

    The number of firings used for the DR calculation at recruitment/derecruitment and at the start/end of the steady-state phase
    can be passed to n_firings_RecDerec and n_firings_steady.

    The user will need to select the start and end of the steady-state phase manually unless specified by
    start_steady and end_steady >= 0.

    If the MViF is not specified (by default mvif = 0) the user will be asked to imput it manually. If
    mvif is a number different from 0, this value is used instead.

    The function returns a DataFrame containing all the results.
    """

    # Check if we need to select the steady-state phase
    if start_steady < 0 and end_steady < 0:
        start_steady, end_steady = showselect(
            emgfile, title="Select the start/end area to consider then press enter"
        )

    # Collect the information to export
    #
    # First: create a dataframe that contains all the output
    exportable_df = []

    # Second: add basic information (MVC, MU number, PNR, Average PNR)
    if mvif == 0:
        # Ask the user to input MViF
        mvif = int(
            input("--------------------------------\nEnter MViF value in newton: ")
        )

    exportable_df.append({"MVC": mvif})
    exportable_df = pd.DataFrame(exportable_df)

    # Basically, we create an empty list, append values, convert the list in df and then concatenate to the exportable_df
    toappend = []
    for i in range(emgfile["NUMBER_OF_MUS"]):
        toappend.append({"MU_number": i + 1})
    toappend = pd.DataFrame(toappend)
    exportable_df = pd.concat([exportable_df, toappend], axis=1)

    # Only for DEMUSE files at this point (once we compute the PNR for the OTB decomposition, we can use it for both)
    if emgfile["SOURCE"] == "DEMUSE":
        # Repeat the task for every new column to fill and concatenate
        toappend = []
        for i in range(emgfile["NUMBER_OF_MUS"]):
            toappend.append({"PNR": emgfile["PNR"][0][i]})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

        # Repeat again...
        toappend = []
        toappend.append({"avg_PNR": np.average(emgfile["PNR"])})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)
    else:
        pass

    # Calculate RT and DERT
    mus_thresholds = compute_thresholds(emgfile=emgfile, mvif=mvif)
    exportable_df = pd.concat([exportable_df, mus_thresholds], axis=1)

    # Calculate DR at recruitment, derecruitment, all, start and end steady-state and all contraction
    mus_dr = compute_dr(
        emgfile=emgfile,
        n_firings_RecDerec=n_firings_RecDerec,
        n_firings_steady=n_firings_steady,
        start_steady=start_steady,
        end_steady=end_steady,
    )
    exportable_df = pd.concat([exportable_df, mus_dr], axis=1)

    # Calculate COVisi
    covisi = compute_covisi(
        emgfile=emgfile,
        n_firings_RecDerec=n_firings_RecDerec,
        start_steady=start_steady,
        end_steady=end_steady,
        event_="steady",
    )
    exportable_df = pd.concat([exportable_df, covisi], axis=1)

    # Calculate COVsteady
    covsteady = compute_covsteady(
        emgfile, start_steady=start_steady, end_steady=end_steady
    )
    covsteady = pd.DataFrame(covsteady, columns=["COV_steady"])
    exportable_df = pd.concat([exportable_df, covsteady], axis=1)

    """ 
    print(exportable_df)
        MVC  MU_number   PNR  avg_PNR      abs_RT    abs_DERT    rel_RT  rel_DERT    DR_rec  DR_derec  DR_start_steady  DR_end_steady  DR_all_steady    DR_all  COVisi_steady  COVisi_all  COV_steady
    0  333.0          1  33.7  32.0125  132.594422  203.150753  4.058934  6.218780  6.139581  4.751324         8.269338       6.507612       7.303444  7.225373      11.866565   15.450206    4.412715     
    1    NaN          2  36.9      NaN  205.666825  230.027668  6.295801  7.041527  5.212117  4.349304         5.619159       5.302997       5.739165  5.692758      12.424448   13.071500         NaN     
    2    NaN          3  29.5      NaN  139.899637  129.526535  4.282559  3.965021  6.154896  4.505799         7.613770       7.503886       7.789876  7.685846      10.322716   14.749926         NaN     
    3    NaN          4  36.7      NaN  178.157095  182.485549  5.453683  5.586184  5.019371  4.023208         6.660404       5.960320       6.464689  6.374818      11.358656   14.974260         NaN     
    4    NaN          5  28.8      NaN  245.468352  203.150753  7.514192  6.218780  4.304906  4.503785         5.744684       6.075250       6.426378  6.352171      13.747331   14.902565         NaN
    ...
    """

    return exportable_df


def compute_covisi(
    emgfile,
    n_firings_RecDerec=4,
    start_steady=-1,
    end_steady=-1,
    event_="rec_derec_steady",
    single_mu_number=-1,
):
    """
    This function can calculate the coefficient of variation of interspike interval (COVisi) at recruitment,
    derecruitment, during the steady-state phase and during all the contraction.

    Parameters
    ----------
    emgfile: dict
        The dictionary containing the emgfile.

    n_firings_RecDerec: int, default 4
        The number of firings at recruitment and derecruitment to consider for the calculation of the COVisi.
    
    start_steady, end_steady: int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and end of the steady-state phase.
    
    event_: str, default "rec_derec_steady"
        When to calculate the COVisi. Input parameters for event_ are:
            "rec_derec_steady" means that the covisi is calculated at recruitment, derecruitment and during the steady-state phase.
            "rec" means that the covisi is calculated at recruitment.
            "derec" means that the covisi is calculated at derecruitment.
            "rec_derec" means that the covisi is calculated at recruitment and derecruitment.
            "steady" means that the covisi is calculated during the steady-state phase.
    
    single_mu_number: int, default -1
        Number of the specific MU to compute the COVisi.
        If single_mu_number >= 0, only the COVisi of the entire contraction will be returned.
        If -1 (default), COVisi will be calculated for all the MUs.
        
    COVisi for all the contraction is automatically calculated and returned.
    
    Returns
    -------
    covisi: pd.DataFrame
        A pd.DataFrame containing the requested COVisi.
    """

    # Check that all the inputs are correct
    errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
    assert event_ in [
        "rec",
        "derec",
        "rec_derec",
        "steady",
        "rec_derec_steady",
    ], errormessage
    if not isinstance(n_firings_RecDerec, int):
        raise Exception(
            f"n_firings_RecDerec must be an integer. {type(n_firings_RecDerec)} was passed instead."
        )

    idr = compute_idr(emgfile=emgfile)  # We use the idr to calculate the COVisi

    # Check if we need to analyse all the MUs or a single MU
    if single_mu_number < 0:
        # Check if we need to manually select the area for the steady-state phase
        if event_ == "rec_derec_steady" or event_ == "steady":
            if start_steady < 0 and end_steady < 0:
                start_steady, end_steady = showselect(
                    emgfile,
                    title="Select the start/end area to consider then press enter",
                )

        # Create an object to append the results
        toappend_covisi = []
        for i in range(emgfile["NUMBER_OF_MUS"]):  # Loop all the MUs

            # COVisi rec
            selected_idr = idr[i]["diff_mupulses"].iloc[0:n_firings_RecDerec]
            covisirec = (selected_idr.std() / selected_idr.mean()) * 100

            # COVisi derec
            length = len(idr[i]["diff_mupulses"])
            selected_idr = idr[i]["diff_mupulses"].iloc[
                length - n_firings_RecDerec + 1 : length
            ]  # +1 because len() counts position 0
            covisiderec = (selected_idr.std() / selected_idr.mean()) * 100

            # COVisi all steady
            if (event_ == "rec_derec_steady" or event_ == "steady"):  # Check if we need the steady-state phase
                idr_indexed = idr[i].set_index("mupulses")
                selected_idr = idr_indexed["diff_mupulses"].loc[start_steady:end_steady]
                covisisteady = (selected_idr.std() / selected_idr.mean()) * 100

            # COVisi all contraction
            selected_idr = idr[i]["diff_mupulses"]
            covisiall = (selected_idr.std() / selected_idr.mean()) * 100

            if event_ == "rec":
                toappend_covisi.append(
                    {"COVisi_rec": covisirec, "COVisi_all": covisiall}
                )
            elif event_ == "derec":
                toappend_covisi.append(
                    {"COVisi_derec": covisiderec, "COVisi_all": covisiall}
                )
            elif event_ == "rec_derec":
                toappend_covisi.append(
                    {
                        "COVisi_rec": covisirec,
                        "COVisi_derec": covisiderec,
                        "COVisi_all": covisiall,
                    }
                )
            elif event_ == "steady":
                toappend_covisi.append(
                    {"COVisi_steady": covisisteady, "COVisi_all": covisiall}
                )
            elif event_ == "rec_derec_steady":
                toappend_covisi.append(
                    {
                        "COVisi_rec": covisirec,
                        "COVisi_derec": covisiderec,
                        "COVisi_steady": covisisteady,
                        "COVisi_all": covisiall,
                    }
                )

        # Convert the dictionary in a DataFrame
        covisi = pd.DataFrame(toappend_covisi)

    else:
        # COVisi all contraction
        selected_idr = idr[single_mu_number]["diff_mupulses"]
        covisiall = (selected_idr.std() / selected_idr.mean()) * 100
        # Create an object to append the results
        toappend_covisi = []
        toappend_covisi.append({"COVisi_all": covisiall})
        # Convert the dictionary in a DataFrame
        covisi = pd.DataFrame(toappend_covisi)

    return covisi


def compute_drvariability(
    emgfile,
    n_firings_RecDerec=4,
    start_steady=-1,
    end_steady=-1,
    event_="rec_derec_steady",
):
    """
    This function can calculate the variability of the instantaneous discharge rate (DR) at recruitment,
    derecruitment, during the steady-state phase and during all the contraction.

    Parameters
    ----------
    emgfile: dict
        The dictionary containing the emgfile.

    n_firings_RecDerec: int, default 4
        The number of firings at recruitment and derecruitment to consider for the calculation of the DR variability.
    
    start_steady, end_steady: int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and end of the steady-state phase.
    
    event_: str, default "rec_derec_steady"
        When to calculate the COVisi. Input parameters for event_ are:
            "rec_derec_steady" means that the DR variability is calculated at recruitment, derecruitment and during the steady-state phase.
            "rec" means that the DR variability is calculated at recruitment.
            "derec" means that the DR variability is calculated at derecruitment.
            "rec_derec" means that the DR variability is calculated at recruitment and derecruitment.
            "steady" means that the DR variability is calculated during the steady-state phase.
    
    DR variability for all the contraction is automatically calculated and returned.
    
    Returns
    -------
    drvariability: pd.DataFrame
        A pd.DataFrame containing the requested DR variability.
    """

    # Check that all the inputs are correct
    errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
    assert event_ in [
        "rec",
        "derec",
        "rec_derec",
        "steady",
        "rec_derec_steady",
    ], errormessage
    if not isinstance(n_firings_RecDerec, int):
        raise Exception(
            f"n_firings_RecDerec must be an integer. {type(n_firings_RecDerec)} was passed instead."
        )

    idr = compute_idr(emgfile=emgfile)  # We use the idr to calculate the COVisi

    # Check if we need to manually select the area for the steady-state phase
    if event_ == "rec_derec_steady" or event_ == "steady":
        if start_steady < 0 and end_steady < 0:
            start_steady, end_steady = showselect(
                emgfile, title="Select the start/end area to consider then press enter"
            )

    # Create an object to append the results
    toappend_drvariability = []
    for i in range(emgfile["NUMBER_OF_MUS"]):  # Loop all the MUs

        # COVisi rec
        selected_idr = idr[i]["idr"].iloc[0:n_firings_RecDerec]
        drvariabilityrec = (selected_idr.std() / selected_idr.mean()) * 100

        # COVisi derec
        length = len(idr[i]["idr"])
        selected_idr = idr[i]["idr"].iloc[
            length - n_firings_RecDerec + 1 : length
        ]  # +1 because len() counts position 0
        drvariabilityderec = (selected_idr.std() / selected_idr.mean()) * 100

        # COVisi all steady
        if (event_ == "rec_derec_steady" or event_ == "steady"):  # Check if we need the steady-state phase
            idr_indexed = idr[i].set_index("mupulses")
            selected_idr = idr_indexed["idr"].loc[start_steady:end_steady]
            drvariabilitysteady = (selected_idr.std() / selected_idr.mean()) * 100

        # COVisi all contraction
        selected_idr = idr[i]["idr"]
        drvariabilityall = (selected_idr.std() / selected_idr.mean()) * 100

        if event_ == "rec":
            toappend_drvariability.append(
                {"DRvar_rec": drvariabilityrec, "DRvar_all": drvariabilityall}
            )
        elif event_ == "derec":
            toappend_drvariability.append(
                {"DRvar_derec": drvariabilityderec, "DRvar_all": drvariabilityall}
            )
        elif event_ == "rec_derec":
            toappend_drvariability.append(
                {
                    "DRvar_rec": drvariabilityrec,
                    "DRvar_derec": drvariabilityderec,
                    "DRvar_all": drvariabilityall,
                }
            )
        elif event_ == "steady":
            toappend_drvariability.append(
                {"DRvar_steady": drvariabilitysteady, "DRvar_all": drvariabilityall}
            )
        elif event_ == "rec_derec_steady":
            toappend_drvariability.append(
                {
                    "DRvar_rec": drvariabilityrec,
                    "DRvar_derec": drvariabilityderec,
                    "DRvar_steady": drvariabilitysteady,
                    "DRvar_all": drvariabilityall,
                }
            )

    # Convert the dictionary in a DataFrame
    drvariability = pd.DataFrame(toappend_drvariability)

    return drvariability
