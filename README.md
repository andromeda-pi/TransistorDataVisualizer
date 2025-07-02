# TransistorDataVisualizer
A Python Library for the Characterization of the Graphene Field-Effect Transistor. 
Check out the [thesis][https://ir.library.oregonstate.edu/concern/undergraduate_thesis_or_projects/jq085v314]!
Check out the documentation for more concise information! 

## Quick Start
Typically, you'll want to import `TransistorDataVisualizer.py` and `TransistorDataFiles.py` which contains the `DataFiles` to create `DataSets` out of. Then, add them to a `Plotter` and begin ploting. 

### Example:
```
from TransistorDataVisualizer import * # import the main package 
import TransistorDataFiles as fls # import the file mappings
# if your file setup is different, change it in the above package and resave it

# select the tests you want:
tests = [fls.It4, fls.It6, fls.It7, fls.It8]

B = DataBank() # then create a DataBank

# then turn all the tests into DataSets and add them to the DataBank
for test in tests:
    B.append( DataSet( test ) )

B.print() # check what is in your bank

# and get the index info to start plotting:
B.print_indices()
```

## Summary of the Data Structures of TransistorDataVisualizer
* `DataFile`: Used to create `File` and `DataSet` objects from CSV files.
* `File`: Used to quickly and unaesthetically plot data for quick checks of data integrity. 
* `DataSet`: Is built on top of a `File` and has more features. Used to store data and configure individual plotting preferences. Has 1 main plotting functions:
    * `quick_plot3d(Zindex:int, connectors:bool = True)`: Plots the data at the selected Zindex against against the x- and y-axes in 3D as a wireframe. Zindex simply corresponds to the data headers in the order they appear. 
* `DataBank`: Can have `DataSets` added or removed via its `append()` or `pop()` methods. It is the old mode for plotting multilpe tests and the following features: plotting, domain restriciton, and some aesthetic changes. 
    For its plotting functions:
    * `quick_plot3d(Zindex)`: Quickly plots data on its selected domain using the Zindex corresponding to each `DataSet`'s headers. 
    * `quick_plot2d(x_idx, y_idx)`: Given the x-axis for a 2d plot and a y-axis (typically conceptualzied as the Zindex for a 3d plot) for a 2d plot, the excluded independent variable is collapsed down and represented in grey-scale.
    * `quick_div_plot3d(DivSet: DataSet, divIdx)`: Creates a plot of the `DataBank` relative to the dividing `DataSet` with additional, potential parameters.   
For more information, see each data structure's section below.  
* `Plotter`: Built upon the `DataBank`. Can have `DataSets` added or removed via its `append()` or `pop()` methods. Is the primary mode for plotting tests and has robust features: plotting, domain restriciton, and colormapping. 
    For its plotting functions:
    * `quick_plot3d(Zindex)`: Quickly plots data on its selected domain using the Zindex corresponding to each `DataSet`'s headers. 
    * `quick_plot2d(x_idx, y_idx,  **kwargs)`: Adds attional functionality to `DataBank`'s `quick_plot2d` function. Has powerful `kwarg`s that enable customization, the most useful one being the `cmap` `kwarg`, enabling usage of `matplotlib` colormaps. 
    * `quick_div_plot3d(DivSet: DataSet, divIdx)`: Creates a plot of the `DataBank` relative to the dividing `DataSet` with additional, potential parameters.   
For more information, see each data structure's section below.
    * `quick_div_plot2d(x_idx, y_idx, DivSet: DataSet, divIdx, **kwargs)`: Combination of `quick_div_plot3d` and `quick_plot2d`. Accepts `cmap` `kwarg`. 
    * `cmap_quick_plot3d(x_idx, y_idx, cmap=None, **kwargs)`: Brings colormapping to 3D!

  Again, check out the documentation for more indepth stuff!

## Providing Function Indices
Many funcitons will ask for an index. The `File` structure of parsed CSV data is as so stored in a datadictionary contaning the data correpsonding to the headers. The the index then is simply the integer index into the headers list. For example:
If `m_headers` = \[independent_variable1, independent_variable2, dependent_variable1, ... dependent_variableN\]
and you want an index `idx` for selecting data, then you will get:
`idx` = 
* 0/'x' = independent_variable1's data
* 1/'y' = independent_variable2's data
* 2 = dependent_variable1's data
* -1 = dependent_variableN's data

When 3d plotting, `Zindex`, the index for to be `Z` axis, should be indexed negatively. 
_If you are unsure of what index you should use, use the `.print_indices()` function._ 

## Demo
Look into the demo! Check out `demo.mk` which explains how to run the demo.

## DataFile: 
Stores the file location and test type for a CSV file.

### DataFile.file_code
Comprised of a character (which denotes test type), another character (denoting gate type) and following numbers (typically transistor number). An example is 'It7' where the first character denotes that the test is a current plot (based on the 'I'), the second character describing that the top gate was used (as shown by the 't') and the last characters showing it was device 7 that was used. 

There are two test types: 'I' for a current test and 'R' for a resistance test.
There are two gate types: 't' for top gate or 'b' for bottom gate operation.
Transistor number: can be anything, but is useful to differentaite tests from eachother.

### DataFile.file_path
The file location in your computer to the CSV file.

### Example
How to load the files 
```
test1 = DataFile(code='Ib7', path=r"Id-Vds var const Vbgs_n1.csv")
test2 = DataFile('It7', "Id-Vds var const Vtgs_n1.csv")
# be careful to make sure the string is properly formatted. Beware that '\' may be interpreted as an escape character in the file path
#   to prevent this, either use a raw string (eg. r'\') or use an escape character for backslash (eg. '\\')
```

## File: 
Turns a DataFile into a plottable object, but with limited plotting funcitonality.

### quick_plot3d(Zindex:int) 
Function to quickly plot the data contained in the File. 

### Example:
```
import TransistorDataVisualizer as tdv

test1 = DataFile(code='Ib7', path=r"Id-Vds var const Vbgs_n1.csv")

File1 = File(test1)
File1.quick_plot3d(Zindex = -1) 
# the selected Zindex selects what gets plotted on the Z axis based on the indices from the CSV file
```

## DataSet
Turns a DataFile into a useful plottable object and has more plotting functionality

### `quick_plot3d(Zindex:int, connectors:bool = True)`
Plots the data at the selected Zindex (typically set as -1) against index 0 (correpsonding to the default x-axis data) and index 1 (corresponding to default y-axis data) in 3D. The data is plotted as a wireframe and if connectors = True, all data points are connected; otherwise, the data is represented as points (which is more accurate to the tests). Zindex simply corresponds to the data headers in the order they appear. 

#### Example:
```
test1 = DataFile('Ib7',r"Id-Vds var const Vbgs_n1.csv")
S1 = DataSet(test1)
S2 = DataSet(test2)

S1.quick_plot3d(-1) 
```

# DataBank
The main feature of the tdv package. The DataBank is used to store and plot multiple DataSets against eachother. 

### Adding/Removing DataSets to the DataBank
Use the `.append()` or `.pop()` methods

### print()
You can also show what is in your DataBank using its `.print()` function.

### print_indices()


## Plotting

### `quick_plot2d(x_idx, y_idx)`
Given the x-axis for a 2d plot and a y-axis (typically conceptualzied as the Zindex for a 3d plot) for a 2d plot, the excluded independent variable is collapsed down and represented in grey-scale.

#### Example: 
```
# assuming you have a preexisting DataBank called 'B'

B.quick_plot2d(0, -1) # will plot the last dependent variable against the default x-axis. 
# Alternative syntax can be used:
B.quick_plot2d('x', -1) # this will be the same plot
```

### `quick_div_plot3d(DivSet: DataSet, divIdx, drop_zeros=True, tolerance: float = -1, Zindex=-1)`
Creates a plot of the `DataBank` relative to the dividing `DataSet`. Divides all the `DataBank`'s `DataSet`s by the dividing `DataSet` called `DivSet` using the `DivSet`'s Zindex called the `divIdx`. If `drop_zeros` is `True`, columns/rows of zeros within the set `tolerance` (which can be specified) are dropped before being plotted.   

### `quick_plot3d(Zindex:int = -1)`
Plots the data at the selected Zindex (automatically set as -1) against index 0 (correpsonding to the default x-axis data) and index 1 (corresponding to default y-axis data) in 3D as a wireframe with (if connectors = True). Zindex simply corresponds to the data headers in the order they appear. 

#### Example:
```
B = DataBank()

B.append(S1) # You can use the .append() and .pop() methods to add or remove DataSets from the DataBank
    
B.quick_plot3d(-1) # You can run use quick_plot3d() to visualize the data in 3d
        # to add connectors, toggle it by setting DataBank.connectors = True
        # to have labels automatically generated, toggle it with DataBank.autolabels = True
    
B.quick_plot2d('x', -1) # You can use the .quick_div2d() function to make a 2d plot of the DataBank

B.quick_div_plot3d(S2, -1) # You can compare performance across devices using the .qucik_div_plot3d() function 
```

### Domain Restriction
You can also restrict the domain that's being plotted on. The DataBank has a 'domain' attribute that can be varied (and reset).

#### Example:
```
B.domain # shows default domain
B.set_domain('x', [0, 5])
B.set_domain('y', [0, 3])
B.domain # shows updated domain

B.quick_plot3d()
B.quick_plot2d('x', -1)
B.quick_div_plot3d(S2, -1)

B.reset_domain()# You can reset the domain vis the reset function
B.domain # now the domain is back to its default settings
```



### Override
The databank will need its `override` attribute set to `True` in order to add DataSets of mismatching test type (for instance adding a 'Ib7' test to a DataBank containing a 'It7' test)

#### Example:
```# You can add more things too
B.append(S1)
B.append(S2)
# but this will give you a mismatching gate type error because we're adding two files of different test types
# we can override this (it may make the labels strange though)
B.override = True
B.append(S2)

B.quick_plot3d()
```

## Plotter
For the best information on the `Plotter`, which is the most complete and useful object in the `tdv` library, please check out its documentation in the documentation folder. It will be worth your time!
