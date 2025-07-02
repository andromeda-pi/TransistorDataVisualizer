# import the main package
from TransistorDataVisualizer import *

# import the file mappings
#import TransistorDataFiles as fls
# if your file setup is different, change it in the above package and resave it

# this is a display of functionality 


# tdv has several data structures that work as the following:
# DataFile: stores the file location and test type for a CSV file
test1 = DataFile(code='Ib7', path=r"Id-Vds var const Vbgs_n1.csv")
test2 = DataFile('It7', r"Id-Vds var const Vtgs_n1.csv")
# be carefule to make sure the string is properly formatted. Beware that '\' may be interpreted as an escape character
#   to prevent this, either use a raw string (eg. r'\') or use an escape character for backslash (eg. '\\')

# File: turns a DataFile into a plottable object, but with limited plotting funcitonality; only .quick_plot3d()
File1 = File(test1)
File1.quick_plot3d(Zindex = -1) # the selected Zindex selects what gets plotted on the Z axis based on the indices from the CSV file

# DataSet: turns a DataFile into a useful plottable object and has 1 main function: quick_plot3d()
S1 = DataSet(test1)
S2 = DataSet(test2)

S1.quick_plot3d(-1) 

# DataBank: the main thingy
B = DataBank()

B.append(S1) # You can use the .append() and .pop() methods to add or remove DataSets from the DataBank
    
B.quick_plot3d(-1) # You can run use quick_plot3d() to visualize the data in 3d
        # to add connectors, toggle it by setting DataBank.connectors = True
        # to have labels automatically generated, toggle it with DataBank.autolabels = True
    
B.quick_plot2d('x', -1) # You can use the .quick_div2d() function to make a 2d plot of the DataBank

B.quick_div_plot3d(S2, -1) # You can compare performance across devices using the .qucik_div_plot3d() function 
    
# You can also restrict the domain that's being plotted
B.domain
B.set_domain('x', [0, 5])
B.set_domain('y', [0, 3])
B.domain

B.quick_plot3d()
B.quick_plot2d('x', -1)
B.quick_div_plot3d(S2, -1)

B.reset_domain()# You can reset the domain vis the reset function
B.domain

# You can also show what is in your DataBank using its print function

B.print()

# You can add more things too
B.append(S2)
# but this will give you a mismatching gate type error because we're adding two files of different test types
# we can override this (it may make the labels strange though)
B.override = True
B.append(S2)

B.quick_plot3d()

# there are additional features added by the Plotter object, but this demo won't go into it.
# For examples of that, check out the thesis's Appendix A.

P = Plotter(S1)
P.quick_plot2d('x', -1, cmap='cool') # creates a 2D plot with 'cool' colormapping

# creates a relative performance plot in 2D comparing S1 to S2 using 'coolwarm' colormapping
# also, turn make it a scatter plot so we don't have to see those lines.
P.scatter_plots = True
P.quick_div_plot2d('x', -1, S2, -1, cmap='coolwarm')

### domain restriction in `Plotter`
# colormaps and domain restriction. It makes things look really good, take a look!

P.scatter_plots = False # use curves instead of scatter plots
P.set_domain('x', [0,5]) # restrict the domains
P.set_domain('y', [0,4])
P.set_name(r'Drain Current $I_D$ Sweep') # set the Plotter title to this
P.set_names('dims') # set DataSet names to the dimensions
P.quick_plot2d('x', -1, cmap='copper', markers=False)
