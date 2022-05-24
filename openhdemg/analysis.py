import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def basic_mus_properties(emgfile, 
                            n_firings_RecDerec = 4,
                            n_firings_steady = 10,
                            ):

    # Extract the variables of interest from the EMG file
    SOURCE = emgfile["SOURCE"] 
    NUMBER_OF_MUS = emgfile["NUMBER_OF_MUS"] 
    PNR = emgfile["PNR"]
    MUPULSES = emgfile["MUPULSES"] 
    REF_SIGNAL = emgfile["REF_SIGNAL"] 
    FSAMP = emgfile["FSAMP"] 


    # --------------------------------- Collect the information to export -------------------------------------
    #
    # First: create a dataframe that contains all the output
    exportable_df = []

    # Second: add basic information (MVC, MU number, PNR, Average PNR) ------ Ottieni nome del partecipante ed MVC dall'esterno? per il batch????
    inputMVC = int(input("--------------------------------\nEnter MVC value in newton: "))
    exportable_df.append({"MVC":inputMVC})
    exportable_df = pd.DataFrame(exportable_df)

    # Basically, we create an empty list, append values, convert the list in df and then concatenate to the exportable_df
    toappend = []
    for i in range(NUMBER_OF_MUS):
        toappend.append({"MU_number":i+1})
    toappend = pd.DataFrame(toappend)
    exportable_df = pd.concat([exportable_df,toappend], axis=1)

    # Only for DEMUSE files at this point (once we compute the PNR for the OTB decomposition, we can use it for both)
    if SOURCE == "DEMUSE":
        # Repeat the task for every new column to fill and concatenate
        toappend = []
        for i in range(NUMBER_OF_MUS):
            toappend.append({"PNR":PNR[0][i]})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df,toappend], axis=1)

        # Repeat again...
        toappend = []
        toappend.append({"avg_PNR":np.average(PNR)})
        toappend = pd.DataFrame(toappend)
        exportable_df = pd.concat([exportable_df,toappend], axis=1)

    # --------------------------------------- Calculate RT and DERT -------------------------------------------
    #

    toappend = []
    # Loop all the MUs
    for i in range(NUMBER_OF_MUS):
        # Detect the first and last firing of the MU
        mup_rec = MUPULSES[i][0]
        mup_derec = MUPULSES[i][-1]
        # Calculate absolute and relative RT and DERT
        abs_RT = ((float(REF_SIGNAL.iloc[mup_rec]) * float(inputMVC)) / 100) * 9.81
        abs_DERT = ((float(REF_SIGNAL.iloc[mup_derec]) * float(inputMVC)) / 100) * 9.81
        rel_RT = float(REF_SIGNAL.iloc[mup_rec])
        rel_DERT = float(REF_SIGNAL.iloc[mup_derec])

        toappend.append({"abs_RT":abs_RT, "abs_DERT":abs_DERT, "rel_RT":rel_RT, "rel_DERT":rel_DERT})

    toappend = pd.DataFrame(toappend)   
    exportable_df = pd.concat([exportable_df, toappend], axis=1)

    # ------------------------------ Calculate DR at recruitment and derecruitment -----------------------------
    #

    toappend = []
    # Loop all the MUs
    for i in range(NUMBER_OF_MUS):
        mup = pd.DataFrame(MUPULSES[i])
        # Calculate the delta (difference) between the firings and istantaneous discharge rate (idr)
        idr = FSAMP / mup.diff()
        # Then divide FSAMP for the average delta between the firings in the interval specified in "n_firings_RecDerec"
        pps_rec = np.mean(idr[0 : n_firings_RecDerec], axis=0) # Can use 0 because it ignores the firs nan value
        pps_derec = np.mean(idr[len(idr)-n_firings_RecDerec+1 : len(idr)], axis=0) # +1 because len() counts position 0

        toappend.append({"DR_rec":pps_rec[0],"DR_derec":pps_derec[0]}) # 0 because has index column to omit

    toappend = pd.DataFrame(toappend)
    exportable_df = pd.concat([exportable_df, toappend], axis=1)

    # Delete idr to use it below
    del idr

    # ------------------ Calculate DR at all, start and end steady-state and all contraction -------------------
    #

    # Visualise and select the steady-state
    plt.figure(num="Fig_ginput")
    plt.plot(REF_SIGNAL[0])
    plt.xlabel("Samples")
    plt.ylabel("%MViF")
    plt.title("Select start/end of the steady-state phase", fontweight ="bold")
    ginput_res = plt.ginput(n=-1)
    # Sort the input range of the steady-state
    if ginput_res[0][0] < ginput_res[1][0]:
        start_steady = round(ginput_res[0][0])
        end_steady = round(ginput_res[1][0])
    else:
        start_steady = round(ginput_res[1][0])
        end_steady = round(ginput_res[0][0])

    # Now calculate the DR in the specified range
    toappend = []
    # Loop all the MUs
    for i in range(NUMBER_OF_MUS):
        mup = pd.DataFrame(MUPULSES[i])
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
        
        # Calculate the DR for the entire stedy-state phase and for all the contraction
        pps_all_steady = np.mean(idr[0].iloc[ind_start+1 : ind_end], axis=0)
        pps_all_contraction = np.mean(idr[0], axis=0)

        toappend.append({"DR_start_steady":pps_start,"DR_end_steady":pps_end,"DR_all_steady":pps_all_steady,"DR_all_contraction":pps_all_contraction}) # 0 because has index column to omit

    toappend = pd.DataFrame(toappend)
    exportable_df = pd.concat([exportable_df, toappend], axis=1)

    print("\n--------------------------------\nFinal dataframe containing basic MUs properties:\n\n{}".format(exportable_df))

    return exportable_df
    
    