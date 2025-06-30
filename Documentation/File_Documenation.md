# General Documentation for the `File` object
About: A `File` is the main data-storing object that the `TransistorDataVisualizer` package uses to store data in a plottable way. It is created using a `DataFile`. It is the base class that the more robust `DataSet` class is built upon. 

## When to use a `File`
The `File` should rarely be used by itself as the `DataSet` object has more functionality. However, if one wants to quickly test the validity of a `DataFile` or CSV file, creating a `File` and using its `quick_plot3d()` method is a good idea. 

### Example:
Say you have two `DataFile`s whose validity you want to test. `datafile1` may have a bad path and `datafile2` may be a strange CSV file itself. To make quick visual confirmation as to whether the datafiles make sense, you may want to create two `File` objects and quickly plot their contents:
```
import TransistorDataVisualizer as tdv

File1 = tdv.File(datafile1)
File2 = tdv.File(datafile2) 

File1.quick_plot3d()
File1.quick_plot3d()
```

## Creating a `File`
A `File` is created through initialization with `DataFile` which contains the `file_name` and a `file_path` to the easyEXPERT csv file. To learn more about the `DataFile` and how to configure it properly, see the `DataFile_Documentation.md`. Simply reading the CSV file is not enough, however. There are additional functions that make everything work. They are "hidden" from users (via the `__` symbols before the function name) as users should never be calling these functions themselves. Unless your curious, you can ignore the 'Hidden Stuff' section which explores the file parsing. 

The `File`'s job is generate usable data (in `numpy` array form) from   easyEXPERT data export CSV. To do this involves several steps. First, a `DataFile` object is passed into the initialization call to the `File` object. From this, the file’s path and specified name (which is a unique identifier that determines how it’s processed by a later object, specifically the `DataSet`) are gathered into the `File` object in its init call. The other object attributes are also initialized, later to be changed by the coming method calls. Several hidden functions are then called, and the `File` is full of data and ready to use!

### Example: Creating a `File` from an imported `DataFile`
```
import TransistorDataVisualizer as tdv
import TransistorDataFiles as fls

F = tdv.File( fls.It7 )
```

### Example: Creating a `File` using a user-created `DataFile`
```
import TransistorDataVisualizer as tdv

DF = tdv.DataFile('Rb10', r'C:\FAKEPATH\Fake_ResistanceTest_BottomGate_Device10.csv')

F = tdv.File( DF )
```

## Indices of a `File` Object/Indexing a `File` Object's Data
In many instances, you will be asked to provide an index for a `File` method. You may want to consider using the `DataSet`'s `print_indices()` function. If you can't, you can use `get_headers()`, which will give you the headers of the `File`. Each index of the header corresponds the appropriate index. 

### Example:
```
TransistorDataVisualizer as tdv
# assume DF is a DataFile
F = tdv.File( DF )
F.get_headers()
```

## Plotting
```
TransistorDataVisualizer as tdv
# assume DF is a DataFile
F = tdv.File( DF )
F.quick_plot3d(Zindex=-1, connector = True)
```

# Hidden stuff
This explains how the CSVs are parsed by the hidden member methods of the `File` object. The most important function is `__check_missing_dims()`. The way `__check_missing_dims()` works is as follows. The `File` will have a member dictionary named `m_datadict` that stores all the data. It will also have the member variable `m_headers`, which stores the keys of `m_datadict` in an ordered way so integer indexing can be utilized with the data dictionary. The initial form of `m_headers` will only have the variables listed by the easyEXPERT file, which may exclude independent variables reported in the interval information. 

The issue arises where not all utilized variables are counted. The total set of variables represented by the total set of dictionary keys (which we will call **K**) is intialized to the set of keys from `m_headers`, which we will notate as **H**. When the program initially runs through the `__process_csv` functions **K** = **H**; however the set of independent variales keys (aka interval keys) **I** may not exist within **K**. In other words, at initialization (before running the `__check_missing_dims()` function), we must assume **I**∉**K**. We want it such that **I**∈**K**∧**H**∈**K**. Once this criterion is met, then we set **H** = **K** and we have then successfully accounted for all variables, independent and dependent, in the data set. 


## __process_csv(self, input_file)
This function scans through the easyEXPERT csv and collects pertinent information of the eE test. It will collect the following attributes directly:
* `m_sweep_type`: The type of sweep the machine it says it’s doing.
* `m_dim1_count`: The integer count of data points collected on the 1st independent variable’s domain. Ei. If only 2 distinct voltages were used for the sweep, this quantity would be equal to 2.  
* `m_dim2_count`: The integer count of data points collected on the 2st independent variable’s domain.
* `m_title`: The actual title of the named test being ran by the machine. 
* `m_shape`: The (row, column) numpy shape of the objects. It is initially set equal to (`m_dim1_count`, `m_dim2_count`).
* `m_headers`: The column headings for the data. 
A primitive form of m_datadict is created for later fleshing out by the functions `reshape_data()` and `__check_missing_dims()`. 
`m_datadict` is a dictionary of numpy arrays of length `m_dim1_count * m_dim2_count` into which each column of data is collected. 

## __process_TestParameters(self, row)
Additionally, `__process_csv(self, input_file)` also calls the function `__process_TestParameters(self, row)`.
This function collects the information of the primary and secondary independent variables used in the sweep. These variables contain the CSV's `start`, `stop`, and either `count` (integer count of discrete points in the `start` to `stop` domain) or the `step` (which may be given) for each independent sweep variable. An intermediate `m_intervals` is created by `__process_TestParameters(self, row)`. 


## __process_interval(self)
The `__process_interval()` function creates `m_intervals`, a dictionary of 1D `numpy.array` intervals with the independent variable names as the keys. The `__process_interval()` function constructs the interval `m_intervals` from the `start`, `stop`, and either `count` (integer count of discrete points in the `start` to `stop` domain) or the `step` (which may be given). These prerequisite variables were collected from the `__process_TestParameters(self, row)` function. These intervals are 1D  `numpy` arrays of the independent variables.

Now, `m_intervals` determines the discrete domains of the 1st and 2nd independent variables and represent them as key-value pairs in a dictionary, with the key being the name of the independent variable and the value being the discrete domain represented via a `numpy` array (e.g. `{'Rd': np.array(0.02)}`. The domain will be of the form `[start, start + step, start + 2*step, … , stop – step, stop]`, after `__process_interval(self)` finishes creating its interval. `__check_missing_dims(self)` uses this information to the create meshgrids with the appropriate test dimensions if the independent variables are missing the appropriate dimensions. 

## __check_missing_dims(self)
Finally, `__check_missing_dims(self)` will verify everything and correct any issues. It compares the set of `m_intervals` **I** to the set of `m_headers` **H**, and if **H** is missing one of the independent variables from **I**, a `numpy` meshgrid is created using `m_intervals` to generate the missing 2D data of the absent independent variable. The meshgrid is created from the 1D `numpy` arrays so the newly replaced missing data has the dimensions matching the test it came from. And tada, we're done!




