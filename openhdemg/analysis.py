import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#from openhdemg.tools import showselect, compute_idr
from tools import showselect, compute_idr


def compute_thresholds(emgfile, event_="rt_dert", type_="abs_rel", mvif=0):
    """
    This function calculates the recruitment/derecruitment thresholds in absolute and relative therms.

    The first argument should be the emgfile.

    Input parameters for event_ are: "rt", "dert", "rt_dert".
    type="rt_dert" means that both recruitment and derecruitment tresholds will be calculated.
    type="rt" means that only recruitment tresholds will be calculated.
    type="dert" means that only derecruitment tresholds will be calculated.

    Input parameters for type_ are: "abs", "rel", "abs_rel".
    type="abs_rel" means that both absolute and relative tresholds will be calculated.
    type="rel" means that only relative tresholds will be calculated.
    type="abs" means that only absolute tresholds will be calculated.

    if mvif is 0, ask the user to input mvif, otherwise use the value passed.

    The function returns a DataFrame containing the requested thresholds.
    """
    # Extract the variables of interest from the EMG file
    NUMBER_OF_MUS = emgfile["NUMBER_OF_MUS"]
    MUPULSES = emgfile["MUPULSES"]
    REF_SIGNAL = emgfile["REF_SIGNAL"]

    # Check that all the inputs are correct
    assert event_ in ["rt_dert", "rt", "dert"], f"event_ must be one of the following strings: rt_dert, rt, dert. {event_} was passed instead."
    assert type_ in ["abs_rel", "rel", "abs"], f"event_ must be one of the following strings: abs_rel, rel, abs. {event_} was passed instead."
    if not isinstance(mvif, (float, int)):
        raise Exception(f"mvif must be one of the following types: float, int. {type(mvif)} was passed instead.")

    if type_ != "rel" and mvif == 0:
        # Ask the user to input MViF
        mvif = int(input("--------------------------------\nEnter MVC value in newton: "))
    
    # Create an object to append the results
    toappend = []
    # Loop all the MUs
    for i in range(NUMBER_OF_MUS):
        if NUMBER_OF_MUS > 1:
            # Detect the first and last firing of the MU and manage the exception of a single MU
            mup_rec = MUPULSES[i][0]
            mup_derec = MUPULSES[i][-1]
        else:
            # Detect the first and last firing of the MU and manage the exception of a single MU
            mup_rec = MUPULSES[0]
            mup_derec = MUPULSES[-1]

        # Calculate absolute and relative RT and DERT if requested
        abs_RT = ((float(REF_SIGNAL.iloc[mup_rec]) * float(mvif)) / 100) * 9.81
        abs_DERT = ((float(REF_SIGNAL.iloc[mup_derec]) * float(mvif)) / 100) * 9.81
        rel_RT = float(REF_SIGNAL.iloc[mup_rec])
        rel_DERT = float(REF_SIGNAL.iloc[mup_derec])

        if event_ == "rt_dert" and type_ =="abs_rel":
            toappend.append({"abs_RT":abs_RT, "abs_DERT":abs_DERT, "rel_RT":rel_RT, "rel_DERT":rel_DERT})

        elif event_ == "rt" and type_ =="abs_rel":
            toappend.append({"abs_RT":abs_RT, "rel_RT":rel_RT})
        
        elif event_ == "dert" and type_ =="abs_rel":
            toappend.append({"abs_DERT":abs_DERT, "rel_DERT":rel_DERT})

        elif event_ == "rt_dert" and type_ =="abs":
            toappend.append({"abs_RT":abs_RT, "abs_DERT":abs_DERT})
        
        elif event_ == "rt" and type_ =="abs":
            toappend.append({"abs_RT":abs_RT})

        elif event_ == "dert" and type_ =="abs":
            toappend.append({"abs_DERT":abs_DERT})
        
        elif event_ == "rt_dert" and type_ =="rel":
            toappend.append({"rel_RT":rel_RT, "rel_DERT":rel_DERT})
        
        elif event_ == "rt" and type_ =="rel":
            toappend.append({"rel_RT":rel_RT})
        
        elif event_ == "dert" and type_ =="rel":
            toappend.append({"rel_DERT":rel_DERT})

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


def compute_dr(emgfile, n_firings_RecDerec = 4, n_firings_steady = 10, event_="rec_derec_steady"):
    """
    This function can calculate the discharge rate at recruitment, derecruitment and during the steady-state phase.

    The first argument should be the emgfile.

    The user will need to select the start and end of the steady-state phase manually.

    The number of firings used for the DR calculation at recruitment/derecruitment and at the start/end of the steady-state phase
    can be passed to n_firings_RecDerec and n_firings_steady.

    Input parameters for event_ are: "rec", "derec", "rec_derec", "steady", "rec_derec_steady".
    type="rec_derec_steady" means that the DR is calculated at recruitment, derecruitment and during the steady-state phase.
    type="rec" means that the DR is calculated at recruitment.
    type="derec" means that the DR is calculated at derecruitment.
    type="rec_derec" means that the DR is calculated at recruitment and derecruitment.
    type="steady" means that the DR is calculated during the steady-state phase.

    The user can specify the number of firings to consider at recruitment/derecruitment and 
    at the start and end of the steady-state phase.
    
    DR for all the contraction is automatically calculated and returned.

    The function returns a DataFrame containing the requested DR.
    """

    # Extract the variables of interest from the EMG file
    NUMBER_OF_MUS = emgfile["NUMBER_OF_MUS"]
    MUPULSES = emgfile["MUPULSES"]
    FSAMP = emgfile["FSAMP"]

    # Check that all the inputs are correct
    errormessage = f"event_ must be one of the following strings: rec, derec, rec_derec, steady, rec_derec_steady. {event_} was passed instead."
    assert event_ in ["rec", "derec", "rec_derec", "steady", "rec_derec_steady"], errormessage
    if not isinstance(n_firings_RecDerec, int):
        raise Exception(f"n_firings_RecDerec must be an integer. {type(n_firings_RecDerec)} was passed instead.")
    if not isinstance(n_firings_steady, int):
        raise Exception(f"n_firings_steady must be an integer. {type(n_firings_steady)} was passed instead.")

    # Create an object to append the results of the recruitment and derecruitment only
    toappend_recderec = []
    # Calculate DR at recruitment and derecruitment
    if event_ != "steady":
        # Loop all the MUs
        for i in range(NUMBER_OF_MUS):
            mup = pd.DataFrame(MUPULSES[i]) if NUMBER_OF_MUS > 1 else pd.DataFrame(MUPULSES) # Manage exception of a single MU
            # Calculate the istantaneous discharge rate (idr)
            idr = FSAMP / mup.diff()
            # Then average idr between the firings in the interval specified in "n_firings_RecDerec"
            pps_rec = np.mean(idr[0 : n_firings_RecDerec], axis=0) # Can use 0 because it ignores the firs nan value
            pps_derec = np.mean(idr[len(idr)-n_firings_RecDerec+1 : len(idr)], axis=0) # +1 because len() counts position 0

            if event_ == "rec_derec" or event_ == "rec_derec_steady":
                toappend_recderec.append({"DR_rec":pps_rec[0],"DR_derec":pps_derec[0]}) # 0 because has index column to omit
            elif event_ == "rec":
                toappend_recderec.append({"DR_rec":pps_rec[0]}) # 0 because has index column to omit
            elif event_ == "derec":
                toappend_recderec.append({"DR_derec":pps_derec[0]}) # 0 because has index column to omit
        
        # Convert the dictionary in a DataFrame
        toappend_recderec = pd.DataFrame(toappend_recderec)
    
    # Create an object to append the results of the steady-state only
    toappend_steady = []
    # Calculate DR at all, start and end steady-state and all contraction
    if event_ == "steady" or event_ == "rec_derec_steady":
        # Visualise and select the steady-state
        start_steady, end_steady = showselect(emgfile, title="Select start/end of the steady-state phase then press enter")

        # Now calculate the DR in the specified range
        # Loop all the MUs
        for i in range(NUMBER_OF_MUS):
            mup = pd.DataFrame(MUPULSES[i]) if NUMBER_OF_MUS > 1 else pd.DataFrame(MUPULSES) # Manage exception of a single MU
            # Calculate the delta (difference) between the firings and istantaneous discharge rate (idr)
            idr = FSAMP / mup.diff()
            # Add to the idr df the corresponding position of the ref signal
            idr["pos"] = mup
            
            # Find the first firing of the steady and calculkate DR at start steady
            for ind_start in idr.index:
                if idr["pos"].loc[ind_start] >= start_steady:
                    break
            pps_start = np.mean(idr[0].iloc[ind_start+1 : ind_start+n_firings_steady], axis=0) # +1 because to work only on the steady state
            
            # Find the last firing of the steady and calculkate DR at end steady
            for ind_end in idr.index:
                if idr["pos"].loc[ind_end] >= end_steady:
                    break
            pps_end = np.mean(idr[0].iloc[ind_end+1-n_firings_steady : ind_end], axis=0) # Stop to ind (and not ind-1) because iloc excludes the last element (as Python standard)
            
            # Calculate the DR for the entire stedy-state
            pps_all_steady = np.mean(idr[0].iloc[ind_start+1 : ind_end], axis=0)
            
            toappend_steady.append({"DR_start_steady":pps_start,"DR_end_steady":pps_end,"DR_all_steady":pps_all_steady}) # 0 because has index column to omit
    
        # Convert the dictionary in a DataFrame
        toappend_steady = pd.DataFrame(toappend_steady)

    # Create an object to append the results of all the contraction only
    toappend_allcontr = []
    # Calculate the DR for all the contraction, this is done in any case, then the user can decide whether to use it or not
    # Loop all the MUs
    for i in range(NUMBER_OF_MUS):
        mup = pd.DataFrame(MUPULSES[i]) if NUMBER_OF_MUS > 1 else pd.DataFrame(MUPULSES) # Manage exception of a single MU
        # Calculate the delta (difference) between the firings and istantaneous discharge rate (idr)
        idr = FSAMP / mup.diff()

        pps_all_contraction = np.mean(idr[0], axis=0)

        toappend_allcontr.append({"DR_all_contraction":pps_all_contraction})
    
    # Convert the dictionary in a DataFrame
    toappend_allcontr = pd.DataFrame(toappend_allcontr)
    
    # Merge the appended DataFrames
    if isinstance(toappend_recderec, pd.DataFrame):
        toappend_allcontr = pd.concat([toappend_allcontr, toappend_recderec], axis=1)
    if isinstance(toappend_steady, pd.DataFrame):
        toappend_allcontr = pd.concat([toappend_allcontr, toappend_steady], axis=1)
    
    mus_dr = pd.DataFrame(toappend_allcontr)
    
    """
    print(mus_dr)
    DR_all_contraction    DR_rec  DR_derec  DR_start_steady  DR_end_steady  DR_all_steady
    0            7.225373  6.139581  4.751324         8.146854       6.417864       7.167632
    1            5.692758  5.212117  4.349304         6.446452       5.242241       5.713736
    2            7.685846  6.154896  4.505799         8.512083       7.337702       7.801723
    3            6.374818  5.019371  4.023208         7.184807       5.833290       6.396255
    4            6.352171  4.304906  4.503785         6.598922       6.025797       6.472538
    ...
    """
    
    return mus_dr


def basic_mus_properties(emgfile, n_firings_RecDerec = 4, n_firings_steady = 10, mvif = 0):
    """
    This function can calculate all the basic properties of the MUs of a trapezoidal contraction,
    in particular the absolute/relative recruitment thresholds and
    the discharge rate at recruitment, derecruitment and during the steady-state phase.

    The first argument should be the emgfile.

    The number of firings used for the DR calculation at recruitment/derecruitment and at the start/end of the steady-state phase
    can be passed to n_firings_RecDerec and n_firings_steady.

    The user will only need to select the start and end of the steady-state phase manually and to enter
    the MViF if this is not specified (by default mvif = 0) while calling the function basic_mus_properties. If 
    mvif is a number different from 0, this value is used instead.

    The function returns a DataFrame containing all the results.
    """

    # Extract the variables of interest from the EMG file
    SOURCE = emgfile["SOURCE"] 
    NUMBER_OF_MUS = emgfile["NUMBER_OF_MUS"] 
    PNR = emgfile["PNR"]

    # Collect the information to export
    #
    # First: create a dataframe that contains all the output
    exportable_df = []

    # Second: add basic information (MVC, MU number, PNR, Average PNR)
    if mvif == 0:
        # Ask the user to input MViF
        mvif = int(input("--------------------------------\nEnter MVC value in newton: "))

    exportable_df.append({"MVC":mvif})
    exportable_df = pd.DataFrame(exportable_df)

    # Basically, we create an empty list, append values, convert the list in df and then concatenate to the exportable_df
    toappend = []
    for i in range(NUMBER_OF_MUS):
        toappend.append({"MU_number":i+1})
    toappend = pd.DataFrame(toappend)
    exportable_df = pd.concat([exportable_df, toappend], axis=1)

    # Only for DEMUSE files at this point (once we compute the PNR for the OTB decomposition, we can use it for both)
    if SOURCE == "DEMUSE":
        # Repeat the task for every new column to fill and concatenate
        toappend = []
        for i in range(NUMBER_OF_MUS):
            toappend.append({"PNR":PNR[0][i]})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

        # Repeat again...
        toappend = []
        toappend.append({"avg_PNR":np.average(PNR)})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df, toappend], axis=1)

    # Calculate RT and DERT
    mus_thresholds = compute_thresholds(emgfile=emgfile, mvif=mvif)   
    exportable_df = pd.concat([exportable_df, mus_thresholds], axis=1)

    # Calculate DR at recruitment, derecruitment, all, start and end steady-state and all contraction
    mus_dr = compute_dr(emgfile=emgfile, n_firings_RecDerec=n_firings_RecDerec, n_firings_steady=n_firings_steady)
    exportable_df = pd.concat([exportable_df, mus_dr], axis=1)

    # Print the dataframe containing all the results
    print("\n--------------------------------\nFinal dataframe containing basic MUs properties:\n\n{}".format(exportable_df))

    """ 
    print(exportable_df)
         MVC  MU_number   PNR  avg_PNR      abs_RT    abs_DERT    rel_RT  rel_DERT  DR_all_contraction    DR_rec  DR_derec  DR_start_steady  DR_end_steady  DR_all_steady
    0  555.0          1  33.7  32.0125  220.990703  338.584589  4.058934  6.218780            7.225373  6.139581  4.751324         8.222959       6.380241       7.300628
    1    NaN          2  36.9      NaN  342.778042  383.379447  6.295801  7.041527            5.692758  5.212117  4.349304         5.774452       5.153086       5.758279
    2    NaN          3  29.5      NaN  233.166062  215.877558  4.282559  3.965021            7.685846  6.154896  4.505799         7.626115       7.341725       7.807892
    3    NaN          4  36.7      NaN  296.928492  304.142582  5.453683  5.586184            6.374818  5.019371  4.023208         6.882195       5.681288       6.473001
    4    NaN          5  28.8      NaN  409.113920  338.584589  7.514192  6.218780            6.352171  4.304906  4.503785         6.103125       6.041242       6.466309
    ...
    """

    return exportable_df



###########################################################################################################################################################
###########################################################################################################################################################
###########################################################################################################################################################
# Test part
if __name__ == "__main__":
    import os, sys
    from openfiles import emg_from_demuse, emg_from_otb
    
    file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_testfile.mat") # Test it on a common trapezoidal contraction
    #file_toOpen = os.path.join(sys.path[0], "Decomposed Test files/DEMUSE_10MViF_TRAPEZOIDAL_only1MU_testfile.mat") # Test it on a contraction with a single MU

    emgfile = emg_from_demuse(file=file_toOpen)

    df_basic_MUs_properties = basic_mus_properties(emgfile = emgfile)
    idr = compute_idr(emgfile = emgfile)
    print(idr)