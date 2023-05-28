# Graphical Interface

This is the basic introduction to the *openhdemg* GUI. In the next few sections, we will go through the basic analysis functions embedded in the GUI. For the advanced stuff, take a look at the [advanced](GUI_advanced.md) chapter. We will start with how to sort the motor units (MUs) included in your analysis file, go over force and MU property analysis, take a detour on plotting, and take a look at how to save and reset your analysis. Have fun!

--------------------------------------------

## Motor Unit Sorting
To sort the MUs included in your analysis file in order of their recruitement, we implemented a sorting algorithm. The MUs are sorted based on their recruitement order in an ascending manner.

1. Load a file. Take a look at the [intro](GUI_intro.md#specifying-an-analysis-file) section on how to do so.

2. Pay attention to view to MUs first, using the `View MUs` button next to the `Sort MUs` button (we explained this button in the [intro](GUI_intro.md) chapter). The MUs will be sorted anyways, but without viewing them you won't see what is happening. 

3. On the left hand side in the main window of the GUI, you can find the `Sort MUs` button. It is located in row three, column two. Once you press the button, the MUs will be sorted. 

## Remove Motor Units
To remove MUs included in your analysis file, you can click the `Remove MUs` button. The button is located on the left hand side in the main window of the GUI in column one of row four.

1. View the MUs using the `View MUs` button prior to MU removal, you can directly see what is happening.

2. Click the `Remove MUs` button, and a file is loaded, a pop-up window will open. 

3. Select the MU you want to delete from the analysis file from the `Select MU:`dropdown. Moreover, you can enter the number of several MUs in case you want to delete more than one. In example, selecting

    ```Python
    Select MU: 1
    ```
    will result in the first MU to be deleted. Selecting 

    ```Python
    Select MU: 1,2,5
    ```
    will result in the removal of the first, second and fifth MU.

4. Click the `Remove MU` button to remove the MU(s). 

## Reference Signal Editing
The *openhdemg* GUI also allows you to edit and filter reference signals corresponding to your analysis file (however, you can also edit and filter seperate reference signals). 

1. View the MUs using the `View MUs` button prior to reference signla editing, you can directly see what is happening.

2. Click the `RefSig Editing` button located in row five and column one, a new pop-up window opens. In the `Reference Signal Editing Window`, you can low-pass filter the reference signal as well as remove any signal offset. 

3. When you click the `Filter RefSig` button, the reference signal gets low-pass filtered according to values specified in the `Filter Order` and `Cutoff Freq` textboxes. In example, specifiying 

    ```Python
    Filter Order: 4
    Cutoff Freq: 15
    ```
    will allow only frequencies below 15 Hz to pass trough. The filter order of 4 indicates a fourth degree polynomial transfer function.

4. When you click the `Remove Offset` button, the reference signal's offset will be removed according to the values specified in the `Offset Value` and `Automatic Offset` textboxes. In example, specifying

    ```Python
    Offset Value : 4
    Automatic: 0
    ```
    will result in an offset correction by -4 in y-axis direction. Furthermore, specifying

    ```Python
    Offset Value : 0
    Automatic: != 0
    ```
    will result in automatic offset removal. Moreover, specifying

    ```Python
    Offset Value : 0
    Automatic: 0
    ```
    will allow you to manually correct the offset in a new pop-up plot. You just need to follow the instructions on the plot. 

## Resize EMG File
Sometime, resizing of you analysis file in unevitable. Luckily, *openhdemg* provides an easy solution. In row five and column 2 in the left side of the GUI, you can find the `Resize File` button. 

1. View the MUs using the `View MUs` button prior to file resizing, you can directly see what is happening.

2. Clicking the `Resize File` button will open a new pop-up plot of your analysis file. 

3. Follow the instructions in the plot to resize the file. Simply click in the signal twice (once for start-point, once for end-point) to specify the resizing region and press enter to confirm your coice.

## Analyse Force Signal
In order to analyse the force signal in your analysis file, you can press the `Analyse Force` button located in row six and column one in the left side of the GUI. A new pop-up window will open where you can analyse the maximum voluntary contraction (MVC) value as well as the rate of force development (RFD). 

### Maximum voluntary contraction
In order to get the MVC value, simply press the **Get MVC** button. A pop-up plot opens and you can select the area where you suspect the MVC to be. Click once to specify the start-point and once to specify the end-point. Press enter to confirm you choice. You will then see a `Result Output` appearing at the bottom of the main window of the GUI. There you can find the actual result of your MVC analysis. You can edit or copy any value in the `Result Output`, however, you need to close the top-level `Force Analysis Window` first.

### Rate Of Force Development
To calculate the RFD values you can press the **Get RFD** button. A pop-up plot appears and you need to specify the starting point of the rise in the force signal by clicking and subsequenlty pressing enter. The respective RFD values between the stated timepoint ranges (ms) in the `RFD miliseconds` textinput are displayed in the `Result Output`. In example, specifying

```Python
RFD miliseconds: 50,100,150,200
```
will result in RFD value calculation between the intervals 0-50ms, 50-100ms, 100-150ms and 150-200ms. You can also specify less or more values in the `RFD miliseconds` textbox. You can edit or copy any value in the `Result Output`, however, you need to close the top-level `Force Analysis Window` first.

## Motor Unit Properties
When you press the **MU Properties** button in row six and column two, the "Motor Unit Properties" Window will pop up. In this window, you have the option to analyse several MUs propierties such as the MUs recruitement threshold or the MUs discharge rate. However, first you **must** specify your priorly calculated MVC in the `Enter MVC [N]:` textbox, like

```Python
Enter MVC [N]: 4242
```
### Compute Motor Unit Threshold
Subsequently to specifying the MVC, you can compute the MUs recruitement threshold by specifying the respective event and type in the `Event` and `Type` dropdown list. Once you click the **Compute threshold** button, the recruitement threshold will be computed. 

From the `Event` dropdown you can choose: 
```Python
"rt_dert" : Both recruitment and derecruitment tresholds will be calculated.
"rt" : Only recruitment tresholds will be calculated.
"dert" : Only derecruitment tresholds will be calculated.
```
From the `Type` dropdown you can choose:
```Python
"abs_rel" : Both absolute and relative tresholds will be calculated.
"rel" : Only relative tresholds will be calculated.
"abs" : Only absolute tresholds will be calculated.
```
The recruitement threshold for each inluded MU in the analysis file will be displayed in the `Result Output` of the GUI.
You can edit or copy any value in the `Result Output`, however, you need to close the top-level `Motor Unit Properties Window` first.

### Compute Motor Unit Discharge Rate
Subsequently to specifying the MVC, you can comput the MUs discharge rate by entering the respective firing rates and event.
First, you need to specify the number of firings at recruitment and derecruitment to consider for the calculation in the `Firings at Rec` textbox. Secondly, enter the start and end point (in samples) of the steady-state phase in the `Firings Start/End Steady` textbox. Lastly you need to specify the computation `Event`. Once you press the **Compute discharge rate** butten, the discharge rate will be calculated. In example, 

```Python
Firings at Rec: 4
Firings Start/End Steady: 10
```
In case where `Firings Start/End Steady` smaller zero, you have to manually choose the start and end of the steady-state phase.
```Python
Firings at Rec: 4
Firings Start/End Steady: -1
```

From the `Event` dropdown list, you can choose:

```Python
"rec_derec_steady" : Discharge rate is calculated at recruitment, derecruitment and during the steady-state phase.
"rec" : Discharge rate is calculated at recruitment.
"derec" : Discharge rate is calculated at derecruitment.
"rec_derec" : Discharge rate is calculated at recruitment and derecruitment.
"steady" : Discharge rate is calculated during the steady-state phase.
```

The discharge rate for each inluded MU in the analysis file at the stated event as well a for all the contraction will be displayed in the `Result Output` of the GUI. You can edit or copy any value in the `Result Output`, however, you need to close the top-level `Motor Unit Properties Window` first.

### Basic Motor Unit Properties
Subsequently to specifying the MVC, you can calculate a bunch of basic MUs properties with one click. These include

- The absolute/relative recruitment/derecruitment thresholds
- The discharge rate at recruitment, derecruitment, during the steady-state phase and during the entire contraction
- The coefficient of variation of interspike interval
- The coefficient of variation of force signal

and are all displayed in the `Result Output` once the analysis in completed. 
In order to start the analysis, specify the number of firings at recruitment and derecruitment to consider for the calculation in the `Firings at Rec` textbox. Then, enter the start and end point (in samples) of the steady-state phase in the `Firings Start/End Steady` textbox. In example, 

```Python
Firings at Rec: 4
Firings Start/End Steady: 10
```
In case where `Firings Start/End Steady` smaller zero, you have to manually choose the start and end of the steady-state phase.
```Python
Firings at Rec: 4
Firings Start/End Steady: -1
```

The basic MUs properties will be displayed in the `Result Output` of the GUI. You can edit or copy any value in the `Result Output`, however, you need to close the top-level `Motor Unit Properties Window` first.

## Plot Motor Units
In *openhdemg* we have implemented options to plot your analysis file ... a lot of options!
Upon clicking the **Plot MUs** button, the "Plot Window" will pop up. In the top right corner of the window, you can find an information button forwarding you directly to some tutorials. You can choose between the follwing plotting options

- Plot the raw emg signal. Single or multiple channels. (Plot EMGSig)
- Plot the reference signal. (Plot RefSig)
- Plot all the MUs pulses (binary representation of the firings time). (Plot MUPulses)
- Plot the impulse train per second (source of decomposition). (Plot IPTS)
- Plot the instantaneous discharge rate (IDR). (Plot IDR)
- Plot the differential derivation of the raw emg signal by matrix column. (Plot Derivation)
- Plot motor unit action potentials (MUAP) obtained from spike-triggered average from one or multiple MUs. (Plot MUAP)

Prior to plotting you can **optionally** select a few options on the left side of the `Plot Window`. When you want the reference signal to be displayed in the plots you can select the `Reference Signal` checkbox in row one and column two in the left side of the `Plot Window`. Moreover, you can specify wheter you want the x-axis of the plots to be scaled in seconds by selecting the `Time in seconds` checkbox in row two and column two in the left side of the `Plot Window`. You can change the size of the plot as well, by inputting your prefered height and width in the `Figure in size in cm (h,w)` textbox in row three and column two in the left side of the `Plot Window`. For example, if you want your plot to have a height of 6 and a width of 8, your input should look like this

```Python
Figure in size in cm (h,w): 6,8
```

These three setting options are universally used in all plotting options. There are two more specification options on the right side of the `Plot Window` only relevant when using the **Plot Derivation** or **Plot MUAP** buttons. The `Matrix Code` must be specified in row one and column four in the right side of the `Plot Window` according to the one you used during acquisition. So far, the codes 
- `GR08MM1305`
- `GR04MM1305`
- `GR10MM0808`
are implemented. You must choose one from the respective dropdown list.
Furthermore, you need to specify the `Orientation` in row two and column four in the left side of the `Plot Window`. The `Orientaion` must match the one of your matrix during acquisition. You can find a reference image for the `Orientation` at the bottom in the right side of the `Plot Window`. 
Keep in mind that these settings, `Matrix Code` and `Orientation`, are **ignored** when analysing `DEMUSE` files. 

### Plot Raw EMG Signal
Clicking the **Plot EMGsig** button in row four and column one in the left side of the `Plot Window`, you can plot the raw emg signal of your analysis file. However, you first need to enter or select a `Channel Number` in / from the dropdown list. For example, if you want to plot `Channel Number` one enter *1* in the dropdown. If you want to plot `Channel Numbers` one, two and three enter *1,2,3* in the dropdown. Once you have clicked the **Plot EMGsig** button, a pop-up plot will appear. 

### Plot Reference Signal 
Clicking the **Plot RefSig** button in row five and column one in the left side of the `Plot Window`, you can plot the reference signal of your analysis file or any other loaded reference sinal for that matter. Once you have clicked the **Plot RefSig** button, a pop-up plot will appear. 

### Plot Motor Unit Pulses
Clicking the **Plot MUpulses** button in row six and column one in the left side of the `Plot Window`, you can plot the single pulses of the MUs in your analysis file. However, you first need to enter/select a pulse `Linewidth` in/from the dropdown list. For example, if you want to use a `Linewidth` of one, enter *1* in the dropdown. Once you have clicked the **Plot MUpulses** button, a pop-up plot will appear. 

### Plot Impulse Train Per Second
Clicking the **Plot IPTS** button in row seven and column one in the left side of the `Plot Window`, you can plot the IPTS of the MUs in your analysis file. However, you first need to enter/select a `MU Number` in/from the dropdown list. For example, if you want to plot the IPTS of `MU Number` one enter *1* in the dropdown. If you want to plot the IPTS of `MU Number` one, two and three enter *1,2,3* in the dropdown. You can also set `MU Number` to "all" to plot the IPTS of all included MUs in the analysis file. Once you have clicked the **Plot EMGsig** button, a pop-up plot will appear. 

### Plot Instanteous Discharge rate
Clicking the **Plot IDR** button in row eight and column one in the left side of the `Plot Window`, you can plot the IDR of the MUs in your analysis file. However, you first need to enter/select a `MU Number` in/from the dropdown list. For example, if you want to plot the IDR of `MU Number` one enter *1* in the dropdown. If you want to plot the IDR of `MU Number` one, two and three enter *1,2,3* in the dropdown. You can also set `MU Number` to "all" to plot the IDR of all included MUs in the analysis file. Once you have clicked the **Plot EMGsig** button, a pop-up plot will appear. 

### Plot Differential Derivation
Clicking the **Plot Derivation** button in row four and column three in the right side of the `Plot Window`, you can plot the differential derivation of the MUs in your analysis file. However, you need to specify the `Configuration` for the calculation first. You can choose from:

- `Single differential` (Calculate single differential of raw signal on matrix rows)
- `Double differential`(Calculate double differential of raw signal on matrix rows)

Furthermore, you are required to specify the respective `Matrix Column` you want to plot. You can choose one from the `Matrix Column` dropdown list. Once you have clicked the **Plot Derivation** button, a new pop-up plot appears. 

### Plot Motor Unit Action Potentials
Clicking the **Plot MUAP** button in row five and column three in the right side of the `Plot Window`, you can plot the action potential of the MUs in your analysis file. However, you need to specify the `Configuration` for  calculation first. You can choose from:

- `Monopolar`
- `Single differential` (Calculate single differential of raw signal on matrix rows)
- `Double differential`(Calculate double differential of raw signal on matrix rows)

Furthermore, you are required to specify the respective `MU Number` you want to plot. You can choose one from the `MU Number` dropdown list. Lastly, you need to specify the `Timewindow` of the plots. You can choose from the `Timewindow` dropdown list or enter an own value. Once you have clicked the **Plot MUAP** button, a new pop-up plot appears. 

## Saving Your Analysis File 
Subsequently to analysing your emg-file in the *openhdemg* GUI, it is beneficial to save it. Otherwise, all changes will be lost when the GUI is closed. To do so, simple press the **Save File** button in row two and column two in the left side of the main window. Once you click the **Save File** button, you need to specify a filename and a location. That's it!

## Saving Your Analysis Results
Some analyses included in the *openhdemg* GUI return values that are displayed in the `Result Output` of the GUI. Of course, you can simply copy-paste them, but it might be more convenient to directly save your analysis results. Plus, all the values in the `Results Output` will be overwritten by new analyses or deleted in case of closing the GUI. To do so, click the **Save Results** button in row two and column two in the left side of the main window. Once you clicked the **Save Results** button, specify a location where to save the file. You can find the file there with the name of your analysis file. 

## Resetting Your Analysis 
We all make mistakes! But, most likely, we are also able to correct them. In case you have made a mistake in the analysis of you emg-file in the *openhdemg* GUI, we have implemented a reset button for you. Clicking the `Reset Analysis` button in row eight and column two in the lef side of the main window will reset any analysis you previously performed since opening the GUI and inputting an analysis file. Your analysis file is resetted to file you have inputted and all changes are revoked. So, no need to be perfect!

--------------------------------------------

We hope you had fun! We are now at the end of describing the basic functions included in the *openhdemg* GUI. In case you need further clarification, don't hesitate to post a question in the Github discussion forum (LINK). Moreover, if you noticed an error that was not properly catched by the GUI, please file a bug report according to our guidelines (LINK).
If you want to proceed to the advanced stuff now, take a look at the [advanced](GUI_advanced.md) tab on the left side of the webpage. 
