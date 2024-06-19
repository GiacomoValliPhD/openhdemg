"""
This module contains all the functions used to quantify and analyze MU
persistent inward currents.

Currently includes delta F.
"""

import pandas as pd
import numpy as np
from itertools import combinations


def compute_deltaf(
    emgfile,
    smoothfits,
    average_method="test_unit_average",
    normalisation="False",
    recruitment_difference_cutoff=1.0,
    corr_cutoff=0.7,
    controlunitmodulation_cutoff=0.5,
    clean=True,
):
    """
    Quantify delta F via paired motor unit analysis.

    Conducts a paired motor unit analysis, quantifying delta F between the
    supplied collection of motor units. Origional framework for deltaF provided
    in Gorassini et. al., 2002:
    https://journals.physiology.org/doi/full/10.1152/jn.00024.2001

    Author: James (Drew) Beauchamp

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    smoothfits : list of arrays
        Smoothed discharge rate estimates.
        Each array: motor unit discharge rate x samples aligned in time;
        instances of non-firing = NaN
        Your choice of smoothing. See compute_svr gen_svr for example.
    average_method : str {"test_unit_average", "all"}, default "test_unit_average"
        The method for test MU deltaF value. More to be added.

        ``test_unit_average``
            The average across all possible control units.

        ``all``
            This returns all possible MU pairs
    normalisation : str {"False", "ctrl_max_desc"}, default "False"
        The method for deltaF nomalization.

        ``ctrl_max_desc``
            Whether to normalise deltaF values to control unit descending
            range during test unit firing. See Skarabot et. al., 2023:
            https://www.biorxiv.org/content/10.1101/2023.10.16.562612v1
    recruitment_difference_cutoff : float, default 1
        An exlusion criteria corresponding to the necessary difference between
        control and test MU recruitement in seconds.
    corr_cutoff : float (0 to 1), default 0.7
        An exclusion criteria corresponding to the correlation between control
        and test unit discharge rate.
    controlunitmodulation_cutoff : float, default 0.5
        An exclusion criteria corresponding to the necessary modulation of
        control unit discharge rate during test unit firing in Hz.
    clean : bool, default True
        To remove values that do not meet exclusion criteria

    Returns
    -------
    delta_f : pd.DataFrame
        A pd.DataFrame containing deltaF values and corresponding MU number.
        The resulting df will be different depending on average_method.
        In particular, if average_method="all", delta_f[MU][row] will
        contain a tuple representing the indices of the two motor units
        for each given pair (reporter, test) and their corresponding 
        deltaF value.

    See also
    --------
    - compute_svr : fit MU discharge rates with Support Vector Regression,
        nonlinear regression.

    Examples
    --------
    Quantify delta F using svr fits.

    >>> import openhdemg.library as emg
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.sort_mus(emgfile=emgfile)
    >>> svrfits = emg.compute_svr(emgfile)
    >>> delta_f = emg.compute_deltaf(
    ...     emgfile=emgfile, smoothfits=svrfits["gensvr"],
    ... )
    delta_f
       MU        dF
    0   0       NaN
    1   1       NaN
    2   2       NaN
    3   3  1.838382
    4   4  2.709522

    For all possible combinations, not test unit average, MU in this case is
    pairs (reporter, test).

    >>> delta_f_2 = emg.compute_deltaf(
    ...     emgfile=emgfile, smoothfits=svrfits["gensvr"], average_method='all',
    ... )
    delta_f_2
           MU        dF
    0  (0, 1)       NaN
    1  (0, 2)       NaN
    2  (0, 3)  2.127461
    3  (0, 4)       NaN
    4  (1, 2)       NaN
    5  (1, 3)  1.549303
    6  (1, 4)       NaN
    7  (2, 3)       NaN
    8  (2, 4)       NaN
    9  (3, 4)  2.709522
    """

    dfret_ret = []
    mucombo_ret = np.empty(0, int)

    # If less than 2 MUs, can not quantify deltaF
    if emgfile["NUMBER_OF_MUS"] < 2:
        dfret_ret = np.nan
        mucombo_ret = np.nan*np.ones([1, 2]) 

        delta_f = pd.DataFrame({'MU': mucombo_ret, 'dF': dfret_ret})

        return delta_f

    # If more than 2 MUs, quantify deltaF.
    # Combinations of MUs.
    combs = combinations(range(emgfile["NUMBER_OF_MUS"]), 2)
    # TODO if units are nonconsecutive

    # init
    r_ret = []
    dfret = []
    testmu = []
    ctrl_mod = []
    mucombo = []
    rcrt_diff = []
    controlmu = [] 
    for mucomb in list(combs):  # For all possible combinations of MUs
        # Extract possible MU combinations (a unique MU pair)
        mu1_id, mu2_id = mucomb[0], mucomb[1]
        # Track current MU combination
        mucombo.append((mu1_id, mu2_id))

        # First MU firings, recruitment, and decrecruitment
        mu1_times = np.where(emgfile["BINARY_MUS_FIRING"][mu1_id] == 1)[0]
        mu1_rcrt, mu1_drcrt = mu1_times[1], mu1_times[-1]
        # Skip first since idr is defined on second

        # Second MU firings, recruitment, and decrecruitment
        mu2_times = np.where(emgfile["BINARY_MUS_FIRING"][mu2_id] == 1)[0]
        mu2_rcrt, mu2_drcrt = mu2_times[1], mu2_times[-1]
        # Skip first since idr is defined on second

        # Region of MU overlap
        muoverlap = range(
            max(mu1_rcrt, mu2_rcrt), min(mu1_drcrt, mu2_drcrt),
        )

        # If MUs do not overlapt by more than two or more samples
        if len(muoverlap) < 2:
            dfret = np.append(dfret, np.nan)
            r_ret = np.append(r_ret, np.nan)
            rcrt_diff = np.append(rcrt_diff, np.nan)
            ctrl_mod = np.append(ctrl_mod, np.nan)
            continue  # TODO test

        # Corr between units - not always necessary, can be set to 0 when
        # desired.
        r = pd.DataFrame(
            zip(
                smoothfits[mu1_id][muoverlap],
                smoothfits[mu2_id][muoverlap],
            )
        ).corr()
        r_ret = np.append(r_ret, r[0][1])

        # Recruitment diff, necessary to ensure PICs are activated in
        # control unit.
        rcrt_diff = np.append(
            rcrt_diff, np.abs(mu1_rcrt-mu2_rcrt)/emgfile["FSAMP"],
        )
        if mu1_rcrt < mu2_rcrt:
            controlU = 1  # MU 1 is control unit, 2 is test unit

            # If control (reporter) unit is not on for entirety of test
            # unit, set last firing to control unit.
            if mu1_drcrt < mu2_drcrt:
                mu2_drcrt = mu1_drcrt
                # This may understimate PICs, other methods can be employed
            # delta F: change in control MU discharge rate between test
            # unit recruitment and derecruitment.
            df = smoothfits[mu1_id][mu2_rcrt]-smoothfits[mu1_id][mu2_drcrt]

            # Control unit discharge rate modulation while test unit is
            # firing.
            ctrl_mod = np.append(
                ctrl_mod,
                np.nanmax(smoothfits[mu1_id][range(mu2_rcrt, mu2_drcrt)])
                - np.nanmin(smoothfits[mu1_id][range(mu2_rcrt, mu2_drcrt)]),
            )

            if normalisation == "False":
                dfret = np.append(dfret, df)
            elif normalisation == "ctrl_max_desc":
                # Normalise deltaF values to control unit descending range
                # during test unit firing.
                k = smoothfits[mu1_id][mu2_rcrt]-smoothfits[mu1_id][mu1_drcrt]
                dfret = np.append(dfret, df/k)

        elif mu1_rcrt > mu2_rcrt:
            controlU = 2  # MU 2 is control unit, 1 is test unit
            if mu1_drcrt > mu2_drcrt:
                # If control (reporter) unit is not on for entirety of
                # test unit, set last firing to control unit.
                mu1_drcrt = mu2_drcrt
                # This may understimate PICs, other methods can be employed.
            # delta F: change in control MU discharge rate between test
            # unit recruitment and derecruitment.
            df = smoothfits[mu2_id][mu1_rcrt]-smoothfits[mu2_id][mu1_drcrt]

            # Control unit discharge rate modulation while test unit is
            # firing.
            ctrl_mod = np.append(
                ctrl_mod,
                np.nanmax(smoothfits[mu2_id][range(mu1_rcrt, mu1_drcrt)])
                - np.nanmin(smoothfits[mu2_id][range(mu1_rcrt, mu1_drcrt)]),
            )

            if normalisation == "False":
                dfret = np.append(dfret, df)
            elif normalisation == "ctrl_max_desc":
                # Normalise deltaF values to control unit descending range
                # during test unit firing.
                k = smoothfits[mu2_id][mu1_rcrt]-smoothfits[mu2_id][mu2_drcrt]
                dfret = np.append(dfret, df/k)

        elif mu1_rcrt == mu2_rcrt:
            if mu1_drcrt > mu2_drcrt:
                controlU = 1  # MU 1 is control unit, 2 is test unit
                # delta F: change in control MU discharge rate between
                # test unit recruitment and derecruitment.
                df = smoothfits[mu1_id][mu2_rcrt]-smoothfits[mu1_id][mu2_drcrt]

                # Control unit discharge rate modulation while test unit is
                # firing.
                ctrl_mod = np.append(
                    ctrl_mod,
                    np.nanmax(smoothfits[mu1_id][range(mu2_rcrt, mu2_drcrt)])
                    - np.nanmin(smoothfits[mu1_id][range(mu2_rcrt, mu2_drcrt)]),
                )

                if normalisation == "False":
                    dfret = np.append(dfret, df)
                elif normalisation == "ctrl_max_desc":
                    # Normalise deltaF values to control unit descending
                    # range during test unit firing.
                    k = smoothfits[mu1_id][mu2_rcrt]-smoothfits[mu1_id][mu1_drcrt]
                    dfret = np.append(dfret, df/k)
            else:
                controlU = 2  # MU 2 is control unit, 1 is test unit
                # delta F: change in control MU discharge rate between
                # test unit recruitment and derecruitment.
                df = smoothfits[mu2_id][mu1_rcrt]-smoothfits[mu2_id][mu1_drcrt]

                # Control unit discharge rate modulation while test unit is
                # firing.
                ctrl_mod = np.append(
                    ctrl_mod,
                    np.nanmax(smoothfits[mu2_id][range(mu1_rcrt, mu1_drcrt)])
                    - np.nanmin(smoothfits[mu2_id][range(mu1_rcrt, mu1_drcrt)]),
                )

                if normalisation == "False":
                    dfret = np.append(dfret, df)
                elif normalisation == "ctrl_max_desc":
                    # Normalise deltaF values to control unit descending
                    # range during test unit firing.
                    k = smoothfits[mu2_id][mu1_rcrt]-smoothfits[mu2_id][mu2_drcrt]
                    dfret = np.append(dfret, df/k)

        # Collect which MUs were control vs test
        controlmu.append(mucombo[-1][controlU-1])
        testmu.append(mucombo[-1][1-controlU//2])

    if clean:  # Remove values that dont meet exclusion criteria
        rcrt_diff_bin = rcrt_diff > recruitment_difference_cutoff
        corr_bin = r_ret > corr_cutoff
        ctrl_mod_bin = ctrl_mod > controlunitmodulation_cutoff
        clns = np.asarray([rcrt_diff_bin & corr_bin & ctrl_mod_bin])
        dfret[~clns[0]] = np.nan

    if average_method == "test_unit_average":
        # Average across all control units
        for ii in range(emgfile["NUMBER_OF_MUS"]):
            clean_indices = [
                index for (index, item) in enumerate(testmu) if item == ii
            ]
            if np.isnan(dfret[clean_indices]).all():
                dfret_ret = np.append(dfret_ret, np.nan)
            else:
                dfret_ret = np.append(
                    dfret_ret, np.nanmean(dfret[clean_indices]),
                )
            mucombo_ret = np.append(mucombo_ret, int(ii))
    else:  # Return all values and corresponding combinations
        dfret_ret = dfret
        mucombo_ret = mucombo

    delta_f = pd.DataFrame({'MU': mucombo_ret, 'dF': dfret_ret})

    return delta_f
