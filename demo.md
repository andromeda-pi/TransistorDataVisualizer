# TransistorDataVisualizer Demo
This file serves as a demonstration of `TransistorDataVisualizer` (`tdv`). For a more information, checkout the [thesis][https://ir.library.oregonstate.edu/concern/undergraduate_thesis_or_projects/jq085v314]!

To run the demo, in the terminal, navigate to the folder in which this package located and run the command:
```python demo.py```
Have fun!

# demo.py
The following is simply `demo.py`, just formatted here for readability.

## common imports
import the main package using the method shown below imports all doc strings and in-editor documentation, which is very useful!
```
from TransistorDataVisualizer import *
```
If you want to import the file mappings, use ```import TransistorDataFiles as fls```. 
You will need to set it up first, however. To provide you with a demo that works without additional fuss, we will omit this step.
To set up the TransistorDataFiles file import, you will need to configure your file path in that file and resave it.

# Data Structures of `tdv`
`tdv`` has several data structures that work as the following:

## DataFile demo
DataFile: stores the file location and test type for a CSV file
```
test1 = DataFile(code='Ib7', path=r"Id-Vds var const Vbgs_n1.csv")
test2 = DataFile('It7', r"Id-Vds var const Vtgs_n1.csv")
```
Be careful to make sure the string is properly formatted. Beware that `'\'` may be interpreted as an escape character to prevent this, either use a raw string (eg. `r'\'`) or use an escape character for backslash (eg. `'\\'`).

## File demo
File: turns a DataFile into a plottable object, but with limited plotting funcitonality; only `.quick_plot3d()`
```
File1 = tdv.File(test1)
File1.quick_plot3d(Zindex = -1) # the selected Zindex selects what gets plotted on the Z axis based on the indices from the CSV file
```

## DataSet: turns a DataFile into a useful plottable object and has 1 main function: quick_plot3d()
S1 = DataSet(test1)
S2 = DataSet(test2)

S1.quick_plot3d(-1) 

## DataBank demo
You can use the .append() and .pop() methods to add or remove DataSets from the DataBank
```
B = DataBank()
B.append(S1) 
```

You can check what is in your DataBank using its print function:
```B.print()```

### Plotting
Of course, plotting with the `DataBank` is the main appeal! 


#### quick_plot3d()
You can run use quick_plot3d() to visualize the data in 3D. To add connectors (on by default with the `File` and `DataSet`), toggle it by setting `B.connectors = True`.
To have labels automatically generated, toggle it using `B.autolabels = True`.
```B.quick_plot3d(-1)```
    
#### quick_plot2d()
You can use the `quick_div2d()`` function to make a 2D plot of the `DataBank`'s data.
```B.quick_plot2d('x', -1)```

#### quick_div_plot3d()
You can compare performance across devices using the `quick_div_plot3d()` function:
```B.quick_div_plot3d(S2, -1)```

### Domain Restriction    
You can also restrict the domain that's being plotted
```
B.domain
B.set_domain('x', [0, 5])
B.set_domain('y', [0, 3])
B.domain

B.quick_plot3d()
B.quick_plot2d('x', -1)
B.quick_div_plot3d(S2, -1)

B.reset_domain()# You can reset the domain via the reset function
B.domain
```

### override setting
You can add more things too. When attempting to append more `DataSet`s, you may encounter an error describing a mismatching gate. 
```B.append(S2)```

The mismatching gate type error come when we're attempting to add two files of different test types. We can override this to bypass it (it may make the labels strange though).
```
B.override = True
B.append(S2)

B.quick_plot3d()
```

## Plotter demo
The Plotter has more functions, including the new `quick_div_plot2d()` function and the `cmap_quick_plot3d()` function. Both of these support `kwarg` parameters. Additionally, the `Plotter` supports `Matplotlib` colormaps!
There are additional features added by the Plotter object, but this demo won't go into it heavily. For examples of that, check out the thesis's Appendix A.

### colormap example
```
P = Plotter(S1)
P.quick_plot2d('x', -1, cmap='cool') # creates a 2D plot with 'cool' colormapping
```

### quick_div_plot2d example
Create a relative performance plot in 2D comparing S1 to S2 using 'coolwarm' colormapping (also, turn make it a scatter plot so we don't have to see those lines):

```
P.scatter_plots = True
P.quick_div_plot2d('x', -1, S2, -1, cmap='coolwarm')
```

### domain restriction in `Plotter`
The new plots work with colormaps, naming, and domain restriction. It makes things look really good, take a look!
```
P.scatter_plots = False # use curves instead of scatter plots
P.set_domain('x', [0,5]) # restrict the domains
P.set_domain('y', [0,4])
P.set_name(r'Drain Current $I_D$ Sweep') # set the Plotter title to this
P.set_names('dims') # set DataSet names to the dimensions
```