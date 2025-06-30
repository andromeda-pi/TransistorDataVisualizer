# easyEXPERT Variable Formatting for TransistorDataVisualizer Interfacing #

The TransistorDataVisualizer (`tdv`) Python module will take in CSV files produced from the easyEXPERT precision measurment machine, parse the contents, and can then visualize the results via MatPlotLib plots.
But first, the easyEXPERT CSV must have its programmed test variables named very specifically so `tdv` can properly parse the file.

## Cheat Sheet ##
If you are setting up a test in the easyEXPERT Precision Measurement Device, make sure your variables are one of these. Otherwise, `TransistorDataVisualizer` will be unable to automatically parse the easyEXPERT CSV.
These are the possible variables:
* `'Vgs'`: gate-source voltage 
* `'Vtgs'`: top gate source voltage
* `'Vbgs'`: bottom gate source voltage
* `'Vds'`: drain-source voltage
* `'R'` or `'Rds'`: drain-source resistance (called drain resistance or just reistance)
* `'I'` or `'Id'`: drain-source current (called drain current)
* `'Rgs'`: gate-source resistance (not yet implemented)
* `'Igs'`: gate-source current (not yet implemented)

These variable names then get automatically turned into labels if the `DataBank.auto_labels` parameter is set to `True`. The variables then automatically become the following labels.
Variable Name to corresponding Auto-Label output:
* `'Vgs'`, `'Vtgs'`, `'Vbgs'` => 'Gate Voltage $V_{GS}$ (V)': 
* `'Vds'` => 'Drain-Source Voltage $V_{DS}$ (V)'
* `'R'` => 'Resistance $R_D$ (Ω)'
* `'Rk'` => 'Resistance $R_D$ (kΩ)'
* `'I'`, `'Id'` => 'Drain Current $I_D$ (A)'
* `'Im'` => 'Drain Current $I_D$ (mA)'
* `'Iu'` => 'Drain Current $I_D$ (μA)'
* `'Rgs'` => 'Gate-Source Resistance $R_{GS}$' (not yet implemented)
* `'Igs'` => 'Gate-Source Current $I_{GS}$' (not yet implemented)


### Example: Quickly Checking File Variables ###
If you have a easyEXPERT test CSV file and want to know what's in it, you can use Python and `TransistorDataVisualizer` to quickly see what's in the file:
```
import TransistorDataVisualizer as tdv

CSVfile = easyEXPERT_exported_file_name.csv
File = tdv.File(CSVfile)

File.print() # prints the headers and the data shape 
File.print_indices() # will print the index corresponding to each header
```


## Setting Up easyEXPERT Tests ##
Using the tests types below, you can make measurements of the possible variables:
* Independent Variables:
  * Drain-Source Voltage
  * Gate-Source Voltage
* Dependent Variables:
  * Drain-Source Current
  * Drain-Source Resistance = Drain-Source Current / Drain-Source Voltage
  * Gate-Source Current
  * Gate-Source Resistance = Gate-Source Current / Gate-Source Voltage
If you plan to measure any of the above things, be sure to name them according to the right naming convention shown in the Cheat Sheet.


### Test Types: ###
There are types of test that were ran: a current test and a resistance test (which calculates the resistance via Ohm's Law and stores the result).

A current test will consist of 3 tracked variables:
* Drain-Source Voltage
* Gate-Source Voltage
  * Because the graphene field-effect transistor has both a top and bottom gate, you may want to keep track of _what_ gate you are using in a gate-source configuation. 
* Current output (either drain-source or gate-source)
  * this can either be drain-source current or gate-source, but the _assumption_ is that it will be the drain-source current (as that is typically of most interest).

A resistance test will consist of 4 tracked variables
* Drain-Source Voltage
* Gate-Source Voltage
* Current output (either drain-source or gate-source)
* Resistance: the quotient of your selected current and its corresponding voltage
  * eg. Drain-Source Resistance = Drain-Source Current / Drain-Source Voltage


### Example: A 2 Variable Drain Current Test ###
If you want to program a test that measures resistance across the GFET using the top gate configuration, you will use a 2 variable test, track these 3 variables, and create a 4th variable from a combination of the three. Then, you have option of choosing from the following variable names for each.
* drain-source voltage (the first independent variable)
  * `'Vds'`: drain-source voltage
* gate-source voltage (the second independent variable) _You will likely want to track this as the **top gate source voltage**_
  * `'Vtgs'`: top gate source voltage. This option has no ambiguity and should be chosen over the other choice when appropriate. Use with multi-gate transistor tests.
  * `'Vgs'`: gate-source voltage. If you are working with a transistor with only one gate, this is a fine option. **However,** if operating a multi-gate transistor, this option will not keep track of the gate via the `TransistorDataVisualizer` modeul;  _you must track it independently_ (in note book or something).
* drain-source current (the dependent variable)
  * `'Id'`: drain(-source) current. Plots made 
  * `'I'`: (ambiguous) current -> gets interpreted as drain(-source) current. If `I` is selected, the current is automatically assumed to be the drain current. 
  * Note: plots made with `Id` or `I` using the `auto_labels()` funciton will display the name "Drain Current" rather than "Drain Source Current". 
* resistance (calculated variable)
  * `'R'`: (drain-source) resistance. Calculated as the quotient of the drain current and drain-source voltage `R = Id/Vds`. 
When the resulting easyEXPERT CSV is parsed by `TransistorDataVisualizer`, it will be able to parse test parameters properly so you can get to plotting with no issues! 

## File Naming Conventions ##

## How `DataBank.make_auto_labels()` works ##
If you are curious as to _why_ the variables need to be named in the specific way defined by the CheatSheet section, it's because the creation of auto_labels comes from the following function, which requires the specific names:
```
def make_auto_labels(self, xlbl, ylbl, zlbl):
        """Returns automatically created labels from 
        """
        if ylbl in ['Vgs', 'Vtgs', 'Vbgs']:
            ylbl = r'Gate Voltage $V_{GS}$ (V)'
        elif ylbl == 'Vds':
            ylbl = r'Drain-Source Voltage $V_{DS}$ (V)'

        if xlbl in ['Vgs', 'Vtgs', 'Vbgs']:
            xlbl = r'Gate Voltage $V_{GS}$ (V)'
        elif xlbl == 'Vds':
            xlbl = r'Drain-Source Voltage $V_{DS}$ (V)'

        if zlbl == 'R':
            zlbl = r'Resistance $R_D$ (Ω)'
        elif zlbl == 'Rk':
            zlbl = r'Resistance $R_D$ (kΩ)'
        elif zlbl in ['I', 'Id']:
            zlbl = r'Drain Current $I_D$ (A)'
        elif zlbl == 'Im':
            zlbl = r'Drain Current $I_D$ (mA)'
        elif zlbl == 'Iu':
            zlbl = r'Drain Current $I_D$ (μA)'
        lbls = [xlbl, ylbl, zlbl]
        return lbls
```
