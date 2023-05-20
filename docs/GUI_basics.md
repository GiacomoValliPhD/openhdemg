# Graphical Interface

This is the basic introduction to the *openhdemg* GUI. In the next few sections, we will go through the basic analysis functions embedded in the GUI. For the advanced stuff, take a look at the "advanced" chapter on the left side of the webpage. We will start with how to sort the motor units included in your analysis file, go over force and motor unit property analysis and take a look at how to save and reset your analysis.

## Motor Unit Sorting
To sort the motor units included in your analysis file in order of their recruitement, we implemented a sorting algorithm. The motor units are sorted based on their recruitement order in an ascending manner. On the left hand side in the main window of the GUI, you can find the **Sort MUs** Button. It is located in row three, column two. Once you press the button, the motor units will be sorted. Pay attention to view to motor units first, using the **View MUs** button next to the **Sort MUs** button (we explained this button in the "intro" chapter). The motor units will be sorted anyways, but without viewing them you won't see what is happening. Moreover, sorting the motor units is only possible when a file is loaded, so don't forget to do that. 

## Remove Motor Units
To remove motor units included in your analysis file, you can click the **Remove MUs** button. The button is located on the left hand side in the main window of the GUI in column one of row four. Once you click the **Remove MUs** button, and a file is loaded, a pop-up window will open. You can select the motor unit you want to delete from the analysis file or you can enter the number of several motor units in case you want to delete more than one. In example, selecting

```Python
Select MU: 1
```
will result in the first motor unit to be deleted. Selecting 

```Python
Select MU: 1,2,5
```
will result in the removal of the first, second and fifth motor unit. When you view the motor units using the **View MUs** button prior to motor unit removal, you can directly see what is happening.

## Reference Signal Editing
The *openhdemg* GUI also allows you to edit and filter reference signals corresponding to your analysis file (however, you can also edit and filter seperate reference signals). By clicking the **RefSig Editing** button located in row five and column one, a new pop-up window opens. In the "Reference Signal Editing Window", you can low-pass filter the reference signal as well as remove any signal offset. 
When you click the **Filter RefSig** button, the reference signal gets low-pass filtered according to values specified in the "Filter Order" and "Cutoff Freq" textboxes. In example, specifiying 

```Python
Filter Order: 4
Cutoff Freq: 15
```
will allow only frequencies below 15 Hz to pass trough. The filter order of 4 indicates a fourth degree polynomial transfer function.

When you click the **Remove Offset** button, the reference signal's offset will be removed according to the values specified in the "Offset Value" and "Automatic Offset" textboxes. In example, specifying

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
will allow you to manually correct the offset in a new pop-up plot. You just need to follow the instructions on the plot. When you view the motor units using the **View MUs** button prior to reference signla editing, you can directly see what is happening.

## Resize EMG File
Sometime, resizing of you analysis file in unevitable. Luckily, *openhdemg* provides an easy solution. In row five and column 2 in the left side of the GUI, you can find the **Resize File** button. Clicking this butten will open a new pop-up plot of your analysis file. You can follow the instructions in the plot to resize the file. Simply click in the signal twice (once for start-point, once for end-point) to specify the resizing region and press enter to confirm your coice. When you view the motor units using the **View MUs** button prior to file resizing, you can directly see what is happening.

## Analyse Force Signal
In order to analyse the force signal in your analysis file, you can press the **Analyse Force** button located in row six and column one in the left side of the GUI. A new pop-up window will open where you can analyse the maximum voluntary contraction (MVC) value as well as the rate of force development (RFD). 
### Maximum voluntary contraction
In order to get the MVC value, simply press the **Get MVC** button. A pop-up plot opens and you can select the area where you suspect the MVC to be. Click once to specify the start-point and once to specify the end-point. Press enter to confirm you choice. You will then see a "Result Output" appearing at the bottom of the main window of the GUI. There you can find the actual result of your MVC analysis. You can edit or copy any value in the "Result Output", however, you need to close the top-level "Force Analysis Window" first.
### Rate Of Force Development
To calculate the RFD values you can press the **Get RFD** button. A pop-up plot appears and you need to specify the starting point of the rise in the force signal by clicking and subsequenlty pressing enter. The respective RFD values between the stated timepoint ranges (ms) in the "RFD miliseconds" textinput are displayed in the "Result Output". In example, specifying

```Python
RFD miliseconds: 50,100,150,200
```
will result in RFD value calculation between the intervals 0-50ms, 50-100ms, 100-150ms and 150-200ms. You can also specify less or more values in the "RFD miliseconds" textbox. You can edit or copy any value in the "Result Output", however, you need to close the top-level "Force Analysis Window" first.

## Motor Unit Properties
When you press the **MU Properties** button in row six and column two, the "Motor Unit Properties" Window will pop up. In this window, you have the option to analyse several MUs propierties such as the MUs recruitement threshold or the MUs discharge rate. However, first you **must** specify your priorly calculated MVC in the "Enter MVC [N]:" textbox, like

```Python
Enter MVC [N]: 4242
```
### Compute Motor Unit Threshold
Subsequently to specifying the MVC, you can compute the MUs recruitement threshold by specifying the respective event and type in the "Event" and "Type" dropdown list. Once you click the **Compute threshold** button, the recruitement threshold will be computed. 

From the "Event" dropdown you can choose: 
```Python
"rt_dert" : Both recruitment and derecruitment tresholds will be calculated.
"rt" : Only recruitment tresholds will be calculated.
"dert" : Only derecruitment tresholds will be calculated.
```
From the "Type" dropdown you can choose:
```Python
"abs_rel" : Both absolute and relative tresholds will be calculated.
"rel" : Only relative tresholds will be calculated.
"abs" : Only absolute tresholds will be calculated.
```
The recruitement threshold for each inluded motor unit in the analysis file will be displayed in the "Result Output" of the GUI.
You can edit or copy any value in the "Result Output", however, you need to close the top-level "Motor Unit Properties Window" first.

### Compute Motor Unit Discharge Rate
Subsequently to specifying the MVC, you can comput the MUs discharge rate by entering the respective firing rates and event.
First, you need to specify the number of firings at recruitment and derecruitment to consider for the calculation in the "Firings at Rec" textbox. Secondly, enter the start and end point (in samples) of the steady-state phase in the "Firings Start/End Steady" textbox. Lastly you need to specify the computation "Event". Once you press the **Compute discharge rate** butten, the discharge rate will be calculated. In example, 

```Python
Firings at Rec: 4
Firings Start/End Steady: 10
```
In case where "Firings Start/End Steady" smaller zero, you have to manually choose the start and end of the steady-state phase.
```Python
Firings at Rec: 4
Firings Start/End Steady: -1
```

From the "Event" dropdown list, you can choose:

```Python
"rec_derec_steady" : Discharge rate is calculated at recruitment, derecruitment and during the steady-state phase.
"rec" : Discharge rate is calculated at recruitment.
"derec" : Discharge rate is calculated at derecruitment.
"rec_derec" : Discharge rate is calculated at recruitment and derecruitment.
"steady" : Discharge rate is calculated during the steady-state phase.
```

The discharge rate for each inluded motor unit in the analysis file at the stated event as well a for all the contraction will be displayed in the "Result Output" of the GUI. You can edit or copy any value in the "Result Output", however, you need to close the top-level "Motor Unit Properties Window" first.

### Basic Motor Unit Properties
Subsequently to specifying the MVC, you can calculate a bunch of basic MUs properties with one click. These include

- The absolute/relative recruitment/derecruitment thresholds
- The discharge rate at recruitment, derecruitment, during the steady-state phase and during the entire contraction
- The coefficient of variation of interspike interval
- The coefficient of variation of force signal

and are all displayed in the "Result Output" once the analysis in completed. 
In order to start the analysis, specify the number of firings at recruitment and derecruitment to consider for the calculation in the "Firings at Rec" textbox. Then, enter the start and end point (in samples) of the steady-state phase in the "Firings Start/End Steady" textbox. In example, 

```Python
Firings at Rec: 4
Firings Start/End Steady: 10
```
In case where "Firings Start/End Steady" smaller zero, you have to manually choose the start and end of the steady-state phase.
```Python
Firings at Rec: 4
Firings Start/End Steady: -1
```

The basic MUs properties will be displayed in the "Result Output" of the GUI. You can edit or copy any value in the "Result Output", however, you need to close the top-level "Motor Unit Properties Window" first.

### Plot Motor Units
In *openhdemg* we have implemented options to plot your analysis file ... a lot of options!
Upon clicking the **Plot MUs** button, the "Plot Window" will pop up. In the top right corner of the window, you can find an information button forwarding you directly to some tutorials. You can choose between the follwing plotting options

- Plot the raw emg signal. Single or multiple channels. (Plot EMGSig)
- Plot the reference signal. (Plot RefSig)
- Plot all the MUs pulses (binary representation of the firings time). (Plot MUPulses)
- Plot the impulse train per second (source of decomposition). (Plot IPTS)
- Plot the instantaneous discharge rate (IDR). (Plot IDR)
- Plot the differential derivation of the raw emg signal by matrix column. (Plot Derivation)
- Plot motor unit action potentials (MUAP) obtained from spike-triggered average from one or multiple MUs. (Plot MUAP)

Prior to plotting you can **optionally** select a few options on the left side of the "Plot Window". When you want the reference signal to be displayed in the plots you can select the "Reference Signal" checkbox. Moreover, you can specify wheter you want the x-axis of the plots to be scaled in seconds by selecting the "Time in seconds" checkbox. You can change the size of the plot as well, by inputting your prefered height and width in the "Figure in size in cm (h,w)" textbox. For example, if you want your plot to have a height of 6 and a width of 8, your input should look like this

```Python
Figure in size in cm (h,w): 6,8
```

There are two more specification options on the right side of the "Plot Window" and we will get to the later. Let's start with the first plots. 

### Plot Raw EMG Signal
Clicking the **Plot EMGsig** button, you can plot the raw emg signal of your analysis file. However, you first need to enter or select a MU number in / from the dropdown list. For example, if you want to plot MU number one enter *"1"* in the dropdown. If you want to plot MUs number one, two and three enter *"1,2,3"* in the dropdown. Once you have clicked the **Plot EMGsig** button, a pop-up plot will appear. 

### Plot Reference Signal 
Clicking the **Plot RefSig** button, you can plot the reference signal of your analysis file or any other loaded reference sinal for that matter. Once you have clicked the **Plot RefSig** button, a pop-up plot will appear. 

### Plot Motor Unit Pulses