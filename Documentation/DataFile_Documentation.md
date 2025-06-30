# Documentation for the `DataFile` object from TransistorDataVisulaizer
The `DataFile` is the current method by which the CSV file path and name is transferred to the `File` and `DataSet` objects, which parse the CSVs to create usable, plottable formualations of the CSV file data.

A `DataFile` is a `Dataclass` (an object with no functions that acts like a data-storage structure exclusively) comprised of 3 parameters: 
* `file_code`: A code used to gather test meta data based on the code given.   
* `file_path`: The file location in your computer to the CSV file.
* `misc`: Used to store miscellaneous info about the test. 

`file_code`: 
Comprised of a character (which denotes test type), another character (denoting gate type) and following numbers (typically transistor number). An example is `'It7'` where the first character denotes that the test is a current plot (based on the `'I'`), the second character describing that the top gate was used (as shown by the `'t'`) and the last characters showing it was device `7` that was used. 

There are two test types: `'I'` for a current test and `'R'` for a resistance test.
There are two gate types: `'t'` for top gate or `'b'` for bottom gate operation. This is referred to as `'gate'` in `DataSet.set_name()`'s accepted keywords. 
Transistor number: for the `DataSet` to fill its `DataInfo` with test metadata, the `'trans_num'` (transistor number) must match the correct device whose information needs to be stored in `devices.json`.  Without the proper `'trans_num'`, no metadata can be automatically loaded. This _can_ be fine, but it offloads a lot of work onto the user. Technically, the transistor number can be anything but is useful to differentiate tests from eachother, and particularly useful for importing metadata for tests. 

### Example: Creating a `DataFile` from a file path and file name
Suppose you have a CSV file named `Id-Vds var const Vbgs_n1.csv` that you want to plot and get a feel for. 
```import TransistorDataFiles as fls
import TransistorDataVisualizer

DF = tdv.DataFile( 'Ib8', r'C:\ABSOLUTE_FILE_PATH\Device8\Id-Vds var const Vbgs_n1.csv' )
F = tdv.File(DF)
F.quick_plot3d(-1)
```
