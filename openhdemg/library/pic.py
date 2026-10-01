"""
This module contains all the functions used to quantify and analyze MU
persistent inward currents.

Includes SVR smoothing of MU discharge rates and delta F estimation.
"""

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import iqr
from sklearn.svm import SVR

from openhdemg.library.tools import compute_idr


def compute_svr(
    emgfile,
    gammain=1/1.6,
    regparam=1/0.370,
    endpointweights_numpulses=5,
    endpointweights_magnitude=5,
    discontfiring_dur=1.0,
):
    """
    Fit MU discharge rates with Support Vector Regression, nonlinear
    regression.

    Provides smooth and continous estimates of discharge rate useful for
    quantification and visualisation. Suggested hyperparameters and framework
    from Beauchamp et. al., 2022
    https://doi.org/10.1088/1741-2552/ac4594

    Author: James (Drew) Beauchamp

    Parameters
    ----------
    emgfile : dict
        The dictionary containing the emgfile.
    gammain : float,  default 1/1.6
        The kernel coefficient.
    regparam : float,  default 1/0.370
        The regularization parameter, must be positive.
    endpointweights_numpulses : int, default 5
        Number of discharge instances at the start and end of MU firing to
        apply a weighting coefficient.
    endpointweights_magnitude : int, default 5
        The scaling factor applied to the number of pulses provided by
        endpointweights_numpulses.
        The scaling is applied to the regularization parameter, per sample.
        Larger values force the classifier to put more emphasis on the number
        of discharge instances at the start and end of firing provided by
        endpointweights_numpulses.
    discontfiring_dur : int, default 1
        Duration of time in seconds that defines an instnance of discontinuous
        firing. SVR fits will not be returned at points of discontinuity.

    Returns
    -------
    svrfits : pd.DataFrame
        A pd.DataFrame containing the smooth/continous MU discharge rates and
        corresponding time vectors.

    See also
    --------
    - compute_deltaf : quantify delta F via paired motor unit analysis.

    Examples
    --------
    Quantify svr fits.

    >>> import openhdemg.library as emg
    >>> import pandas as pd
    >>> emgfile = emg.emg_from_samplefile()
    >>> emgfile = emg.sort_mus(emgfile=emgfile)
    >>> svrfits = emg.compute_svr(emgfile)

    Quick plot showing the results.

    >>> smoothfits = pd.DataFrame(svrfits["gensvr"]).transpose()
    >>> emg.plot_smoothed_dr(
    >>>     emgfile,
    >>>     smoothfits=smoothfits,
    >>>     munumber="all",
    >>>     addidr=False,
    >>>     stack=True,
    >>>     addrefsig=True,
    >>> )
    """

    # TODO input checking and edge cases
    idr = compute_idr(emgfile)  # Calc IDR

    svrfit_acm = []
    svrtime_acm = []
    gensvr_acm = []
    for mu in range(len(idr)):  # For all MUs
        # Skip if no data
        if idr[mu].size==0:
            svrfit_acm.append([])
            svrtime_acm.append([])
            gensvr_acm.append(np.nan*np.ones(emgfile["EMG_LENGTH"]))

        else:            # Train the model on the data.
            # Time vector, removing first element.
            xtmp = np.transpose([idr[mu].timesec[1:]])
            # Discharge rates, removing first element, since DR has been assigned
            # to second pulse.
            ytmp = idr[mu].idr[1:].to_numpy()
            # Time between discharges, will use for discontinuity calc
            xdiff = idr[mu].diff_mupulses[2:].values
            # Motor unit pulses, samples
            mup = np.array(idr[mu].mupulses[1:].values)

            # Defining weight vector. A scaling applied to the regularization
            # parameter, per sample.
            smpwht = np.ones(len(ytmp))
            smpwht[0:endpointweights_numpulses-1] = endpointweights_magnitude
            smpwht[(len(ytmp)-(endpointweights_numpulses-1)):len(ytmp)] = endpointweights_magnitude

            # Create an SVR model with a gausian kernel and supplied hyperparams.
            # Origional hyperparameters from Beauchamp et. al., 2022:
            # https://doi.org/10.1088/1741-2552/ac4594
            svr = SVR(
                kernel='rbf', gamma=gammain, C=np.abs(regparam),
                epsilon=iqr(ytmp)/11,
            )
            svr.fit(xtmp, ytmp, sample_weight=smpwht)

            # Defining prediction vector
            # TODO need to add custom range.
            # From the second firing to the end of firing, in samples.
            predind = np.arange(mup[0], mup[-1]+1)
            predtime = (predind/emgfile["FSAMP"]).reshape(-1, 1)  # In time (s)
            newtm = []
            # Initialise nan vector for tracking fits aligned in time. Usefull for
            # later quant metrics.
            gen_svr = np.nan*np.ones(emgfile["EMG_LENGTH"])

            # Check for discontinous firing
            bkpnt = mup[
                np.where((xdiff > (discontfiring_dur * emgfile["FSAMP"])))[0]
            ]
            bkpnt = bkpnt[np.where(bkpnt != mup[-1])]

            if len(bkpnt) == 1:
                if bkpnt[0] == mup[0]:  # When first firing is the only discontinuity
                    bkpnt = []
                    predind = np.arange(mup[1], mup[-1]+1)
                    predtime = (predind/emgfile["FSAMP"]).reshape(-1, 1)

            # Make predictions on the data
            if len(bkpnt) > 0:  # If there is a point of discontinuity
                if bkpnt[0] == mup[0]:  # When first firing is discontinuity
                    smoothfit = np.nan*np.ones(1)
                    newtm = np.nan*np.ones(1)
                    bkpnt = bkpnt[1:]

                tmptm = predtime[
                    0: np.where(
                        (bkpnt[0] >= predind[0:-1]) & (bkpnt[0] < predind[1:])
                    )[0][0],
                ]  # Break up time vector for first continous range of firing
                smoothfit = svr.predict(tmptm)  # Predict with svr model
                newtm = np.append(newtm,tmptm,)  # Track new time vector

                tmpind = predind[
                    0: np.where(
                        (bkpnt[0] >= predind[0:-1]) & (bkpnt[0] < predind[1:])
                    )[0][0]
                ]  # Sample vector of first continous range of firing

                # Fill corresponding sample indices with svr fit
                gen_svr[tmpind.astype(np.int64)] = smoothfit
                # Add last firing as discontinuity
                bkpnt = np.append(bkpnt, mup[-1])
                for ii in range(len(bkpnt)-1):  # All instances of discontinuity
                    curind = np.where(
                        (bkpnt[ii] > predind[0:-1]) & (bkpnt[ii] <= predind[1:])
                    )[0][0]  # Current index of discontinuity
                    nextind = np.where(
                        (bkpnt[ii+1] > predind[0:-1]) & (bkpnt[ii+1] <= predind[1:])
                    )[0][0]  # Next index of discontinuity

                    # MU firing before discontinuity
                    curmup = np.where(mup == bkpnt[ii])[0][0]
                    curind_nmup = np.where(
                        (mup[curmup+1] > predind[0:-1]) & (mup[curmup+1] <= predind[1:])
                    )[0][0]  # MU firing after discontinuity

                    # If the next discontinuity is the next MU firing, nan fill
                    if curind_nmup >= nextind:
                        # Edge case NEED TO CHECK THE GREATER THAN CASE>> WHY TODO
                        smoothfit = np.append(smoothfit, np.nan*np.ones(1))
                        newtm = np.append(newtm, np.nan*np.ones(1))
                    else:  # Fit next continuous region of firing
                        smoothfit = np.append(
                            smoothfit,
                            np.nan*np.ones(len(predtime[curind:curind_nmup])-2),
                        )
                        smoothfit = np.append(
                            smoothfit, svr.predict(predtime[curind_nmup:nextind]),
                        )
                        newtm = np.append(
                            newtm,
                            np.nan*np.ones(len(predtime[curind:curind_nmup])-2),
                        )
                        newtm = np.append(newtm, predtime[curind_nmup:nextind],)
                        gen_svr[predind[curind_nmup:nextind]] = svr.predict(
                            predtime[curind_nmup:nextind]
                        )
            else:
                smoothfit = svr.predict(predtime)
                newtm = predtime
                gen_svr[predind] = smoothfit


            # Append fits, new time vect, time aligned fits
            svrfit_acm.append(smoothfit.copy())
            svrtime_acm.append(np.squeeze(newtm.copy()))
            gensvr_acm.append(gen_svr.copy())

    svrfits = {
        "svrfit": svrfit_acm,
        "svrtime": svrtime_acm,
        "gensvr": gensvr_acm,
    }

    return svrfits


def compute_deltaf(
    emgfile,
    smoothfits,
    average_method="test_unit_average",
    normalisation="False",
    recruitment_difference_cutoff=1.0,
    corr_cutoff=0.7,
    controlunitmodulation_cutoff=0.5,
    clean=True,
    correlation_metric="r",
):
    """
    Quantify delta F via paired motor unit analysis.

    Conducts a paired motor unit analysis, quantifying delta F between the
    supplied collection of motor units. Origional framework for deltaF provided
    in Gorassini et. al., 2002:
    https://journals.physiology.org/doi/full/10.1152/jn.00024.2001

    !!! warning "Since version 0.2.0b3"
        DeltaF estimates may differ from earlier releases because pairs whose
        reporter derecruits before the test unit are now excluded. Pair labels
        in ``average_method="all"`` now follow (reporter, test) order.

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
        To remove values that do not meet exclusion criteria. Pairs with fewer  # TODO: Drew, Should it be "To remove values that do not meet inclusion criteria."?
        than two firings in either MU, insufficient overlap, or a reporter
        that derecruits before the test unit remain invalid even if False.
    correlation_metric : str {"r", "r_squared"}, default "r"
        Use Pearson r or its square when applying corr_cutoff. Both modes
        require positive correlation. Only applied when clean=True.

    Returns
    -------
    delta_f : pd.DataFrame
        A pd.DataFrame containing deltaF values and corresponding MU number.
        The resulting df will be different depending on average_method.
        In particular, if average_method="all", delta_f[MU][row] will
        contain a tuple representing the indices of the two motor units
        for each given pair (reporter, test) and their corresponding
        deltaF value.
        Invalid pairs have NaN deltaF. With fewer than two MUs, "all" returns
        an empty DataFrame; "test_unit_average" returns one NaN per MU.

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
    ...     emgfile=emgfile,
    ...     smoothfits=svrfits["gensvr"],
    ...     average_method='all',
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

    # TODO: Drew, please check the optional r/r_squared parameter.
    if correlation_metric not in ("r", "r_squared"):
        raise ValueError("correlation_metric must be 'r' or 'r_squared'")

    dfret_ret = []
    mucombo_ret = np.empty(0, int)

    # If less than 2 MUs, can not quantify deltaF
    if emgfile["NUMBER_OF_MUS"] < 2:
        # TODO: Drew, please check the zero/one-MU output convention.
        mucombo_ret = np.arange(
            emgfile["NUMBER_OF_MUS"]
            if average_method == "test_unit_average" else 0,
        )
        dfret_ret = np.full(len(mucombo_ret), np.nan)

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
        # TODO: Drew, please check rejection of MUs with fewer than two firings.
        if np.size(np.where(emgfile["BINARY_MUS_FIRING"][mu1_id] == 1)) < 2:
            mu1_rcrt, mu1_drcrt = 0, 0
        else:
            mu1_times = np.where(emgfile["BINARY_MUS_FIRING"][mu1_id] == 1)[0]
            mu1_rcrt, mu1_drcrt = mu1_times[1], mu1_times[-1]
        # Skip first since idr is defined on second

        # Second MU firings, recruitment, and decrecruitment
        if np.size(np.where(emgfile["BINARY_MUS_FIRING"][mu2_id] == 1)) < 2:
            mu2_rcrt, mu2_drcrt = 0, 0
        else:
            mu2_times = np.where(emgfile["BINARY_MUS_FIRING"][mu2_id] == 1)[0]
            mu2_rcrt, mu2_drcrt = mu2_times[1], mu2_times[-1]
        # Skip first since idr is defined on second

        # Region of MU overlap
        muoverlap = range(
            max(mu1_rcrt, mu2_rcrt), min(mu1_drcrt, mu2_drcrt),
        )

        # TODO: Drew, please check rejection of early reporter derecruitment.
        reporter_stops_early = (
            (mu1_rcrt < mu2_rcrt and mu1_drcrt < mu2_drcrt)
            or (mu2_rcrt < mu1_rcrt and mu2_drcrt < mu1_drcrt)
        )
        # Reject unavailable deltaF endpoints, preserving pair alignment.
        if len(muoverlap) < 2 or reporter_stops_early:
            dfret = np.append(dfret, np.nan)
            r_ret = np.append(r_ret, np.nan)
            rcrt_diff = np.append(rcrt_diff, np.nan)
            ctrl_mod = np.append(ctrl_mod, np.nan)

            # Collect which MUs were control vs test
            if mu1_rcrt < mu2_rcrt or (mu1_rcrt == mu2_rcrt and mu1_drcrt > mu2_drcrt):
                controlU = 1 
            else:
                controlU = 2

            controlmu.append(mucombo[-1][controlU-1])
            testmu.append(mucombo[-1][1-controlU//2])
            continue  #

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
        # TODO: Drew, please check r-squared filtering and positive-r requirement.
        if correlation_metric == "r_squared":
            corr_bin = (r_ret > 0) & (r_ret**2 > corr_cutoff)
        else:
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
        # TODO: Drew, please check the explicit (reporter, test) labels.
        mucombo_ret = list(zip(controlmu, testmu))

    delta_f = pd.DataFrame({'MU': mucombo_ret, 'dF': dfret_ret})

    return delta_f
