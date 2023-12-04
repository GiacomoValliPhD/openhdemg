# Graphical Interface

Welcome, to the *openhdemg* Graphical User Interface (GUI) introduction! 

The *openhdemg* GUI incorporates all relevant high-level functions of the *openhdemg* library. The GUI allows you to successfully perform High-Density Electromyography (HD-EMG) data anlysis **without any programming skills required**. Moreover, there is no downside to using the GUI even if you are an experienced programmer.

The GUI can be simply accessed from the command line with:

```shell
python -m openhdemg.gui.openhdemg_gui
```

-------------------------------------------------

Let us shortly walk you through the main window of the GUI. An image of the starting page of the GUI is displayed below.

![gui_preview](md_graphics/index/gui_preview.png)

This is your starting point for every analysis. On the left hand side you can find all the entryboxes and buttons relevant for the analyses you want to perform. In the middle you can see the plotting canvas where plots of the HD-EMG data analysis are displayed. On the right hand side you can find information buttons leading you directly to more information, tutorials, and more. And, with a little swoosh of magic, the results window appears at the bottom of the GUI once an analysis is finished. 

-------------------------------------------------

## Specifying an analysis file

1. In order to load file into the GUI, you first need to select something in the **Type of file** dropdown box at the top left corner. The available filetypes are:

    - `OPENHDEMG` (emgfile or reference signal stored in .json format)
    - `DEMUSE` (.mat file used in DEMUSE)
    - `OTB` (.mat file exportable by OTBiolab+)
    - `OTB_REFSIG` (Reference signal in the .mat file exportable by OTBiolab+)
    - `DELSYS` (.mat and .txt files exportable by Delsys software)
    - `DELSYS_REFSIG` (.mat file exportable by Delsys software)
    - `CUSTOMCSV` (custom data from a .csv file)
    - `CUSTOMCSV_REFSIG` (Reference signal in a custom .csv file)

    Each filetype corresponds to a distinct datatype that should match the file you want to analyse. So, select the `Type of file` corresponding to the type of your file. In case you selected `OTB`, specify the `extension factor` in the dropdown.

2. To actually load the file, click the **Load File** button and select the file you want to analyse. In case of occurence, follow the error messages and repeat this and the previos step.

3. Once the file is successfully loaded, the specifications of the file you want to analyse will be displayed next to the **Load File** button. 

## Viewing an analysis file

It doesn't get any simpler than this! 

Once a file is successfully loaded as described above, you can click the `View MUs` button to plot/view your file. In the middle section of the GUI, a plot containing your data should appear.

----------------------------------------

In the two sections above, we described the two most rudimental functions in the GUI. To learn more about basic and more advanced analysis features of the GUI, check out the [basic](gui_basics.md) and [advanced](gui_advanced.md) chapters.


## More questions?

We hope that this tutorial was useful. If you need any additional information, do not hesitate to read the answers or ask a question in the [*openhdemg* discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"}. If you are not familiar with GitHub discussions, please read this [post](https://github.com/GiacomoValliPhD/openhdemg/discussions/42){:target="_blank"}. This will allow the *openhdemg* community to answer your questions.
