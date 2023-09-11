"""
This module contains all the functions used to analyse the MUs properties when
not involving the MUs action potential shape.
"""

import pandas as pd
import numpy as np
from openhdemg.library.tools import showselect, compute_idr, compute_covsteady
from openhdemg.library.mathtools import compute_pnr, compute_sil
import warnings
import math


def compute_thresholds(emgfile, event_="rt_dert", type_="abs_rel", mvc=0):
    """
    Calculates recruitment/derecruitment thresholds.

    Values are calculated both in absolute and relative terms.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    event_ : str {"rt_dert", "rt", "dert"}, default "rt_dert"
        When to calculate the thresholds.

        ``rt_dert``
            Both recruitment and derecruitment tresholds will be calculated.
        ``rt``
            Only recruitment tresholds will be calculated.
        ``dert``
            Only derecruitment tresholds will be calculated.
    type_ : str {"abs_rel", "rel", "abs"}, default "abs_rel"
        The tipe of value to calculate.

        ``abs_rel``
            Both absolute and relative tresholds will be calculated.
        ``rel``
            Only relative tresholds will be calculated.
        ``abs``
            Only absolute tresholds will be calculated.
    mvc : float, default 0
        The maximum voluntary contraction (MVC).
        if mvc is 0, the user is asked to input MVC; otherwise, the value
        passed is used.

    Returns
    -------
    mus_thresholds : pd.DataFrame
        A DataFrame containing the requested thresholds.

    See also
    --------
    - compute_dr : calculate the discharge rate.
    - basic_mus_properties : calculate basic MUs properties on a trapezoidal
        contraction.
    - compute_covisi : calculate the coefficient of variation of interspike
        interval.
    - compute_drvariability : calculate the DR variability.

    Examples
    --------
    Load the EMG file and compute the thresholds.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> mus_thresholds = emg.compute_thresholds(
    ...     emgfile=emgfile,
    ...     event_="rt_dert",
    ... )
    >>> mus_thresholds
           abs_RT    abs_DERT     rel_RT   rel_DERT
    0  160.148294  137.682351  18.665302  16.046894
    1   39.138554   49.860936   4.561603   5.811298
    2   88.155160   95.133218  10.274494  11.087788
    3   37.776982   41.010716   4.402912   4.779804

    Type of output can be adjusted, e.g., to have only absolute values at
    recruitment.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> mus_thresholds = emg.compute_thresholds(
    ...     emgfile=emgfile,
    ...     event_="rt",
    ...     type_="abs",
    ... )
    >>> mus_thresholds
           abs_RT
    0  160.148294
    1   39.138554
    2   88.155160
    3   37.776982
    """

    # Extract the variables of interest from the EMG file
    NUMBER_OF_MUS = emgfile["NUMBER_OF_MUS"]
    MUPULSES = emgfile["MUPULSES"]
    REF_SIGNAL = emgfile["REF_SIGNAL"]

    # Check that all the inputs are correct
    if event_ not in ["rt_dert", "rt", "dert"]:
        raise ValueError(
            f"event_ must be one of : 'rt_dert', 'rt', 'dert'. {event_} was passed instead."
        )

    if type_ not in ["abs_rel", "rel", "abs"]:
        raise ValueError(
            f"event_ must be one of : 'abs_rel', 'rel', 'abs'. {event_} was passed instead."
        )

    if not isinstance(mvc, (float, int)):
        raise TypeError(
            f"mvc must be one of the following types: float, int. {type(mvc)} was passed instead."
        )

    if type_ != "rel" and mvc == 0:
        # Ask the user to input MVC
        mvc = float(
            input("--------------------------------\nEnter MVC value in newton: ")
        )

    # Create an object to append the results
    toappend = []
    # Loop all the MUs
    for mu in range(NUMBER_OF_MUS):
        # Manage the exception of empty MUs
        if len(MUPULSES[mu]) > 0:
            # Detect the first and last firing of the MU and
            mup_rec = MUPULSES[mu][0]
            mup_derec = MUPULSES[mu][-1]
            # Calculate absolute and relative RT and DERT if requested
            abs_RT = ((float(REF_SIGNAL.at[mup_rec, 0]) * mvc) / 100)
            abs_DERT = ((float(REF_SIGNAL.at[mup_derec, 0]) * mvc) / 100)
            rel_RT = float(REF_SIGNAL.at[mup_rec, 0])
            rel_DERT = float(REF_SIGNAL.at[mup_derec, 0])

        else:
            abs_RT = np.nan
            abs_DERT = np.nan
            rel_RT = np.nan
            rel_DERT = np.nan

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
    Calculate the discharge rate (DR).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    n_firings_RecDerec : int, default 4
        The number of firings at recruitment and derecruitment to consider for
        the calculation of the DR.
    n_firings_steady : int, default 10
        The number of firings to consider for the calculation of the DR at the
        start and at the end
        of the steady-state phase.
    start_steady, end_steady : int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and
        end of the steady-state phase.
    event_ : str {"rec_derec_steady", "rec", "derec", "rec_derec", "steady"}, default "rec_derec_steady"
        When to calculate the DR.

            ``rec_derec_steady``
                DR is calculated at recruitment, derecruitment and during the
                steady-state phase.
            ``rec``
                DR is calculated at recruitment.
            ``derec``
                DR is calculated at derecruitment.
            ``rec_derec``
                DR is calculated at recruitment and derecruitment.
            ``steady``
                DR is calculated during the steady-state phase.

    Returns
    -------
    mus_dr : pd.DataFrame
        A pd.DataFrame containing the requested DR.

    Warns
    -----
    warning
        When calculation of DR at rec/derec fails due to not enough firings.

    See also
    --------
    - compute_thresholds : calculates recruitment/derecruitment thresholds.
    - basic_mus_properties : calculate basic MUs properties on a trapezoidal
        contraction.
    - compute_covisi : calculate the coefficient of variation of interspike
        interval.
    - compute_drvariability : calculate the DR variability.

    Notes
    -----
    DR for all the contraction is automatically calculated and returned.

    Examples
    --------
    Load the EMG file and compute the DR.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> mus_dr = emg.compute_dr(emgfile=emgfile)
    >>> mus_dr
         DR_rec  DR_derec  DR_start_steady  DR_end_steady  DR_all_steady     DR_all
    0  5.701081  4.662196         7.321255       6.420720       6.907559   6.814342
    1  7.051127  6.752467        14.919066      10.245462      11.938671  11.683134
    2  6.101529  4.789000         7.948740       6.133345       7.695189   8.055731
    3  6.345692  5.333535        11.121785       9.265212      11.544140  11.109796

    Type of output can be adjusted, e.g., to have only the DR at recruitment.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> mus_dr = emg.compute_dr(emgfile=emgfile, event_="rec")
    >>> mus_dr
         DR_rec     DR_all
    0  5.701081   6.814342
    1  7.051127  11.683134
    2  6.101529   8.055731
    3  6.345692  11.109796

    The manual selection of the steady state phase can be bypassed
    if previously calculated with an automated method.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> mus_dr = emg.compute_dr(
    ...     emgfile=emgfile,
    ...     start_steady=20000,
    ...     end_steady=50000,
    ...     event_="steady",
    ... )
    >>> mus_dr
       DR_start_steady  DR_end_steady  DR_all_steady     DR_all
    0         7.476697       6.271750       6.794170   6.814342
    1        14.440561      10.019572      11.822081  11.683134
    2         7.293547       5.846093       7.589531   8.055731
    3        13.289651       9.694317      11.613640  11.109796
    """

    # Check that all the inputs are correct
    errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
    if event_ not in [
        "rec",
        "derec",
        "rec_derec",
        "steady",
        "rec_derec_steady",
    ]:
        raise ValueError(errormessage)

    if not isinstance(n_firings_RecDerec, int):
        raise TypeError(
            f"n_firings_RecDerec must be an integer. {type(n_firings_RecDerec)} was passed instead."
        )
    if not isinstance(n_firings_steady, int):
        raise TypeError(
            f"n_firings_steady must be an integer. {type(n_firings_steady)} was passed instead."
        )

    idr = compute_idr(emgfile=emgfile)

    # Check if we need to manually select the area for the steady-state phase
    if event_ == "rec_derec_steady" or event_ == "steady":
        if (start_steady < 0 and end_steady < 0) or (start_steady < 0 or end_steady < 0):
            points = showselect(
                emgfile,
                title="Select the start/end area of the steady-state by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
                titlesize=10,
            )
            start_steady, end_steady = points[0], points[1]

    # Create an object to append the results
    toappend_dr = []
    for mu in range(emgfile["NUMBER_OF_MUS"]):  # Loop all the MUs
        # DR rec/derec
        if len(idr[mu]["idr"]) >= n_firings_RecDerec:
            selected_idr = idr[mu]["idr"].iloc[0:n_firings_RecDerec]
            drrec = selected_idr.mean()

            length = len(idr[mu]["idr"])
            selected_idr = idr[mu]["idr"].iloc[
                length - n_firings_RecDerec + 1: length
            ]
            # +1 because len() counts position 0
            drderec = selected_idr.mean()

        else:
            drrec = np.nan
            drderec = np.nan

            warnings.warn(
                "Calculation of DR at rec/derec failed, not enough firings"
            )

        # Set indexes for the steady-state firings
        index_startsteady = np.nan
        index_endsteady = np.nan

        # Find nex indexes of start and end steady if possible
        for pos, pulse in enumerate(idr[mu]["mupulses"]):
            if pulse >= start_steady and pulse <= end_steady:
                index_startsteady = pos
                break

        if not math.isnan(index_startsteady):
            for pos, pulse in enumerate(idr[mu]["mupulses"]):
                if pulse >= end_steady:
                    index_endsteady = pos
                    break

                else:
                    # Account for MUs that stop firing before the end of the
                    # steady-state phase
                    index_endsteady = pos

        # Calculate DR at the steady-state phase if there is a steady-state
        c1 = math.isnan(index_startsteady)
        c2 = math.isnan(index_endsteady)

        if not c1 and not c2:
            # # DR drstartsteady
            # Use +1 because to work only on the steady state (here and after)
            # because the idr is calculated on the previous firing (on the
            # ramp).
            selected_idr = idr[mu]["idr"].loc[
                index_startsteady + 1: index_startsteady + n_firings_steady
            ]
            drstartsteady = selected_idr.mean()

            # DR endsteady
            selected_idr = idr[mu]["idr"].loc[
                index_endsteady + 1 - n_firings_steady: index_endsteady
            ]
            drendsteady = selected_idr.mean()

            # DR steady
            selected_idr = idr[mu]["idr"].loc[
                index_startsteady + 1: index_endsteady
            ]
            drsteady = selected_idr.mean()

        else:
            drstartsteady = np.nan
            drendsteady = np.nan
            drsteady = np.nan

        # DR all contraction
        selected_idr = idr[mu]["idr"]
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

    return mus_dr


def basic_mus_properties(
    emgfile,
    n_firings_RecDerec=4,
    n_firings_steady=10,
    start_steady=-1,
    end_steady=-1,
    accuracy="default",
    mvc=0,
):
    """
    Calculate basic MUs properties on a trapezoidal contraction.

    The function is meant to be used on trapezoidal contractions and
    calculates:
    the absolute/relative recruitment/derecruitment thresholds,
    the discharge rate at recruitment, derecruitment, during the steady-state
    phase and during the entire contraction,
    the coefficient of variation of interspike interval,
    the coefficient of variation of force signal.

    Accuracy measures, MVC and steadiness are also returned.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    n_firings_RecDerec : int, default 4
        The number of firings at recruitment and derecruitment to consider for
        the calculation of the DR.
    n_firings_steady : int, default 10
        The number of firings to consider for the calculation of the DR at the
        start and at the end of the steady-state phase.
    start_steady, end_steady : int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and
        end of the steady-state phase.
    accuracy : str {"default", "SIL", "PNR", "SIL_PNR"}, default "default"
        The accuracy measure to return.

        ``default``
            The original accuracy measure already contained in the emgfile is
            returned without any computation.
        ``SIL``
            The Silhouette score is computed.
        ``PNR``
            The pulse to noise ratio is computed.
        ``SIL_PNR``
            Both the Silhouette score and the pulse to noise ratio are
            computed.
    mvc : float, default 0
        The maximum voluntary contraction (MVC). It is suggest to report
        MVC in Newton (N). If 0 (default), the user will be asked to imput it
        manually. Otherwise, the passed value will be used.

    Returns
    -------
    exportable_df : pd.DataFrame
        A pd.DataFrame containing the results of the analysis.

    See also
    --------
    - compute_thresholds : calculates recruitment/derecruitment thresholds.
    - compute_dr : calculate the discharge rate.
    - compute_covisi : calculate the coefficient of variation of interspike
        interval.
    - compute_drvariability : calculate the DR variability.

    Examples
    --------
    Get full summary of all the MUs properties.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> df = emg.basic_mus_properties(emgfile=emgfile)
    >>> df
         MVC  MU_number      abs_RT    abs_DERT     rel_RT   rel_DERT    DR_rec  DR_derec  DR_start_steady  DR_end_steady  DR_all_steady     DR_all  COVisi_steady  COVisi_all  COV_steady
    0  786.0          1  146.709276  126.128587  18.665302  16.046894  5.701081  4.662196         7.467810       6.242360       6.902616   6.814342      11.296316   16.309681    1.423286
    1    NaN          2   35.854200   45.676801   4.561603   5.811298  7.051127  6.752467        11.798908       9.977337      11.784061  11.683134      15.871254   21.233615         NaN
    2    NaN          3   80.757524   87.150011  10.274494  11.087788  6.101529  4.789000         7.940926       5.846093       7.671361   8.055731      35.755090   35.308650         NaN
    3    NaN          4   34.606886   37.569257   4.402912   4.779804  6.345692  5.333535        11.484875       9.636914      11.594712  11.109796      24.611246   29.372524         NaN

    We can bypass manual prompting the MVC by pre-specifying it and/or
    bypass the manual selection of the steady state phase if previously
    calculated with an automated method.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> df = emg.basic_mus_properties(
    ...     emgfile=emgfile,
    ...     start_steady=20000,
    ...     end_steady=50000,
    ...     mvc=786,
    ... )
    >>> df
         MVC  MU_number      abs_RT    abs_DERT     rel_RT   rel_DERT    DR_rec  DR_derec  DR_start_steady  DR_end_steady  DR_all_steady     DR_all  COVisi_steady  COVisi_all  COV_steady
    0  786.0          1  146.709276  126.128587  18.665302  16.046894  5.701081  4.662196         7.476697       6.271750       6.794170   6.814342      11.066966   16.309681    1.431752
    1    NaN          2   35.854200   45.676801   4.561603   5.811298  7.051127  6.752467        14.440561      10.019572      11.822081  11.683134      15.076819   21.233615         NaN
    2    NaN          3   80.757524   87.150011  10.274494  11.087788  6.101529  4.789000         7.293547       5.846093       7.589531   8.055731      36.996894   35.308650         NaN
    3    NaN          4   34.606886   37.569257   4.402912   4.779804  6.345692  5.333535        13.289651       9.694317      11.613640  11.109796      26.028689   29.372524         NaN
    """
    # TODO make new examples, also with accuracy

    # Check if we need to select the steady-state phase
    if (start_steady < 0 and end_steady < 0) or (start_steady < 0 or end_steady < 0):
        points = showselect(
            emgfile,
            title="Select the start/end area of the steady-state by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
            titlesize=10,
        )
        start_steady, end_steady = points[0], points[1]

    # Collect the information to export
    # First: create a dataframe that contains all the output
    exportable_df = []

    # Second: add basic information (MVC, MU number, ACCURACY, Average ACCURACY)
    if mvc == 0:
        # Ask the user to input MVC
        mvc = float(
            input(
                "--------------------------------\nEnter MVC value in newton: "
            )
        )

    exportable_df.append({"MVC": mvc})
    exportable_df = pd.DataFrame(exportable_df)

    # Basically, we create an empty list, append values, convert the
    # list in a pd.DataFrame and then concatenate to the exportable_df
    toappend = []
    for i in range(emgfile["NUMBER_OF_MUS"]):
        toappend.append({"MU_number": i})
    toappend = pd.DataFrame(toappend)
    exportable_df = pd.concat([exportable_df, toappend], axis=1)

    if accuracy == "default":
        # Report the original accuracy
        toappend = emgfile["ACCURACY"]
        toappend.columns = ["Accuracy"]
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

        # Calculate avrage accuracy
        avg_accuracy = exportable_df["Accuracy"].mean()
        toappend = pd.DataFrame([{"avg_Accuracy": avg_accuracy}])
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

    elif accuracy == "SIL":
        # Calculate SIL
        toappend = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            sil = compute_sil(
                ipts=emgfile["IPTS"][mu],
                mupulses=emgfile["MUPULSES"][mu],
            )
            toappend.append({"SIL": sil})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

        # Calculate avrage SIL
        avg_sil = exportable_df["SIL"].mean()
        toappend = pd.DataFrame([{"avg_SIL": avg_sil}])
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

    elif accuracy == "PNR":
        # Calculate PNR
        # Repeat the task for every new column to fill and concatenate
        toappend = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            pnr = compute_pnr(
                ipts=emgfile["IPTS"][mu],
                mupulses=emgfile["MUPULSES"][mu],
                fsamp=emgfile["FSAMP"],
            )
            toappend.append({"PNR": pnr})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

        # Calculate avrage PNR
        # dropna to avoid nan average.
        avg_pnr = exportable_df["PNR"].mean()
        toappend = pd.DataFrame([{"avg_PNR": avg_pnr}])
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

    elif accuracy == "SIL_PNR":
        # Calculate SIL
        toappend = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            sil = compute_sil(
                ipts=emgfile["IPTS"][mu],
                mupulses=emgfile["MUPULSES"][mu],
            )
            toappend.append({"SIL": sil})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

        # Calculate avrage SIL
        avg_sil = exportable_df["SIL"].mean()
        toappend = pd.DataFrame([{"avg_SIL": avg_sil}])
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

        # Calculate PNR
        # Repeat the task for every new column to fill and concatenate
        toappend = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):
            pnr = compute_pnr(
                ipts=emgfile["IPTS"][mu],
                mupulses=emgfile["MUPULSES"][mu],
                fsamp=emgfile["FSAMP"],
            )
            toappend.append({"PNR": pnr})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

        # Calculate avrage PNR
        # dropna to avoid nan average.
        avg_pnr = exportable_df["PNR"].mean()
        toappend = pd.DataFrame([{"avg_PNR": avg_pnr}])
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

    else:
        raise ValueError(
            f"accuracy must be one of 'default', 'SIL', 'PNR', 'SIL_PNR'. {accuracy} was passed instead"
        )

    # Calculate RT and DERT
    mus_thresholds = compute_thresholds(emgfile=emgfile, mvc=mvc)
    exportable_df = pd.concat([exportable_df, mus_thresholds], axis=1)

    # Calculate DR at recruitment, derecruitment, all, start, end of the
    # steady-state and on all the contraction.
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
        emgfile=emgfile,
        start_steady=start_steady,
        end_steady=end_steady,
    )
    covsteady = pd.DataFrame([{"COV_steady": covsteady}])
    exportable_df = pd.concat([exportable_df, covsteady], axis=1)

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
    Calculate the COVisi.

    This function calculates the coefficient of variation of interspike
    interval (COVisi).

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    n_firings_RecDerec : int, default 4
        The number of firings at recruitment and derecruitment to consider for
        the calculation of the COVisi.
    start_steady, end_steady : int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and
        end of the steady-state phase.
    event_ : str {"rec_derec_steady", "rec", "derec", "rec_derec", "steady"}, default "rec_derec_steady"
        When to calculate the COVisi.

            ``rec_derec_steady``
                covisi is calculated at recruitment, derecruitment and during
                the steady-state phase.
            ``rec``
                covisi is calculated at recruitment.
            ``derec``
                covisi is calculated at derecruitment.
            ``rec_derec``
                covisi is calculated at recruitment and derecruitment.
            ``steady``
                covisi is calculated during the steady-state phase.
    single_mu_number : int, default -1
        Number of the specific MU to compute the COVisi.
        If single_mu_number >= 0, only the COVisi of the entire contraction
        will be returned. If -1 (default), COVisi will be calculated for all
        the MUs.

    Returns
    -------
    covisi : pd.DataFrame
        A pd.DataFrame containing the requested COVisi.

    See also
    --------
    - compute_thresholds : calculates recruitment/derecruitment thresholds.
    - compute_dr : calculate the discharge rate.
    - basic_mus_properties : calculate basic MUs properties on a trapezoidal
        contraction.
    - compute_drvariability : calculate the DR variability.

    Notes
    -----
    COVisi for all the contraction is automatically calculated and returned.

    Examples
    --------
    Compute covisi during the various parts of the trapezoidal contraction.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> df = emg.compute_covisi(emgfile=emgfile)
    >>> df
       COVisi_rec  COVisi_derec  COVisi_steady  COVisi_all
    0    8.600651     24.007405      11.230602   16.309681
    1   46.874208     19.243432      16.657603   21.233615
    2   32.212757     18.642514      35.421124   35.308650
    3   62.995864     13.080768      24.966372   29.372524

    If the steady-state phase has been pre-identified, the manual selection
    of the area can be bypassed.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> df = emg.compute_covisi(
    ...     emgfile=emgfile,
    ...     event_="rec_derec",
    ...     start_steady=20000,
    ...     end_steady=50000,
    ... )
    >>> df
       COVisi_rec  COVisi_derec  COVisi_all
    0    8.600651     24.007405   16.309681
    1   46.874208     19.243432   21.233615
    2   32.212757     18.642514   35.308650
    3   62.995864     13.080768   29.372524

    To access the covisi of the entire contraction of a single MU.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> df = emg.compute_covisi(emgfile=emgfile, single_mu_number=2)
    >>> df
       COVisi_all
    0    35.30865
    """

    # Check that all the inputs are correct
    errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
    if event_ not in [
        "rec",
        "derec",
        "rec_derec",
        "steady",
        "rec_derec_steady",
    ]:
        raise ValueError(errormessage)

    if not isinstance(n_firings_RecDerec, int):
        raise TypeError(
            f"n_firings_RecDerec must be an integer. {type(n_firings_RecDerec)} was passed instead."
        )

    # We use the idr pd.DataFrame to calculate the COVisi
    idr = compute_idr(emgfile=emgfile)

    # Check if we need to analyse all the MUs or a single MU
    if single_mu_number < 0:
        # Check if we need to manually select the area for the steady-state
        # phase.
        if event_ == "rec_derec_steady" or event_ == "steady":
            if (start_steady < 0 and end_steady < 0) or (start_steady < 0 or end_steady < 0):
                points = showselect(
                    emgfile,
                    title="Select the start/end area of the steady-state by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
                    titlesize=10,
                )
                start_steady, end_steady = points[0], points[1]

        # Create an object to append the results
        toappend_covisi = []
        for mu in range(emgfile["NUMBER_OF_MUS"]):  # Loop all the MUs

            # COVisi rec
            selected_idr = idr[mu]["diff_mupulses"].iloc[0: n_firings_RecDerec]
            covisirec = (selected_idr.std() / selected_idr.mean()) * 100

            # COVisi derec
            length = len(idr[mu]["diff_mupulses"])
            selected_idr = idr[mu]["diff_mupulses"].iloc[
                length - n_firings_RecDerec + 1: length
            ]  # +1 because len() counts position 0
            covisiderec = (selected_idr.std() / selected_idr.mean()) * 100

            # COVisi all steady
            if (event_ == "rec_derec_steady" or event_ == "steady"):
                idr_indexed = idr[mu].set_index("mupulses")
                selected_idr = idr_indexed["diff_mupulses"].loc[
                    start_steady: end_steady
                ]
                covisisteady = (selected_idr.std() / selected_idr.mean()) * 100

            # COVisi all contraction
            selected_idr = idr[mu]["diff_mupulses"]
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
    Calculate the DR variability.

    This function calculates the variability (as the coefficient of variation)
    of the instantaneous discharge rate (DR) at recruitment, derecruitment,
    during the steady-state phase and during all the contraction.

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    n_firings_RecDerec : int, default 4
        The number of firings at recruitment and derecruitment to consider for
        the calculation of the DR variability.
    start_steady, end_steady : int, default -1
        The start and end point (in samples) of the steady-state phase.
        If < 0 (default), the user will need to manually select the start and
        end of the steady-state phase.
    event_ : str {"rec_derec_steady", "rec", "derec", "rec_derec", "steady"}, default "rec_derec_steady"
        When to calculate the DR variability.

            ``rec_derec_steady``
                DR variability is calculated at recruitment, derecruitment and
                during the steady-state phase.
            ``rec``
                DR variability is calculated at recruitment.
            ``derec``
                DR variability is calculated at derecruitment.
            ``rec_derec``
                DR variability is calculated at recruitment and derecruitment.
            ``steady``
                DR variability is calculated during the steady-state phase.

    Returns
    -------
    drvariability : pd.DataFrame
        A pd.DataFrame containing the requested DR variability.

    See also
    --------
    - compute_thresholds : calculates recruitment/derecruitment thresholds.
    - compute_dr : calculate the discharge rate.
    - basic_mus_properties : calculate basic MUs properties on a trapezoidal
        contraction.
    - compute_covisi : calculate the coefficient of variation of interspike
        interval.

    Notes
    -----
    DR variability for all the contraction is automatically calculated and
    returned.

    Examples
    --------
    Compute covisi during the various parts of the trapezoidal contraction.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> df = emg.compute_covisi(emgfile=emgfile)
    >>> df
       DRvar_rec  DRvar_derec  DRvar_steady  DRvar_all
    0   8.560971    21.662783     11.051780  13.937779
    1  36.934213    17.714761     55.968609  52.726356
    2  28.943139    17.263000     49.375100  54.420703
    3  48.322396    12.873456     54.718482  48.019809

    If the steady-state phase has been pre-identified, the manual selection
    of the area can be bypassed.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.askopenfile(filesource="OTB", otb_ext_factor=8)
    >>> df = emg.compute_covisi(
    ...     emgfile=emgfile,
    ...     event_="rec_derec",
    ...     start_steady=20000,
    ...     end_steady=50000,
    ... )
    >>> df
       DRvar_rec  DRvar_derec  DRvar_all
    0   8.560971    21.662783  13.937779
    1  36.934213    17.714761  52.726356
    2  28.943139    17.263000  54.420703
    3  48.322396    12.873456  48.019809
    """

    # Check that all the inputs are correct
    errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
    if event_ not in [
        "rec",
        "derec",
        "rec_derec",
        "steady",
        "rec_derec_steady",
    ]:
        raise ValueError(errormessage)

    if not isinstance(n_firings_RecDerec, int):
        raise type(
            f"n_firings_RecDerec must be an integer. {type(n_firings_RecDerec)} was passed instead."
        )

    # We use the idr pd.DataFrame to calculate the COVisi
    idr = compute_idr(emgfile=emgfile)

    # Check if we need to manually select the area for the steady-state phase
    if event_ == "rec_derec_steady" or event_ == "steady":
        if (start_steady < 0 and end_steady < 0) or (start_steady < 0 or end_steady < 0):
            points = showselect(
                emgfile,
                title="Select the start/end area of the steady-state by hovering the mouse\nand pressing the 'a'-key. Wrong points can be removed with right click.\nWhen ready, press enter.",
                titlesize=10,
            )
            start_steady, end_steady = points[0], points[1]

    # Create an object to append the results
    toappend_drvariability = []
    for mu in range(emgfile["NUMBER_OF_MUS"]):  # Loop all the MUs

        # COVisi rec
        selected_idr = idr[mu]["idr"].iloc[0:n_firings_RecDerec]
        drvariabilityrec = (selected_idr.std() / selected_idr.mean()) * 100

        # COVisi derec
        length = len(idr[mu]["idr"])
        selected_idr = idr[mu]["idr"].iloc[
            length - n_firings_RecDerec + 1: length
        ]  # +1 because len() counts position 0
        drvariabilityderec = (selected_idr.std() / selected_idr.mean()) * 100

        # COVisi all steady
        if (event_ == "rec_derec_steady" or event_ == "steady"):
            idr_indexed = idr[mu].set_index("mupulses")
            selected_idr = idr_indexed["idr"].loc[start_steady: end_steady]
            drvariabilitysteady = (selected_idr.std() / selected_idr.mean()) * 100

        # COVisi all contraction
        selected_idr = idr[mu]["idr"]
        drvariabilityall = (selected_idr.std() / selected_idr.mean()) * 100

        if event_ == "rec":
            toappend_drvariability.append(
                {"DRvar_rec": drvariabilityrec, "DRvar_all": drvariabilityall}
            )
        elif event_ == "derec":
            toappend_drvariability.append(
                {
                    "DRvar_derec": drvariabilityderec,
                    "DRvar_all": drvariabilityall,
                }
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
                {
                    "DRvar_steady": drvariabilitysteady,
                    "DRvar_all": drvariabilityall,
                }
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
