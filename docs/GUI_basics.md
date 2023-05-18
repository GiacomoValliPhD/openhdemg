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



