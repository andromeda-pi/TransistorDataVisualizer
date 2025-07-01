# Documentation for TransistorDataFiles.py (imported as fls)
About: The `TransistorDataFiles.py` file is the current interface between the TransistorDataVisualizer package and the easyEXPERT CSV tests that the KeySight easyEXPERT precision measurement machine produces. 

## Getting Started
You can get a copy of all existing easyEXPERT files via the shared Google Drive.
Once you download the file hierarchy (whose root directory is by default called KeySight_easyEXPERT_dataExport), then you set that location as the `FILEPATH`. From there, all tests can be accessed from an import call. 


### Example: preexisting file mappings
Once your FILEPATH is set, you can import the file (`import TransistorDataFiles as fls`) and now you access to all existing tests that have been mapped. For instance: `fls.It7` will get the path and test type in the `tdv.DataFile` format necessary to begin creating Files and DataSets. If there are new tests, you will need to manually create a `tdv.DataFile` object 

## Setting up FILEPATH Example
Assuming you download the root file directly to the 'E:' drive of your computer, the setup example pathing for what would be as follows:
```
PCPATH = # Example path: 'E:\\KeySight_easyEXPERT_dataExport\\'

FILEPATH = PCPPATH
```
_Be careful to make sure the string is properly formatted._
Beware that '\' may be interpreted as an escape character in the file path to prevent this, either use a raw string (eg. r'\') or use an escape character for backslash (eg. '\\').

### Example: fetching a test and quickly plotting its results:
```
import TransistorDataVisualizer as tdv
import TransistorDataFiles as fls
 
DS1 = tdv.DataSet( fls.It7 )
DS1.quick_plot3d(-1) 
```

## Adding New Files
To add a new test CSV to the list of tests, you will need to create a new `tdv.DataFile` object with a system-interpretable `file_code` and a working `file_path`. For more information, see the `DataFile_Documentaion.md`. 

### Example: Adding a new test
Suppose you just downloaded a new easyEXPERT CSV file and is located in your downloads folder.
To add this test to the list of files in `fls`, create a `DataFile` with the right attribues:
`NewTest = tdv.DataFile( 'It10', r'C:\Users\User\Downloads\Current and top gate device 10')`

### See Also: 
To ensure that the `File` object can properly parse the CSV file provided in the `DataFile` object, check out `File_IO_Documentation.md`  

## Setup gitignore
Once you have your `FILEPATH` set up, it is recommended to add `TransistorDataFiles.py` to `.gitignore` so it doesn't get reset when doing `git pull` for future version releases






