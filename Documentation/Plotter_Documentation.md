# Plotter
The main feature of the tdv package. The Plotter is used to store and plot multiple DataSets against eachother simultanously. It has access to colormapping, which is useful for keeping track of variable values in 2D. 
It has 5 main functions: 
* `quick_plot3d()`: Plots data in 3D.
* `quick_plot2d()`: Plots data in 2D. Can accept colormaps for coloring using `cmap=` `kwarg`.
* `cmap_quick_plot3d()`: Plots data in 3D using a specificed colormap.
* `quick_div_plot3d()`: Plots the quotient of data relative to a baseline `DataSet` in 3D. No colormap support.
* `quick_div_plot2d()`: Plots the quotient of data relative to a baseline `DataSet` in 2D. Supports colormaps via `kwarg` `cmap` argument.

It also has access to two new, plotting methods that the `DataBank` does not have: `cmap_quick_plot3d()` and `quick_div_plot2d()`. 

There are other, non-plotting methods that are demonstrated below the Plotting section. 

## Plotting
The `Plotter` has the most plotting options. The plotting methods are shown in the section after this (and after the example), but first, there are some variables set in the `Plotter` object that effect all plots:
* `scatter_plots: bool = False`: Plots all functions without connecting lines. Can be useful when plotting in 2D with the second independent variable (i.e. `x_idx='y'`). Also, accurately represents the total number of data points the plotted data contains. 
* `show_fig: bool = True`: Determines whether `matplotlib.pyplot.show()` is automatically called during execution of a quick_plot function. If `show_fig` is set to `False`, figures can be saved at higher resolution using [`matplotlib.pyplot.show()`][https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.show.html].
* `auto_labels: bool = True`: Converts supported variables names (e.g. `'Id'`) to their written equivalents (e.g. `r'Drain-Source Current $I_D$ (A)'`). For more info, see the documentation on variable formatting .
* `connectors: bool = False`: 3D quick_plot functions (unless `scatter_plots=True` is toggled) 
* `show_legend: bool = True`: Sometimes that legend obfuscates some of the data, well you can turn it off!
* `override: bool = False`:  Required to be `True` if you want to add `DataSet`s of non-identical `file_code`s to the `Plotter` (i.e. attempting to add data from multiple sweeps where the sweep tests are non-identical). 

#### Example of setting an attribute: the override
The databank will need its `override` attribute set to `True` in order to add DataSets of mismatching test type (for instance adding a 'Ib7' test to a DataBank containing a 'It7' test)
```
# assume S1, S2 are DataSets and P is a Plotter
P.append(S1)
P.append(S2)
# but this will give you a mismatching gate type error because we're adding two files of different test types
# we can override this (it may make the labels strange though)

P.override = True # set the variable DIRECTLY

P.append(S2) # now we can append it and plot
P.quick_plot3d()
```

### `quick_plot3d(Zindex:int = -1)`
The simplest plotting method. Plots data in 3D uses a homogeneous color for each of the `Plotter`'s `DataSet`s according to its `color` attribute. 

Required arguments:
* None

Optional, positional arguments:
* `Zindex: int = -1`: The index that determines what data from the `Plotter`'s `DataSet`s gets plotted along the dependent axis (which is the z-axis in 3D, hence the name).
 
Supported keyword (kwarg) arguments:
* None


#### Example:
```
P = tdv.Plotter(S1) # assume S1 is a DataSet and tdv is the imported TransistorDataVisualizer
P.cmap_quick_plot3d() # produces a 3D plot
```


### `quick_plot2d(x_idx, y_idx, **kwargs)`
Given the x-axis for a 2d plot and a y-axis (typically conceptualzied as the Zindex for a 3d plot) for a 2d plot, the excluded independent variable is collapsed down and represented in monochrome.

Required arguments:
* `x_idx`: the index that will be used as the displayed dependent variable in 2D. The secondary independent variable gets represeted via colorbar.
* `y_idx`: equivalent to `Zindex` for `quick_plot3d()` functions; is the index that determines what data gets plotted along the dependent axis (which is the y-axis in 2D, hence the name). 

Optional, positional arguments:
* None

Supported keyword (kwarg) arguments:
* `cmap: str`: Pass in a supported colormap string for matplotlib's cmap library! I.e. `'coolwarm'`. Otherwise, a monochrome colormap will be created for all `DataSet`s in the `Plotter`, and the colorbar will use the `0`th `DataSet`'s monochrome cmap as its colormap. 
* `cbar: bool`: Toggle whether a colorbar is displayed. Default is `True`. 
* `markers: bool`: Toggle whether `DataSet`s have their markers displayed while plotting. Default is `True`. 
* `discrete: bool`: Toggle whether the colorbar is a gradient (`discrete=False`) or is discrete, which is the default behvarior (`discrete=True`).
* `legend_loc: str`: Identical to `legend_loc` `kwarg` for   matplotlib.pyplot` objects. Default behavior: `legend_loc = 'upper left'`. 
* `figsize: list[float, float]`: Allows scaling of the figure size. Identical to `figsize` for `matplotlib.pypot` objects. Default is close to `(4, 6)`.

#### Example: Basic 2d plotting using quick_plot2d()
```
# assuming you have a preexisting DataBank called 'P'

P.quick_plot2d(0, -1) # will plot the last dependent variable against the default x-axis. 
# Alternative syntax can be used:
P.quick_plot2d('x', -1) # this will be the same plot

P.quick_plot2d('y', -1) # will plot the last dependent variable against the default x-axis.
# Since the 'y' axis is plotted as the main dependent variable, the 'x' axis is represented via colorbar;
#   however, since the 'x' axis (primary sweep variable) often has more data points, a 'y'-axis 2d plot
#   has its data represented as a scatter plot by default.
```

#### Example: Using kwargs with 2d plotting for Plotter
```
# assuming you have a preexisting DataBank called 'P'

P.quick_plot2d('x', -1, cmap='coolwarm') # uses the 'coolwarm' colormap for all DataSets in Plotter

# uses the 'cool' colormap and a discrete colorbar for plotting secondary dependent data
P.quick_plot2d('y', -1, cmap='cool', discrete=True)

# moves legend to the lower right and plots DataSets without their markers according
#   to DataSets' preexisting color settings.
P.quick_plot2d('x', -1, markers=False, legend_loc='lower right') 
```

### `quick_div_plot3d(DivSet: DataSet, divIdx, drop_zeros=True, tolerance: float = -1, Zindex=-1)`
Creates a plot of the all `Plotter`'s contained `DataSet`s relative to the dividing `DataSet`. Divides all the `DataBank`'s `DataSet`s by the dividing `DataSet` called `DivSet` using the `DivSet`'s Zindex called the `divIdx`. If `drop_zeros` is `True`, columns/rows of zeros within the set `tolerance` (which can be specified) are dropped before being plotted.   
Given the x-axis for a 2d plot and a y-axis (typically conceptualzied as the Zindex for a 3d plot) for a 2d plot, the excluded independent variable is collapsed down and represented in monochrome.

Required arguments:
* `DivSet: DataSet`: the index that will be used as the displayed dependent variable in 2D. The secondary independent variable gets represeted via colorbar.
* `divIdx`: the index that determines what data from the `DivSet` will be used as the denominator in calculating the quotient.

Optional, positional arguments:
* `drop_zeros: bool =True`: Toggle whether the rows and columns containing zeros (within the toloerance) in the `DivSet`'s `divIdx`'s data are dropped before division. 
* `tolerance: float = -1`: Allows values of `0` plus or minus the `tolerance` to be dropped before divisino, to prevent division by zero. Default behvaior, if `tolerance=-1`, is that `tolerance=min+varaince` for `DivSet` data.
* `Zindex: int = -1`: The index that determines what data from the `Plotter`'s `DataSet`s gets used as the numerator in creating the quotient. 

Supported keyword (kwarg) arguments:
* None

#### Example:
```
# assume S1 and S2 are initialized DataSets
P = tdv.Plotter(S1) 
P.append(S2)

P.quick_plot3d(-1) # You can run use quick_plot3d() to visualize the data in 3d
        # to add connectors, toggle it by setting DataBank.connectors = True
        # to have labels automatically generated, toggle it with DataBank.autolabels = True

P.quick_div_plot3d(S2, -1) # You can compare performance across devices using the .qucik_div_plot3d() function 
```

### `cmap_quick_plot3d(x_idx, y_idx, cmap:str = None, **kwargs)`
Plots data in 3D using a specificed colormap, or if no colormap specified, uses a monochrome colormap of each `DataSet`'s `color` attribute. 

Required arguments:
* `x_idx`: determines which variable will be treated as the primary independent variable, with the cmap varying according to the secondary independent variable
* `y_idx`: equivalent to `Zindex` for `quick_plot3d()` functions; is the index that determines what data gets plotted along the dependent axis (which is the y-axis in 2D, hence the name). 

Optional, positional arguments:
* `cmap: str`: Pass in a supported colormap string from [matplotlib's cmap library][https://matplotlib.org/stable/users/explain/colors/colormaps.html], i.e. `'coolwarm'`. Otherwise (for default behavior with `cmap=None`), a monochrome colormap will be created for all `DataSet`s in the `Plotter`, and the colorbar will use the `0`th `DataSet`'s monochrome cmap as its colormap. 

Supported keyword (kwarg) arguments:
* `cbar: bool`: Toggle whether a colorbar is displayed. Default is `True`. If you are having errors, a good idea is to turn `cmap=False`, it tends to fix a lot.
* `markers: bool`: Toggle whether `DataSet`s have their markers displayed while plotting. Default is `True`. 
* `discrete: bool`: Toggle whether the colorbar is a gradient (`discrete=False`) or is discrete, which is the default behvarior (`discrete=True`).
* `figsize: list[float, float]`: Allows scaling of the figure size. Identical to `figsize` for `matplotlib.pypot` objects. Default is close to `(4, 6)`.
* `pov: str`: Either `'fowards'` or `'backwards'`. Determines the order in which the curves are plotted. If viewing the curves from behind, curves plotted in the `forward` configuration will behaive strangly, with the furthest-back curves clipping in front of the furthest-forward curves. Ensure that `pov` matches your viewing angle. Defualt is `pov=forward`.
* `view_init: tuple(elevation: float, azimuthal_angle (degrees): float, roll: float)`: Allows changing view intialization for saving high-quality figures! Identical to [MatPlotLib's view_init][https://matplotlib.org/stable/api/toolkits/mplot3d/view_angles.html] variable.

#### Example:
```
# assume S1 and S2 are initialized DataSets and tdv is the imported TransistorDataVisualizer
P = tdv.Plotter(S1) 
P.append(S2)

P.cmap_quick_plot3d('x', -1, 'coolwarm') # produces a 3D plot similar to quick_plot2d using a cmap
```

### `quick_div_plot2d(self, x_idx, y_idx, DivSet:DataSet, divIdx, drop_zeros=True, tolerance: float = -1, cmap:str = None):`
Plots the data at the selected Zindex (automatically set as -1) against index 0 (correpsonding to the default x-axis data) and index 1 (corresponding to default y-axis data) in 3D as a wireframe with (if connectors = True). Zindex simply corresponds to the data headers in the order they appear. 

Required arguments:
* `x_idx`: the index that will be used as the displayed dependent variable in 2D. The secondary independent variable gets represeted via colorbar.
* `y_idx`: the index that determines what data from the `Plotter`'s `DataSet`s gets used as the numerator in creating the quotient. 
* `DivSet: DataSet`: the index that will be used as the displayed dependent variable in 2D. The secondary independent variable gets represeted via colorbar.
* `divIdx`: the index that determines what data from the `DivSet` will be used as the denominator in calculating the quotient.
  
Optional, positional arguments:
* `drop_zeros: bool =True`: Toggle whether the rows and columns containing zeros (within the toloerance) in the `DivSet`'s `divIdx`'s data are dropped before division. 
* `tolerance: float = -1`: Allows values of `0` plus or minus the `tolerance` to be dropped before divisino, to prevent division by zero. Default behvaior, if `tolerance=-1`, is that `tolerance=min+varaince` for `DivSet` data.

Supported keyword (kwarg) arguments:
* None

#### Example:
```
# assume S1 and S2 are initialized DataSets
P = tdv.Plotter(S1) 
P.append(S2)

P.quick_plot3d(-1) # You can run use quick_plot3d() to visualize the data in 3d
        # to add connectors, toggle it by setting DataBank.connectors = True
        # to have labels automatically generated, toggle it with DataBank.autolabels = True

# You can use the .quick_div2d() function to make a 2d plot of the Plotter and color it with a 'Reds' cmap
P.quick_plot2d('x', -1, S1, -1, cmap='Reds')
```


## Non-Plotting Methods
Functions avaiable to the `Plotter` that do not create plots, shown below. 

### Adding/Removing DataSets to the Plotter
Use the `.append()` or `.pop()` methods

### print()
You can also show what is in your DataBank using its `.print()` function.

### print_indices()
The `Plotter` will need often require indices that correspond to data. These indices can be determined by calling the `print_indices()` function.

### Domain Restriction
You can also restrict the domain that's being plotted on. The DataBank has a 'domain' attribute that can be varied (and reset).

#### Example:
```
P.domain # shows default domain
P.set_domain('x', [0, 5])
P.set_domain('y', [0, 3])
P.domain # shows updated domain

P.quick_plot3d()
P.quick_plot2d('x', -1)
P.quick_div_plot3d(S2, -1)

P.reset_domain()# You can reset the domain vis the reset function
P.domain # now the domain is back to its default settings
```

### Changing colors
To change the color the `DataSet` displays when plotted by itself, in a `DataBank`, or in a `Plotter`, there are two options:
* `set_color(int)`: There are 7 preset RGB colors (set for usability with various forms of color blindness). They cycle as follows:
  * `0`: grey,    RGB = `(0.5, 0.5, 0.5)`
  * `1`: magenta, RBG = `(0.863, 0.149, 0.498)`
  * `2`: blue,    RGB = `(0.392, 0.561, 1)`
  * `3`: purple,  RGB = `(0.471, 0.369, 0.941)`
  * `4`: orange,  RGB = `(0.996, 0.38, 0)`
  * `5`: green,   RGB = `(0, 1, 0)` NOTE, this one is NOT set for colorblindness
  * `6`: gold,    RGB `(1, 0.69, 0)`
* `set_colorRGB(list[R:float, G:float, B:float])`: You can set the RGB as a 3-item tuple of floats with values ranging from `0.` to `1.`.

* ## Changing Names
* `set_name(str)` allows you to set the display name of the `Plotter`, which is set as the title of non div-plot plots. 
