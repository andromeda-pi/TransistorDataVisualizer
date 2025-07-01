# imports required for everything
import numpy as np
import matplotlib.pyplot as plt

from dataclasses import dataclass # import required for DataFile

# imports required for File
from csv import reader as csvreader
from json import load as jsonload

# imports required for DataSet and DataBank
import matplotlib as mpl
# really, mpl.cm, mpl.ticker, and mpl.colors are used

# imports required for Plotter
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.animation as animation

# ==============================================================================
#               DataFile
# ==============================================================================
@dataclass
class DataFile:
    def __init__(self, code: str, path: str, misc = None):
        ''''''
        self.file_code:str = code
        self.file_path: str = path
        self.misc = misc
        # misc can store any other relevant info, like cryo, epoxy, data quality etc

    def print(self):
        print("File Code Name: ", self.file_code)
        print("File Location: ", self.file_path)
        print(f"Miscellaneous: {self.misc}")

# ==============================================================================
#               File
# ==============================================================================
class File:
    def __init__(self, DataFile: DataFile):
        self.m_headers = []
        self.m_title: str
        self.m_gate_type: str = ''
        self.m_dim1_count: int
        self.m_dim2_count: int
        self.m_sweep_type: str
        self.file_type: str = DataFile.file_code
        self.m_datadict: dict = {}
        self.m_shape: tuple # 2D shape tuple
        self.m_intervals: dict # dim1 and dim2 intervals from 'start' to 'stop' in steps of 'step'
        self.m_intervals_info: dict
        self.__process_csv(DataFile.file_path)
        self.__process_interval()
        self.reshape_data()
        self.__check_missing_dims()


    def __process_csv(self, input_file):
        '''Scrapes all pertinent data from the easyEXPERT csv into the File object.'''
        with open(input_file, 'r') as csvfile:
            reader = csvreader(csvfile, delimiter = ',') # change contents to floats
            data_idx = 0 # data row index -- which row in specifically the numerical data columns we're at
            for row in reader: # each row is a list
                match row[0].strip():
                    case 'PrimitiveTest':
                        self.m_sweep_type = row[1].strip()
                    case 'TestParameter':
                        self.__process_TestParameters(row)
                    case 'Dimension1':
                        self.m_dim1_count = int(row[1])
                    case 'Dimension2':
                        self.m_dim2_count = int(row[1])
                    case 'AnalysisSetup':
                        if row[1].strip() == 'Analysis.Setup.Title':
                            self.m_title = row[2].strip()
                    case 'DataName': # This comes directly before the DataValue entries
                        for i, header in enumerate(row):
                            if i == 0:
                                continue
                            self.m_headers.append(header.strip())

                            # this allocates appropriately-sized numpy arrays for the data
                            self.m_datadict[header.strip()] = np.zeros( self.m_dim1_count * self.m_dim2_count )
                    case 'DataValue': # this inserts data into the appropriate data array spots
                        for i, v in enumerate(row):
                            if i == 0:
                                continue
                            self.m_datadict[self.m_headers[i-1]][data_idx] = float(v)
                        data_idx += 1
        self.m_shape = (self.m_dim2_count, self.m_dim1_count)

    def __process_TestParameters(self, row):
        """Fetches stop, start, and step/count interval information from eE (easyEXPERT) csv.
        This will then be used to construct the intervals of each dimension via process_interval()"""
        match row[1].strip():
            case 'Channel.VName':
                self.m_intervals = [ [row[2].strip(), {}], [row[3].strip(), {}] ]
            case 'Measurement.Primary.Stop':
                self.m_intervals[0][1]['stop'] = float(row[2].strip()) 
            case 'Measurement.Primary.Count':
                self.m_intervals[0][1]['count'] = int(row[2].strip()) 
            case 'Measurement.Primary.Step':
                self.m_intervals[0][1]['step'] = float(row[2].strip())
            case 'Measurement.Bias.Source':
                self.m_intervals[0][1]['start'] = float(row[2].strip()) 
                self.m_intervals[1][1]['start'] = float(row[3].strip())
            case 'Measurement.Secondary.Step':
                self.m_intervals[1][1]['step'] = float(row[2].strip())
            case 'Measurement.Secondary.Count':
                self.m_intervals[1][1]['count'] = int(row[2].strip())

        


    def __process_interval(self):
        """Creates the v1, v2 intervals via [start, start+step, ... stop-step, stop].
        Overwrites self.m_intervals w/ new intervals. Calculates start/step/stop when necessary.
        Goal is to get stop, start, and step params to make the intervals using np.arange()
        Step is frequently determined via the 'count' param if 'step' DNE already"""
        intervals, intervals_info = {}, {}
        v1_name, v2_name = self.m_intervals[0][0], self.m_intervals[1][0]
        v1_start, v2_start = self.m_intervals[0][1]['start'], self.m_intervals[1][1]['start']

        # get the first voltage v1's interval
        v1_stop = self.m_intervals[0][1]['stop']
        if 'count' in self.m_intervals[0][1].keys():
            v1_count = self.m_intervals[0][1]['count']
            v1_step = (v1_stop - v1_start) / (v1_count - 1) # count-1 so it doesn't count the start
        elif 'step' in self.m_intervals[0][1].keys():
            v1_step = self.m_intervals[0][1]['step']
        intervals[v1_name] = np.arange(v1_start, (v1_stop+v1_step), v1_step)
        intervals_info[v1_name] = {"start": v1_start, 
                                   "stop": v1_stop, 
                                   "step": v1_step, 
                                   "count": len(intervals[v1_name])}

        # get the second voltage v2's interval
        if 'step' and 'count' in self.m_intervals[1][1].keys(): # multiple data rows
            v2_count = self.m_intervals[1][1]['count']
            v2_step = self.m_intervals[1][1]['step']
            v2_stop = v2_start + (v2_count-1) * v2_step # count-1 so it doesn't recount the start
            intervals[v2_name] = np.arange(v2_start, (v2_stop+v2_step), v2_step)
        else:
            intervals[v2_name] = np.array([v2_start]) # a single row of data
            v2_count = 1
            v2_step = 0
            v2_stop = v2_start
        intervals_info[v2_name] = {"start": v2_start, "stop": v2_stop, "step": v2_step, "count": v2_count}
        
        self.m_intervals_info = intervals_info
        self.m_intervals = intervals


    def __check_missing_dims(self):
        """This function checks to see if there are independent variables NOT in m_datadict.
        If missing variables are found, then a 2D numpy array is created via the meshgrid."""

        header_keys = self.m_headers 
        # header_keys may or may not contain all interval keys. This determined later on.

        interval_keys = list(self.m_intervals.keys())
        # interval_keys will contain 2 entries: each independent variable voltage

        keys = ['', ''] # this list will store the order of interval keys
        for i in [0, 1]:
            if not interval_keys[i] in header_keys: # if the i-th interval key is NOT in the header keys...
                keys[1] = interval_keys[i] # set keys[1] to the missing key
            else:
                keys[0] = interval_keys[i] # set keys[0] to the present key
        if keys[1]: # if there was an interval key that was missing from the headers keys
            # create the missing 2D array that would go with the missing independent variable using a meshgrid
            x, y = np.meshgrid(self.m_intervals[interval_keys[0]], self.m_intervals[interval_keys[1]])
            # and add it to the m_headers as the 2nd independent variable
            self.m_headers.insert(1, keys[1])
            self.m_datadict[keys[1]] = y
    
    def swap_x_and_y(self):
        """Untested function, beware. It is supposed flip data along the x = y line."""
        temp = self.m_headers[0]
        self.m_headers[0] = self.m_headers[1]
        self.m_headers[1] = temp
        # for key in self.m_headers:
        #     if reverse:
        #         self.m_datadict[key] = np.reshape(self.m_datadict[key], (self.m_dim1_count, self.m_dim2_count))
        #     else:
        #         self.m_datadict[key] = np.reshape(self.m_datadict[key], (self.m_dim2_count, self.m_dim1_count))


    def reshape_data(self, reverse = False):
        """Changes all data in m_datadict to have the same array shape."""
        for key in self.m_headers:
            if reverse:
                self.m_datadict[key] = np.reshape(self.m_datadict[key], (self.m_dim1_count, self.m_dim2_count))
            else:
                self.m_datadict[key] = np.reshape(self.m_datadict[key], (self.m_dim2_count, self.m_dim1_count))

    def print(self):
        """Prints the headers and numpy shape of the data arrays"""
        print(self.m_headers)
        print(self.m_shape)

    def make_meshgrid(self):
        """Creates a meshgrid from the two independent variables"""
        keys = []
        things = []
        for key in self.m_intervals.keys():
            keys.append(key)
        return np.meshgrid(self.m_intervals[keys[0]], self.m_intervals[keys[1]])

    def quick_plot3d(self, Zindex:int, connectors:bool = True):
        """Creates a 3D plot of the data, with the Z axis selected via Zindex

        Input: 
            Zindex: index the Z-data will be pulled from. If 0 or 1, will be the same as X or Y data. 
                Suggested to set Zindex to -1 or -2.
            connectors: Bool of whether to have the wireframe object automatically connect points.   
        """
        if Zindex >= len(self.m_headers):
            print(f"Zindex [{Zindex}] out of bounds of data with len = {len(self.m_headers)}")
            return
        x, y = self.get_data(0), self.get_data(1)
        z = self.get_data(Zindex)
        fig, ax1 = plt.subplots(
            1, 1, #figsize = (12, 18),
            subplot_kw={'projection': '3d'})
        if connectors:
            ax1.plot_wireframe(x, y, z, rcount=self.m_dim2_count, ccount=self.m_dim1_count)#cstride=file.m_dim2_count)
        else:
            ax1.plot_wireframe(x, y, z, rcount=self.m_dim2_count, ccount=0)#cstride=file.m_dim2_count)
    
        ax1.set_xlabel(self.get_data_name(0))
        ax1.set_ylabel(self.get_data_name(1))
        ax1.set_zlabel(self.get_data_name(Zindex))
        ax1.set_title(self.get_title())
        plt.show()

    def quick_plot3d_data(self, X:list, Y:list, Z:list, connectors:bool = True):
        """Creates a 3D plot of the X, Y, Z data according to the combinations of (X[i,j],Y[i,j],Z[i,j]) coordinate triplets.
        X and Y are typically the product of the NumPy.meshgrid(x:1Dlist, y:1Dlist) which will return (X, Y)
        
        Input: 
            X is a 2D list of values that vary column to column but not row to row
            Y is a 2D list of values that vary row to row but not column to column
            Z is a 2D list of values that map each 
            connectors: bool of whether to have the wireframe object automatically connect points.
        """
        fig, ax1 = plt.subplots(
            1, 1, figsize = (12, 18),
            subplot_kw={'projection': '3d'})
        if connectors:
            ax1.plot_wireframe(X, Y, Z, rcount=self.m_dim2_count, ccount=self.m_dim1_count)#cstride=file.m_dim2_count)
        else:
            ax1.plot_wireframe(X, Y, Z, rcount=self.m_dim2_count, ccount=0)#cstride=file.m_dim2_count)
    
        ax1.set_xlabel(self.get_data_name(0))
        ax1.set_ylabel(self.get_data_name(1))
        #ax1.set_zlabel()
        ax1.set_title(self.get_title())
        plt.show()

    def get_data(self, index: int):
        return self.m_datadict[self.m_headers[index]]
    
    def get_data_name(self, index: int):
        return self.m_headers[index]
    
    def get_headers(self):
        return self.m_headers
    
    def get_interval(self, index: int):
        return self.m_intervals[self.m_headers[index]]
    
    def get_interval_name(self, index: int) -> str:
        return self.m_intervals.keys()[self.m_headers[index]]
    
    def get_title(self):
        """Returns m_title"""
        return self.m_title
    
    def get_interval_info(self, index: int) -> dict:
        """Returns the interval_info of the data at index specified."""
        return self.m_intervals_info[self.m_headers[index]]
    
    def get_slicing(self, axis, domain: list[float, float]) -> tuple[int, int]:
        """Returns a tuple for index slicing to reduce the x or y axis to the domain [a, b] via x[:, a:b] or y[a:b, :]
        
        Input:  axis ->'x' or 0 or 'y' or 1 to select axis
                domain -> [a, b] to restrict given axis to
                
        Ouptut: tuple for index slicing of form (a, b)"""
        if axis == 0 or axis == 'x':
            xdom = domain
            x = self.get_data(0)
            cols = (np.searchsorted(x[0,:], xdom[0]),    np.searchsorted(x[0, :], xdom[1], side='right'))
            return cols
        elif axis == 1 or axis == 'y':
            ydom = domain
            y = self.get_data(1)
            rows = (np.searchsorted(y[:, 0], ydom[0]),    np.searchsorted(y[:, 0], ydom[1], side='right'))
            return rows
        else:
            print("Invalid axis selection. Enter either the axis index or character (ei. 'x' or 0; 'y' or 1)")
            return None
        
        """
        For the proper index slicing, x values vary column to column, so you need to hold the row constant
        and vary the column indices. For the y values, y values are constant from column to column and vary 
        row by row, so you need to do the index slicing where you hold the columns constant and change the row.
        This ultimately comes out to looking like: x val var = x[0, :]  ;  y val var = y[:, 0]

        Then, to properly do the slicing of the data arrarows, since x correpsonds to changes in the rows and 
        y corresponds to changes in the columns, the ordering of the index slicing should be like this:
        xtrimmed = x[ rows[0]:rows[1], cols[0]:cols[1] ]
        ytrimmed = y[ rows[0]:rows[1], cols[0]:cols[1] ]
        """



# ==============================================================================
#               DataInfo
# ==============================================================================
# @dataclass
class DataInfo:
    def __init__(self):
        self.data_name: str = '' # name used in title/legend when plotting this object
        self.test_title: str = '' # defulult test title from CSV
        self.file_code: int = -1 # test_type, gate_type, transistor_number 
        self.test_type: int = -1
        self.device_number = -1
        self.device_model: str = ''
        self.units = {'x': '', 'y': '', 'z': ''}
        self.chan_dims = {'len': '', 'wid': '', 'area': ''}
        self.gate: str = ''
        self.misc: str = None

    def print(self):
        print(f"Data set name: {self.data_name}")
        print(f"Default CSV test title: {self.test_title}")
        print(f"File code: {self.file_code}")
        print(f"Gate ID: {self.gate}")
        print(f"Graph preset selection: {self.test_type}")
        print(f"Transistor number: {self.device_number}")
        print(f"Dimensions: {self.chan_dims['len']} x {self.chan_dims['wid']} = {self.chan_dims['area']}")
        print(f"Units: x ({self.units['x']}); y ({self.units['y']}); z ({self.units['z']})")
        if self.misc:
            print(f"Misc: {self.misc}")

    def copy_from(self, Info):
        self.data_name = Info.data_name
        self.test_title  = Info.test_title
        self.file_code = Info.file_code
        self.test_type = Info.test_type
        self.device_number = Info.device_number
        self.device_model = Info.device_model
        self.units= Info.units
        self.chan_dims = Info.chan_dims
        self.gate = Info.gate
        if Info.misc:
            self.misc = Info.misc

    def make_copy(self):
        copy = DataInfo()
        copy.data_name = self.data_name
        copy.test_title  = self.test_title
        copy.file_code = self.file_code
        copy.test_type = self.test_type
        copy.device_number = self.device_number
        copy.device_model = self.device_model
        copy.units= self.units
        copy.chan_dims = self.chan_dims
        copy.gate = self.gate
        if self.misc:
            copy.misc = self.misc
        return copy


# ==============================================================================
#               DataSet
# ==============================================================================
class DataSet(File):
    instance_count = 0
    markers = ['.', '3', '*', '4', 'v', 'o']
    colorblind = True # uses the IBM color pallete for colorblindness
    def __init__(self, DataFile: DataFile):
        super().__init__(DataFile)
        self.Info = DataInfo()
        self.ln_style:str  = '-'
        self.marker: str
        # self.title: bool = True
        self.color: list
        self.set_marker(DataSet.instance_count)
        self.set_color(DataSet.instance_count)#(0.5, 0.5, 0.5)
        self.Info.test_title = self.m_title # defulult test title from CSV
        self.Info.data_name  = DataFile.file_code
        DataSet.instance_count += 1
        self.__parse_data_name(DataFile.file_code) # 1 char, 1 char, #'s numbers (graph type, gate, item number)
        if DataFile.misc:
            self.Info.misc = DataFile.misc

    def print(self, with_data_info = False, with_data = False):
        """Prints DataSet's information"""
        self.Info.print()
        print(f"Line color RGB = {self.color}")
        print(f"Line stye: {self.ln_style}")
        print(f"Line marker: {self.marker}")

        if with_data_info:
            print(self.m_headers)
            print(f"X has length of {len(self.m_x_data)}")
            for i,x in enumerate(self.m_y_data):
                print(f"Y's {i} column has length of {len(x)}")
        if with_data:
            print(self.m_x_data)
            print(self.m_y_data)
    
    def __parse_data_name(self, data_name):
        """Sets the DataSet's meta info from the 3 character test code data_name"""
        self.file_code = data_name

        self.__parse_test_type(data_name[0]) # determines Current or Resistance test type

        if data_name[1] == 'b':
            self.Info.gate = 'bottom'
            self.ln_style = '--'
        elif data_name[1] == 't':
            self.Info.gate = 'top'
            self.ln_style = '-'
        else:
            print("Error: data_name[1] is not readable gate 'b' or 't'.")

        self.__parse_device_number(data_name[2:])

    def set_colorRGB(self, rgb: list[float, float, float]):
        '''Sets the color of the DataSet to the RGB values as a tuple of 3 like so: (R, G, B)'''
        if len(rgb) != 3:
            print('Error: please provide a tuple of floats like of size 3 like so: (R, G, B)')
        self.color = tuple(rgb)
    
    def set_color(self, num: int, print_name: bool = False):
        '''Given an integer, cycles through available color presets. 
        If you want to directly set the RGB, instead use the set_colorRGB() method.
        '''
        color = self.get_color_preset(num, print_name)
        self.set_colorRGB(color)
            

    def set_marker(self, num: int):
        if num < len(DataSet.markers):
            self.marker = DataSet.markers[num]
        else:
            self.set_marker(num-len(DataSet.markers))

    def set_lnstyle(self, style: str):
        self.ln_style = style

    def scale_color(self, scale):
        for i in range(3):
            self.color[i] *= scale

    def get_color(self)->list[float, float, float]:
        "Returns a 3-item tuple of RGB color floats"
        return self.color

    def get_color_preset(self, num, print_name: False)->list[float, float, float]:
        "Returns a 3-item tuple of RGB color floats that corresponds to the color presets"
        assert(num >= 0 and type(num) == int)
        if DataSet.colorblind: # uses the IBM color pallete for colorblindness
            match num:
                case 0:
                    color = [0.5, 0.5, 0.5] ; name = 'grey'
                case 1:
                    color = [0.863, 0.149, 0.498] ; name = 'magenta'
                case 2:
                    color = [0.392, 0.561, 1] ; name = 'blue'
                case 3:
                    color = [0.471, 0.369, 0.941] ; name = 'purple'
                case 4:
                    color = [0.996, 0.38, 0] ; name = 'orange'
                case 5:
                    color = [0, 1, 0] ; name = 'neon green'
                case 6:
                    color = [1, 0.69, 0] ; name = 'yellow'
                case _: 
                    color = self.get_color_preset(num-7, print_name)
        else: 
            match num:
                case 0:
                    color = [0.5, 0.5, 0.5] ; name = 'grey' # color = [0, 0, 0] # black 
                case 1:
                    color = [1, 0, 0] ; name = 'bright red'
                case 2:
                    color = [0, 0, 1] ; name = 'blue'
                case 3:
                    color = [1, 0, 1] ; name = 'neon magenta'
                case 4:
                    color = [0, 0.8, 0.8] ; name = 'cyan' #color = [0, 1, 1] # bright cyan
                case 5:
                    color = [0, 1, 0] ; name = 'neon green'
                case 6:
                    color = [1, 1, 0] ; name = 'bright yellow'
                case _: 
                    color = self.get_color_preset(num-7, print_name)
        if print_name:
            print(color, " <= ", name)
        return color

    def __parse_test_type(self, char: str):
        if char.lower() == 'r':
            self.Info.test_type = 'R'
            self.Info.units['x'] = 'V'
            self.Info.units['y'] = 'V'
            self.Info.units['z'] = 'Ω'
            # self.Info.x_unit = 'V'
            # self.Info.y_unit = 'Ω'        
        elif char.lower() == 'i':
            self.Info.test_type = 'I'
            self.Info.units['x'] = 'V'
            self.Info.units['y'] = 'V'
            self.Info.units['z'] = 'A'
            # self.Info.x_unit = 'V'
            # self.Info.y_unit = 'A'
        else: 
            print("Error: data_name[0] is not readable gate 'R' or 'I'.")

    
    def __parse_device_number(self, transistor_number: str):
        f = open('devices.json') # Opening JSON file containing device info
        data = jsonload(f) # returns JSON object as a dictionary using JSON import

        tnum = int(transistor_number) # device number we'll be looking for
        unknown_device: bool = True
        for device in data['devices']: # Iterating through the JSON list of devices
            if device['number'] == tnum: # if we find the right device, we set fill in its info
                unknown_device = False
                self.Info.device_number = device['number']
                self.Info.chan_dims['len'] = device['length']
                self.Info.chan_dims['wid'] = device['width']
                self.Info.chan_dims['area'] = device['area']
                self.Info.device_model = device['model']
        if unknown_device: # if the device isn't listed
                print(" Adding device not listed in 'devices.json'...")
                print("  Is your test code right or are you testing an unlisted device?")
                self.Info.device_number = None
                self.Info.chan_dims['len'] = "unknown"
                self.Info.chan_dims['wid'] = "unknown"
                self.Info.chan_dims['area'] = "unknown"
                self.Info.device_model = "unknown"
        f.close() # close JSON file

    def add_new_data(self, zlabel: str, z:np.array):
        """Appends a new 2D independent variable array to this DataSet's m_datadict if the dimensions match"""
        DSshape = np.shape(self.get_data(0))
        zshape = np.shape(z)
        if DSshape == zshape:
            self.m_datadict[zlabel] = z
            self.m_headers.append(zlabel) 
        else:
            print(f"\nError: Shape mismatch:")
            print(f" New data dimensions of {zshape} do not match DataSet dimensions of {DSshape}.\n")

    def quick_plot3d(self, Zindex:int, connectors:bool = True):
        """Creates a 3D plot of the data, with the Z axis selected via Zindex

        Input: 
            Zindex: index the Z-data will be pulled from. If 0 or 1, will be the same as X or Y data. 
                Suggested to set Zindex to -1 or -2.
            connectors: Bool of whether to have the wireframe object automatically connect points.   
        """

        if Zindex >= len(self.m_headers):
            print(f"Zindex [{Zindex}] out of bounds of data with len = {len(self.m_headers)}")
            return
        x, y = self.get_data(0), self.get_data(1)
        z = self.get_data(Zindex)
        fig, ax1 = plt.subplots(
            1, 1, #figsize = (12, 18),
            subplot_kw={'projection': '3d'})
        if connectors:
            ax1.plot_wireframe(x, y, z, rcount=self.m_dim2_count, ccount=self.m_dim1_count, color = self.color)#cstride=file.m_dim2_count)
        else:
            ax1.plot_wireframe(x, y, z, rcount=self.m_dim2_count, ccount=0, color = self.color)#cstride=file.m_dim2_count)
    
        ax1.set_xlabel(self.get_data_name(0))
        ax1.set_ylabel(self.get_data_name(1))
        ax1.set_zlabel(self.get_data_name(Zindex))
        ax1.set_title(self.Info.data_name)
        plt.show()


    
    def quick_plot2d(self, x_idx, y_idx, color_bar: bool = True):
        """Given the selected independent x-axis and dependent y-axis, generate a 2D plot projected
            onto the second independent x2-axis, representing x2 via greyscaling.
        Input: 
            x_idx = 'x'/'y' or 0/1 and will select data for x-axis of 2D plot
            y_idx = 2/3/-1 and will select data for y-axis of 2D plot
                  the non-selected independent axis will be represented via sidebar 
            hint: to know which index correpsonds to what header, use the get_indices() method    
        """
        marker = self.marker
        color = np.array(self.color)
        name = self.Info.data_name

        if x_idx in [0, 'x']:
            x_idx = [0, 'x']
            x2_idx = [1, 'y']
        elif x_idx in [1, 'y']:
            x_idx = [1, 'y']
            x2_idx = [0, 'x']
        else:
            print(" Error: Invalid x_idx, choose from 0/'x' or 1/'y'")
            return
            
        fig, ax1 = plt.subplots(1, figsize = (6, 4))
        labels = [self.get_data_name(x_idx[0]), self.get_data_name(x2_idx[0]), self.get_data_name(y_idx)]
        ax1.set_xlabel(labels[0]) # sets x label on 2d plot
        ax1.set_ylabel(labels[2]) # sets y label on 2d plot
        ax1.set_title(self.Info.data_name)

        x: np.array = self.get_data(x_idx[0])
        x2: np.array = self.get_data(x2_idx[0])
        y: np.array = self.get_data(y_idx)


        if x2_idx[0]: # if x2_idx is the 2nd indep variable (corresponding to y axis in 3d plot)
            x2 = x2[ :, 0 ]
            x = x[ 0, : ]
            rc_reversal = False # the order of rows and columns is preserved
        else:# x varies by columns and y varies by rows, so if x_idx == 'y' and x2_idx == 'x'
            #   then the row and column slicing must be swapped accordingly.
            x2 = x2[ 0, : ]
            x = x[ : , 0 ]
            rc_reversal = True # the order of rows and columns is swapped
            marker = ',' # change the marker type so the scatter plot doesn't look ugly    

        if (x2.max()-x2.min()==0): # if there's only data point color, 
            meta_color_data = np.array([1]) # don't bother shading the color
        else:
            meta_color_data = np.linspace(0.2, 1, len(x2))

        if color_bar== True:
            my_cmap = [shade*color for shade in meta_color_data]
            my_cmap = mpl.colors.ListedColormap(my_cmap)

            if len(x2) < 21: #if there is a reasonable number of curves to display on a colorbar
                # assuming that the curves are evenly spaced in the domain by a 'step' parameter:
                step = (x2.max() - x2.min())/len(x2)
            else: # otherwise, there are too many points and we will treat the cbar as continuous
                step = (x2.max() - x2.min())/10 # in which case, we will just do 10 tick marks

            # to fit all curves into the domain, the ticks must be located at these places
            if step == 0:
                ticks = x2
            else:            
                ticks = np.arange(x2.min(), x2.max()+step, step)

            # assuming that the curves are evenly spaced in the domain by a 'step' parameter:
            # step = (x2.max() - x2.min())/len(x2) # step
            # # to fit all curves into the domain, the ticks must be located at these places
            # ticks = np.arange(x2.min() + step/2, x2.max() +3*step/2, step)
            norm = plt.Normalize(x2.min(), x2.max())

            if len(x2) > 21:
                fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), ax = ax1,
                        format=mpl.ticker.FixedFormatter( ticks ), # what values go on the tick marks
                        label=labels[1], 
                        ticks = ticks # the location of where to put the tick marks on the colorbar  
                        )
            else:
                fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), ax = ax1,
                        format=mpl.ticker.FixedFormatter(x2), # what values go on the tick marks
                        label=labels[1], 
                        ticks = ticks + step/2 # the location of where to put the tick marks on the colorbar  
                        )

        for col in range(len(x2)):
            if not rc_reversal:
                ax1.plot(x, y[col, :], 
                            color = meta_color_data[col] * color,
                            marker = marker)
            else:
                ax1.scatter(x, y[:, col], 
                            color = meta_color_data[col] * color, 
                            marker = marker)
        plt.show()

    def print_indices(self):   
        '''Prints off indices of the corresponding axis label'''     
        print(" index\theader")
        headers = self.get_headers()
        for j, h in enumerate(headers):
            print(f"   {j}\t {h}")

    def set_name(self, data_name: str):
        match data_name:
            case "area":
                area: str = f"{self.Info.chan_dims['area']}" + r"$\mu m^2$"
                self.Info.data_name = area
            case "dims":
                dims: str = f"{self.Info.chan_dims['len']}" + r"$\mu m\times$" + f"{self.Info.chan_dims['wid']}" +r"$\mu m$"
                self.Info.data_name = dims
            case "gate":
                self.Info.data_name = f"{self.Info.gate} gate"
            case "device_model":
                self.Info.data_name = f"{self.Info.device_model}"
            case "device_number":
                self.Info.data_name = f"Device #{self.Info.device_number}"
            case "file_code":
                self.Info.data_name = self.Info.file_code
            case "test_type":
                self.Info.data_name = self.Info.test_type
            case "misc":
                if self.Info.misc:
                    self.Info.data_name = self.Info.misc
                else:
                    self.Info.data_name = "no_misc_found_message"
            case _:
                self.Info.data_name = data_name


# ==============================================================================
#               DataBank
# ==============================================================================
class DataBank:
    def __init__(self, Set: DataSet = None):
        self.DataSets = []
        self.X: list = []
        self.Y: list = []
        self.Z: list = []
        self.domain: dict[str, list[float]] = {'x': (-float('inf'),float('inf')),
                        'y': (-float('inf'),float('inf')),
                        'z': (-float('inf'),float('inf'))
                        }
        self.scatter_plots: bool = False
        self.show_fig: bool = True
        self.auto_labels: bool = True
        self.connectors: bool = False
        self.show_legend: bool = True
        self.Bank_Info: DataInfo = None
        self.override: bool = False
        if Set:
            self.append(Set)

    def change_Set_color(self, SetIndex: int, color: list[float,float,float]):
        """Method to change a DataSet at index SetIndex to the RGB input color"""
        print(f"Data Set #{SetIndex} color changed from {self.DataSets[SetIndex].color}")
        self.DataSets[SetIndex] = color
        print(f"to {self.DataSets[SetIndex].color}")

    def process_axis(self, axis, num_output=False):
        valid_axis = False
        for i, v in enumerate(['x','y','z']):
            if axis == i or axis == v:
                if not num_output:
                    axis = v
                    valid_axis = True
                else:
                    axis = i
                    valid_axis = True
        if not valid_axis:
            raise Exception("Error: invalid axis selected. Pick from 'x'/0, 'y'/1, or 'z'/2")
        return axis
   
    def append(self, Set: DataSet):
        """Method for appending DataSets to the DataBank"""
        assert(type(Set) == DataSet)

        s_count = len(self.DataSets)
        if s_count == 0:
            self.DataSets.append(Set)
            self.Bank_Info = Set.Info.make_copy()
            # Set.set_color(s_count)
        elif Set.Info.gate == self.Bank_Info.gate and Set.Info.test_type == self.Bank_Info.test_type:
            # Set.set_color(s_count)
            # Set.set_marker(s_count)
            self.DataSets.append(Set)
            # Set.set_color(s_count)
        else:
            if self.override:
                # Set.set_color(s_count)
                # Set.set_marker(s_count)
                self.DataSets.append(Set)
                # Set.set_color(s_count)
            else:
                print("\nMismatching gate/graph type. Cannot add this data to current set without override.\n")

    def add_from_DataFile(self, 
                          DataFile: DataFile, 
                          y_col:list = [],
                          x_col:int = 0
                          ):
        if not y_col:
            #print("Using this Data Bank's default y_col selection...")
            y_col = self.DataSets[0].col_info[1]
        if not x_col:
            #print("Uisng this Data Bank's default x_col selection...")
            x_col = self.DataSets[0].col_info[0]
        Set = DataSet(DataFile, x_col, y_col)
        #print("Adding Set...")
        self.append(Set)


    def print(self, include_info: bool = False):
        """Prints info about the DataBank and the stored DataSets"""
        length = len(self.DataSets)
        print(f"Data Set count: {length}\n")
        if length == 0:
            print("No data sets loaded.")
            return
        print(f"Data Set length info:")
        for i in range(length):
            print(f" Data Set {i}'s x length: {self.DataSets[i].m_dim1_count}")
            print(f" Data Set {i}'s y length: {self.DataSets[i].m_dim2_count}")
            if include_info:
                self.DataSets[i].print()
                print()
        print(f"Data bank's gate type: {self.Bank_Info.gate}")
        print(f"Data bank's graph setting: {self.Bank_Info.test_type}")

    def make_auto_labels(self, xlbl, ylbl, zlbl):
        """Returns automatically created labels from input labels
        """
        # if ylbl in ['Vgs', 'Vtgs', 'Vbgs']:
        #     ylbl = r'Gate Voltage $V_{GS}$ (V)'
        if ylbl in ['Vgs']:
            ylbl = r'Gate Voltage $V_{GS}$ (V)'
        elif ylbl in ['Vtgs'] and self.override == False:
            ylbl = r'Top Gate Voltage $V_{TGS}$ (V)'
        elif ylbl in ['Vbgs'] and self.override == False:
            ylbl = r'Bottom Gate Voltage $V_{BGS}$ (V)'
        elif ylbl in ['Vtgs', 'Vbgs'] and self.override == True:
            ylbl = r'Gate Voltage $V_{GS}$ (V)'
        elif ylbl == 'Vds':
            ylbl = r'Drain-Source Voltage $V_{DS}$ (V)'

        # if xlbl in ['Vgs', 'Vtgs', 'Vbgs']:
        #     xlbl = r'Gate Voltage $V_{GS}$ (V)'
        if xlbl in ['Vgs']:
            xlbl = r'Gate Voltage $V_{GS}$ (V)'
        elif xlbl in ['Vtgs'] and self.override == False:
            xlbl = r'Top Gate Voltage $V_{TGS}$ (V)'
        elif xlbl in ['Vbgs'] and self.override == False:
            xlbl = r'Bottom Gate Voltage $V_{BGS}$ (V)'
        elif xlbl in ['Vtgs', 'Vbgs'] and self.override == True:
            xlbl = r'Gate Voltage $V_{GS}$ (V)'
        elif xlbl == 'Vds':
            xlbl = r'Drain-Source Voltage $V_{DS}$ (V)'

        if zlbl in ['R', 'Rd', 'Rds']:
            zlbl = r'Resistance $R_{DS}$ (Ω)'
        elif zlbl in ['Rk']:
            zlbl = r'Resistance $R_{DS}$ (kΩ)'
        elif zlbl in ['I', 'Id', 'Ids']:
            zlbl = r'Drain Current $I_{DS}$ (A)'
        elif zlbl == 'Im':
            zlbl = r'Drain Current $I_{DS}$ (mA)'
        elif zlbl == 'Iu':
            zlbl = r'Drain Current $I_{DS}$ (μA)'
        elif zlbl in ['div', "RP"]:
            zlbl = r'Relative Performance'
        lbls = [xlbl, ylbl, zlbl]
        return lbls

    

    def quick_plot3d(self, Zindex = -1):
        """Displays a 3D plot of the DataBank's contents with 
        user-set domain restriction, potential auto-labeling, and possible connectors.
        """

        fig, ax1 = plt.subplots(
            1, 1, 
            # figsize = self.figsize,
            subplot_kw={'projection': '3d'})
        
        if len(self.DataSets) == 0:
            print("No data loaded, empty plot generated")
            plt.show()
            return      

        labels = [self.DataSets[0].get_data_name(0),
                    self.DataSets[0].get_data_name(1),
                    self.DataSets[0].get_data_name(Zindex)]
        if self.auto_labels:
            labels = self.make_auto_labels(labels[0], labels[1], labels[2])

        ax1.set_xlabel(labels[0])
        ax1.set_ylabel(labels[1])
        ax1.set_zlabel(labels[2])

        ax1.set_title(self.Bank_Info.data_name)
        
        for i, S in enumerate(self.DataSets):
            x, y = S.get_data(0), S.get_data(1)
            z = S.get_data(Zindex)
            dim1, dim2 = S.m_dim1_count, S.m_dim2_count

            cols = S.get_slicing('x', self.domain['x'])
            rows = S.get_slicing('y', self.domain['y'])



            color = S.color
            name = S.Info.data_name
            marker = S.marker
            if self.connectors:
                col_counts = dim1
            else:
                col_counts = 0
            if self.scatter_plots:
                ax1.scatter3D(x[ rows[0]:rows[1], cols[0]:cols[1] ],
                                y[ rows[0]:rows[1], cols[0]:cols[1] ],
                                z[ rows[0]:rows[1], cols[0]:cols[1] ], 
                                marker = marker,
                                color = color,
                                label = name)
            else:
                ax1.plot_wireframe( x[ rows[0]:rows[1], cols[0]:cols[1] ],
                                y[ rows[0]:rows[1], cols[0]:cols[1] ],
                                z[ rows[0]:rows[1], cols[0]:cols[1] ], 
                                rcount=dim2, 
                                ccount= col_counts,
                                color = color,
                                label = name)
        if self.show_legend:
            plt.legend(loc='upper left')
        if self.show_fig:
            plt.show()
        


    def quick_div_plot3d(self, DivSet: DataSet, divIdx, drop_zeros=True, tolerance: float = -1, Zindex=-1):
        """Displays a 3D plot of the DataBank's contents relative to the dividing DataSet. 
        """
        
        div_data_dims = (DivSet.m_dim1_count, DivSet.m_dim2_count)

        fig, ax1 = plt.subplots(
            1, 1, 
            # figsize = self.figsize,
            subplot_kw={'projection': '3d'})
        
        if len(self.DataSets) == 0:
            print("No data loaded, empty plot generated")
            plt.show()
            return

        labels = [self.DataSets[0].get_data_name(0),
                  self.DataSets[0].get_data_name(1),
                  f"{self.DataSets[0].get_data_name(Zindex)}/{DivSet.get_data_name(divIdx)}"]
        if self.auto_labels:
            temp = self.make_auto_labels(labels[0], labels[1], labels[2])
            labels[0] = temp[0]
            labels[1] = temp[1]

        ax1.set_xlabel(labels[0])
        ax1.set_ylabel(labels[1])
        ax1.set_zlabel('Relative Performance')

        ax1.set_title(self.Bank_Info.data_name)
        X, Y, Z = [], [], []
        colors, names, markers, dim1s, dim2s = [], [], [], [], []
        for i, S in enumerate(self.DataSets):
            S_data_dims = (S.m_dim1_count, S.m_dim2_count)

            # if dimensions mismatch, omit the data set
            if S_data_dims != div_data_dims:
                print(f"\nDataSet at index ({i}) does not have matching x,y array dimensions of the dividing DataSet")
                print(f"\t{S_data_dims} =/= {div_data_dims}")
                print(f"Skipping DataSet ({i}) in DataBank\n")
                # add a "skipped DataSets" list here to keep track of for labelling later down the line
                continue

            zdiv = DivSet.get_data(divIdx)
            x = S.get_data(0)
            y = S.get_data(1)
            z = S.get_data(Zindex)
            if drop_zeros:
                zdiv, x, y, z = self.drop_zeros([zdiv, x, y, z], tolerance)

            dim1s.append(S.m_dim1_count)
            dim2s.append(S.m_dim2_count)

            cols = self.get_slicing('x', self.domain['x'], x)
            rows = self.get_slicing('y', self.domain['y'], y)

            X.append(x[ rows[0]:rows[1], cols[0]:cols[1] ])
            Y.append(y[ rows[0]:rows[1], cols[0]:cols[1] ])
            Z.append(z[ rows[0]:rows[1], cols[0]:cols[1] ] / zdiv[ rows[0]:rows[1], cols[0]:cols[1] ])

            colors.append( S.color )
            names.append( S.Info.data_name )
            markers.append( S.marker )
        for i in range(len(X)):
            if self.connectors:
                col_counts = dim1s[i]
            else:
                col_counts = 0

            if self.scatter_plots:
                ax1.scatter3D( X[i], Y[i], Z[i],
                                marker = markers[i],
                                color = colors[i],
                                label = names[i])
            else:
                ax1.plot_wireframe(X[i], Y[i], Z[i], 
                                rcount=dim2s[i], 
                                ccount=col_counts,
                                color = colors[i],
                                label = names[i])#cstride=file.m_dim2_count)
        if self.show_legend:
            plt.legend(loc='upper left')
        if self.show_fig:
            plt.show()
    
    
    def print_indices(self):   
        '''Prints off indices of the corresponding axis label'''     
        for i, S in enumerate(self.DataSets):
            print(f"For data set {i}:")

            if self.auto_labels:
                print(" index\theader\tauto axis label")
                ax_labels = []

            else:
                print(" index\theader")
            
            headers = S.get_headers()
            for j, h in enumerate(headers):
                
                if self.auto_labels:
                    if j == 0:
                        ax_labels = self.make_auto_labels(headers[0], headers[1], headers[2])
                    elif j > 2:
                        temp = self.make_auto_labels(headers[0], headers[1], headers[j])
                        ax_labels.append(temp[2])
                    print(f"   {j}\t {h}\t {ax_labels[j]}")

                else:
                    print(f"   {j}\t {h}")


    def set_domain(self, axis: str, domain: list[float, float], show=False):
        """[a, b] restricts the domain on the provided axis to be between the values a and b. 
        """
        if axis == 0 or axis == 'x':
            self.domain['x'] = tuple(domain)
        elif axis == 1 or axis == 'y':
            self.domain['y'] = tuple(domain)
        else:
            print(f"Axis '{axis}' is not a valid axis choice. Select from either 'x'/0 or 'y'/1.")
        if show:
            print(f"Domain now:\n{self.domain}")

    def reset_domain(self):
        self.domain = {'x': (-float('inf'), float('inf')), 'y': (-float('inf'), float('inf')), 'z': (-float('inf'), float('inf'))}
        
    
    def pop(self, i:int =-1) -> DataSet:
        """Akin to str pop method. If len(DataSets) becomes 0, Bank_Info resets to None type"""
        S = self.DataSets.pop(i)
        if len(self.DataSets) == 0:
            self.Bank_Info: DataInfo = None
        return S
    
    def create_projection_mapping(self, X2: list):
        """creates a dictionary of valid column indices as keys and
          corresponding valid DataSet indices"""
        meta_col_data = {}
        meta_color_data = {}
        for s, v in enumerate(X2): # for each DataSet # and list of values
            ncols = len(v) # finds number of columns in X2 data
            meta_color_data[s] = np.linspace(0.2, 1, ncols) # creates different shading factors based on X2 depth
            for c in range(ncols): # for each 
                if c in meta_col_data:
                    meta_col_data[c].append(s) # append the DataSet index s to the list of valid column indices 
                else:
                    meta_col_data[c] = [s] # make a new key-value pair of column index and DataSet index
        # check values 
        for s, x2 in enumerate(X2):
            if (x2.max()-x2.min()==0): # if there's only data point color, 
                meta_color_data[s] = np.array([1]) # don't bother shading the color

        return meta_col_data, meta_color_data


    def quick_plot2d(self, x_idx, y_idx, cbar: bool = True, cmap:str = None, **kwargs):
        """Given the selected independent x-axis and dependent y-axis, generate a 2D plot projected
            onto the second independent x2-axis, representing x2 via greyscaling.
        Input: 
            x_idx = 'x'/'y' or 0/1 and will select data for x-axis of 2D plot
            y_idx = 2/3/-1 and will select data for y-axis of 2D plot
                  the non-selected independent axis will be represented via sidebar 
            hint: to know which index correpsonds to what header, use the get_indices() method    
        """
        if len(self.DataSets) == 0:
            print("No data loaded, empty plot generated")
            plt.show()
            return

        for k, val in kwargs.items():
            print("%s == %s" % (k, val))

        
        if x_idx in [0, 'x']:
            x_idx = [0, 'x']
            x2_idx = [1, 'y']
        elif x_idx in [1, 'y']:
            x_idx = [1, 'y']
            x2_idx = [0, 'x']
        else:
            print(" Error: Invalid x_idx, choose from 0/'x' or 1/'y'")
            return

        fig, ax1 = plt.subplots(
            1, figsize = (6, 4))

        X, X2, Y = [], [], []
        markers, colors, names, line_styles = [], [], [], []
        # line_names = []  

        labels = [self.DataSets[0].get_data_name(x_idx[0]),
                    self.DataSets[0].get_data_name(x2_idx[0]),
                    self.DataSets[0].get_data_name(y_idx)]
        if self.auto_labels:
            labels = self.make_auto_labels(labels[0], labels[1], labels[2])

        ax1.set_xlabel(labels[0]) # sets x label on 2d plot
        ax1.set_ylabel(labels[2]) # sets y label on 2d plot

        ax1.set_title(self.Bank_Info.data_name)

        for S in self.DataSets:
            x: list = S.get_data(x_idx[0])
            x2: list= S.get_data(x2_idx[0])
            y: list = S.get_data(y_idx)
            
            if x2_idx[0]: # if x2_idx is the 2nd indep variable (corresponding to y axis in 3d plot)
                cols = S.get_slicing(x_idx[0], self.domain[x_idx[1]]) # x vars by columns
                rows = S.get_slicing(x2_idx[0], self.domain[x2_idx[1]]) # y vars by rows
                x2 = x2[ rows[0]:rows[1], 0 ]
                x = x[ 0, cols[0]:cols[1] ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = False # the order of rows and columns is preserved
            else:
                # x varies by columns and y varies by rows, so if x_idx == 'y' and x2_idx == 'x'
                #   then the row and column slicing must be swapped accordingly.
                rows = S.get_slicing(x_idx[0], self.domain[x_idx[1]]) 
                cols = S.get_slicing(x2_idx[0], self.domain[x2_idx[1]]) 
                x2 = x2[ 0, cols[0]: cols[1] ]
                x = x[ rows[0]:rows[1], 0 ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = True # the order of rows and columns is flipped
            dim1, dim2, ydim = len(x), len(x2), len(y)

            X.append( x )
            X2.append(x2)
            Y.append( y )

            if rc_reversal and S.marker == '.':
                markers.append(',')
            else:
                markers.append(S.marker)
            colors.append(np.array(S.color))
            names.append(S.Info.data_name)
            line_styles.append(S.ln_style)

        meta_col_data, meta_color_data = self.create_projection_mapping(X2)

        # discrete=True
        if cmap:
            cmap = cmap # sets the current cmap in arg to the cmap used
        else:
            cmap = meta_color_data #sets to the calculated cmap

        if cbar == True:
            X2r = np.round(X2, decimals=2)
            if type(cmap) == dict: 
                my_cmap = [shade*np.array(self.DataSets[0].color) for shade in cmap[0]]
                my_cmap = mpl.colors.ListedColormap(my_cmap)
            elif type(cmap) == str:
                # if discrete:
                my_cmap = plt.get_cmap(cmap, len(X2[0]))

            norm = plt.Normalize(X2[0].min(), X2[0].max())

            if len(X2[0]) > 21: #if there is NOT a reasonable number of curves to display on a colorbar
                discrete = False # automatically turn discrete plotting off

            if len(X2[0]) < 21: 
                # assuming that the curves are evenly spaced in the domain by a 'step' parameter:
                step = (X2[0].max() - X2[0].min())/len(X2[0])
            else: # otherwise, there are too many points and we will treat the cbar as continuous
                step = (X2[0].max() - X2[0].min())/10 # in which case, we will just do 10 tick marks
                
            # to fit all curves into the domain, the ticks must be located at these places
            if step == 0:
                ticks = np.round(X2[0], 3)
                # ticks = [str(round(float(label), 2)) for label in [X2r[0][0]]]
            else:
                ticks = np.arange(X2[0].min(), X2[0].max()+step, step)
                # ticks = np.round(ticks, 3)
                # ticks = [str(round(float(label), 2)) for label in [X2[0][0]]]


            tick_labels = ['{:.2f}'.format(x_2) for x_2 in X2[0]]

            if len(X2[0]) > 21:
                fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), ax = ax1,
                        format=mpl.ticker.FixedFormatter( ticks ), # what values go on the tick marks
                        label=labels[1], 
                        ticks = ticks # the location of where to put the tick marks on the colorbar  
                        )
            else:
                fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), ax = ax1,
                        format=mpl.ticker.FixedFormatter( tick_labels ), # what values go on the tick marks
                        label=labels[1], 
                        ticks = ticks + step/2 # the location of where to put the tick marks on the colorbar  
                        )

        for col, sets in meta_col_data.items():
            for s in sets:
                if type(cmap) == dict:
                    color = meta_color_data[s][col] * colors[s]
                else: # type(meta_col_data) == mpl.colors.LinearSegmentedColormap:
                    my_cmap = plt.get_cmap(cmap)
                    color = my_cmap( int(256*norm(X2[s][col])) )
                if not rc_reversal:
                    if self.scatter_plots:
                        ax1.scatter(X[s], Y[s][col, :], 
                                color = color, 
                                marker = markers[s])
                    else:
                        ax1.plot(X[s], Y[s][col, :], 
                             color = color,
                             marker = markers[s])
                else:
                    ax1.scatter(X[s], Y[s][:, col], 
                                color = color, 
                                marker = markers[s])
                                #marker='.')
        if self.show_legend:
            for s in range(len(names)):
                if self.scatter_plots:
                    ax1.scatter([], [], # plot no data, just do this to get legend
                            color = colors[s], 
                            marker = markers[s],
                            label = names[s])
                else:
                    ax1.plot([], [], 
                            linestyle = line_styles[s],
                            color = colors[s], 
                            marker = markers[s],
                            label = names[s])
        
            plt.legend(loc='upper left')

        if self.show_fig:
            plt.show()
    
    def quick_div_plot2d(self, x_idx, y_idx, DivSet: DataSet, divIdx, drop_zeros=True, tolerance: float = -1, cbar: bool = True, cmap:str = None):
        """Displays a 2D plot of the DataBank's contents relative to the dividing DataSet.         
        Given the selected independent x-axis and dependent y-axis, generate a 2D plot projected
            onto the second independent x2-axis, representing x2 via greyscaling.
        Input: 
            x_idx = 'x'/'y' or 0/1 and will select data for x-axis of 2D plot
            y_idx = 2/3/-1 and will select data for y-axis of 2D plot
                  the non-selected independent axis will be represented via sidebar 
            hint: to know which index correpsonds to what header, use the get_indices() method    
        """
        if len(self.DataSets) == 0:
            print("No data loaded, empty plot generated")
            plt.show()
            return

        if x_idx in ['x', 0]:
            x_idx, x2_idx = 'x', 'y'
        elif x_idx in ['y', 1]:
            x_idx, x2_idx = 'y', 'x'
        else:
            print("Invalid axis selected: pick from 0/'x' or 1/'y'")
            return

        fig, ax1 = plt.subplots(
            1, figsize = (6, 4))

        X, X2, Y = [], [], []
        line_styles, markers, colors, names = [], [], [], []
        # line_names = []  

        labels = [self.DataSets[0].get_data_name(self.process_axis(x_idx, num_output=True)),
                    self.DataSets[0].get_data_name(self.process_axis(x2_idx, num_output=True)),
                    self.DataSets[0].get_data_name(y_idx)]
        if self.auto_labels:
            labels = self.make_auto_labels(labels[0], labels[1], 'div')

        ax1.set_xlabel(labels[0]) # sets x label on 2d plot
        ax1.set_ylabel(labels[2]) # sets y label on 2d plot
        ax1.set_title(f"Performance Plot Relative to {DivSet.Info.data_name}")
        # ax1.set_title(self.Bank_Info.data_name)


        div_data_dims = (DivSet.m_dim1_count, DivSet.m_dim2_count)

        X, X2, Y = [], [], []

        for i, S in enumerate(self.DataSets):
            S_data_dims = (S.m_dim1_count, S.m_dim2_count)

            # if dimensinos mismatch, omit the data set
            if S_data_dims != div_data_dims:
                print(f"\nDataSet at index ({i}) does not have matching x,y array dimensions of the dividing DataSet")
                print(f"\t{S_data_dims} =/= {div_data_dims}")
                print(f"Skipping DataSet ({i}) in DataBank\n")
                # add a "skipped DataSets" list here to keep track of for labelling later down the line
                continue

            ydiv: list = DivSet.get_data(divIdx)
            x: list = S.get_data(self.process_axis(x_idx, num_output=True))
            x2: list= S.get_data(self.process_axis(x2_idx, num_output=True))
            y: list = S.get_data(y_idx)/ydiv

            if drop_zeros:
                ydiv, x, x2, y = self.drop_zeros([ydiv, x, x2, y], tolerance)

            ######################## Domain Restriction implementation ##############################

            if x2_idx == 'y': # if x2_idx is the 2nd indep variable (corresponding to y axis in 3d plot)
                cols = self.get_slicing(x_idx, self.domain[x_idx], x) # x vars by columns
                # cols = S.get_slicing(x_idx[0], self.domain[x_idx[1]]) 
                rows = self.get_slicing(x2_idx, self.domain[x2_idx], x2) # y vars by rows
                x2 = x2[ rows[0]:rows[1], 0 ]
                x = x[ 0, cols[0]:cols[1] ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = False # the order of rows and columns is preserved
            else:
                # x varies by columns and y varies by rows, so if x_idx == 'y' and x2_idx == 'x'
                #   then the row and column slicing must be swapped accordingly.
                rows = self.get_slicing(x_idx, self.domain[x_idx], x) 
                cols = self.get_slicing(x2_idx, self.domain[x2_idx], x2) 
                x2 = x2[ 0, cols[0]: cols[1] ]
                x = x[ rows[0]:rows[1], 0 ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = True # the order of rows and columns is flipped

            ########################################################################################

            X.append( x )
            X2.append(x2)
            Y.append( y )

            if rc_reversal and S.marker == '.': # if 'y' is being plotted as the independent variable
                markers.append(',') # change all markers to be very small so you can see them
            else: 
                markers.append(S.marker) # otherwise, just use the regular markers 
            colors.append(np.array(S.color))
            names.append(S.Info.data_name)
            line_styles.append(S.ln_style)
        
        meta_col_data, meta_color_data = self.create_projection_mapping(X2)       
        if cmap:
            cmap = cmap
        else:
            cmap = meta_color_data
        #################### Color bar implementation ##################
        if cbar:
            discrete=True
            min = -float('inf')
            max =  float('inf')
            x2 = X2[0]
            for S in (X2):
                    if min < S.min():
                        min = S.min()
                    if max > S.max():
                        max = S.max()

            if type(cmap) == dict: 
                my_cmap = [shade*np.array(self.DataSets[0].color) for shade in meta_color_data[0]]
                my_cmap = mpl.colors.ListedColormap(my_cmap)
            elif type(cmap) == str:
                if discrete:
                    my_cmap = plt.get_cmap(cmap, len(x2))
                else:
                    my_cmap = plt.get_cmap(cmap)

            norm = plt.Normalize(min, max)
            self.norm = norm
            
            letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p']
            
            if discrete:
                step = (x2.max() - x2.min())/(len(x2))
                if step == 0:
                    tick_locations = [x2[0]]
                    tick_labels = [x2[0]]
                else:            
                    tick_locations = np.arange(x2.min(), x2.max() + step, step) 
                    tick_locations += 0.5*step
                    tick_labels = [str(round(float(label), 2)) for label in x2] #x2
                # print(step, x2.min(), x2.max())
                # print(tick_locations, tick_labels)
                
            else:
                step = (x2.max() - x2.min())/10
                if step == 0:
                    tick_locations = x2[0]
                    tick_labels = [x2[0]]
                else:
                    tick_locations = np.arange(X2[0].min(), X2[0].max()+step, step)
                    tick_labels = [str(round(float(label), 2)) for label in x2]
            
            if discrete:
                fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), ax = ax1,
                        label=labels[1], 
                        format=mpl.ticker.FixedFormatter( tick_labels ), # what values go on the tick marks
                        ticks = tick_locations# the location of where to put the tick marks on the colorbar relative to norm
                        )
            else:
                fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), ax = ax1,
                    label=labels[1], 
                    format=mpl.ticker.FixedFormatter(tick_locations), # what values go on the tick marks
                    ticks = tick_locations # the location of where to put the tick marks on the colorbar relative to norm
                    )

            #Normalize to [0,1]
            norm = plt.Normalize(min, max)

        ###############################################################

        # if self.cmap:
        #     meta_color_data = 


        ##################### plot_data ###############################
        for col, sets in meta_col_data.items():
            for s in sets:
                if type(cmap) == dict:
                    color = meta_color_data[s][col] * colors[s]
                else: # type(meta_col_data) == mpl.colors.LinearSegmentedColormap:
                    my_cmap = plt.get_cmap(cmap)
                    color = my_cmap( int(256*self.norm(X2[s][col])) )
                if not rc_reversal:
                    if self.scatter_plots:
                        plt.scatter(X[s], Y[s][col, :], 
                                color = color, 
                                marker = markers[s])
                    else:
                        plt.plot(X[s], Y[s][col, :], 
                             color = color,
                             #  color = meta_color_data[s][col] * self.colors[s],
                             marker = markers[s])
                else:
                    plt.scatter(X[s], Y[s][:, col], 
                                color = color, 
                                marker = markers[s])
        
        if self.show_legend:
            for s in range(len(names)):
                if self.scatter_plots:
                    ax1.scatter([], [], # plot no data, just do this to get legend
                            color = colors[s], 
                            marker = markers[s],
                            label = names[s])
                else:
                    ax1.plot([], [], 
                            linestyle = line_styles[s],
                            color = colors[s], 
                            marker = markers[s],
                            label = names[s])

            plt.legend(loc='upper left')

        ###########################################################################
        if self.show_fig:
            plt.show()


    def get_slicing(self, axis, domain: list[float, float], Array2D: np.array) -> tuple[int, int]:
        """Returns a tuple for index slicing to reduce the x or y axis to the domain [a, b] via x[:, a:b] or y[a:b, :]
        
        Input:  DataSet -> DataSet object you want sliced
                axis ->'x' or 0 or 'y' or 1 to select axis
                domain -> [a, b] to restrict given axis to

                
        Ouptut: tuple for index slicing of form (a, b)
                0/'x' -> cols
                1/'y' -> rows"""

        if axis in [0, 'x']:
            xdom = domain
            cols = (np.searchsorted(Array2D[0,:], xdom[0]),  np.searchsorted(Array2D[0, :], xdom[1], side='right'))
            return cols
        elif axis in [1, 'y']:
            ydom = domain
            rows = (np.searchsorted(Array2D[:,0], ydom[0]),  np.searchsorted(Array2D[:, 0], ydom[1], side='right'))
            return rows
        else:
            print("Invalid axis selection. Enter either the axis index or character (ei. 'x' or 0; 'y' or 1)")
            return None
        
        """
        For the proper index slicing, x values vary column to column, so you need to hold the row constant
        and vary the column indices. For the y values, y values are constant from column to column and vary 
        row by row, so you need to do the index slicing where you hold the columns constant and change the row.
        This ultimately comes out to looking like: x val var = x[0, :]  ;  y val var = y[:, 0]

        Then, to properly do the slicing of the data arrarows, since x correpsonds to changes in the rows and 
        y corresponds to changes in the columns, the ordering of the index slicing should be like this:
        xtrimmed = x[ rows[0]:rows[1], cols[0]:cols[1] ]
        ytrimmed = y[ rows[0]:rows[1], cols[0]:cols[1] ]
        """

    def drop_zeros(self, arrays: list[np.array], tolerance: float = -1)->list[np.array]:
        """Input a list of np.arrays of the same dimensions. Finds the columns and rows that are all zero in arrays[0],
        Drops the rows/columns of the 0th element of the input array that are all zeros from all arrays in the input.
        
        Input: arrays: list[np.array] -> arrays to drop zeros from using 0th item to determine what to drop
        
        Output: list[np.array] with rows/colums of zeros dropped"""
        drop_arr = arrays[0].copy()
        if tolerance == -1:
            min = np.min(np.absolute(drop_arr))
            var = np.var(drop_arr)
            tolerance = min+var

        drop_arr = arrays[0].copy()
        drop_arr[np.absolute(drop_arr) <= tolerance] = 0

        zero_rows = [i for i in range(drop_arr.shape[0]) if not drop_arr[i,:].any()]
        zero_cols = [i for i in range(drop_arr.shape[1]) if not drop_arr[:,i].any()]

        for i in range(len(arrays)):     
            arrays[i] = np.delete(arrays[i], zero_rows, axis=0)
            arrays[i] = np.delete(arrays[i], zero_cols, axis=1)   

        return arrays


    def set_name(self, bank_name: str):
        '''The name determines the titles of plots. To have no title, use set_name('')'''
        self.Bank_Info.data_name = bank_name

    def get_name(self) -> str:
        return self.Bank_Info.data_name

    def set_names(self, name: str):
        "Sets each data_name of the DataSet to the preset name code. "
        for i, S in enumerate(self.DataSets):
            match name:
                case "area":
                    area: str = f"{S.Info.chan_dims['area']}" + r"$\mu m^2$"
                    S.Info.data_name = area
                case "dims":
                    dims: str = f"{S.Info.chan_dims['len']}" + r"$\mu m\times$" + f"{S.Info.chan_dims['wid']}" +r"$\mu m$"
                    S.Info.data_name = dims
                case "gate":
                    S.Info.data_name = f"{S.Info.gate} gate"
                case "device_model":
                    S.Info.data_name = f"{S.Info.device_model}"
                case "device_number":
                    S.Info.data_name = f"Device #{S.Info.device_number}"
                case "file_code":
                    S.Info.data_name = S.Info.file_code
                case "test_type":
                    S.Info.data_name = S.Info.test_type
                case "misc":
                    S.Info.data_name = S.Info.misc
            
                case _:
                    S.Info.data_name = name

    def get_names(self)->list[str]:
        "Returns a list of data_names of the DataSet"
        return [Set.Info.data_name for Set in self.DataSets]

    def set_colorsRGB(self, colors: list[ list[float, float, float] ]):
        "Returns a list containing the RGB color tuples of all DataSets in the DataBank, in order."
        assert(len(self.DataSets) == len(colors))
        for color in colors:
            if len(color) != 3:
                print('Error: please provide a tuple of floats like of size 3 like so: (R, G, B)')
                assert(len(color) == 3)

        for i, S in enumerate(self.DataSets):
            S.set_colorRGB(colors[i])

    def get_colorsRGB(self)->list[float, float, float]:
        "Returns a list containing the RGB color tuples of all DataSets in the DataBank, in order."
        return [Set.color for Set in self.DataSets]


    def set_linestyles(self, linestyles:list[str]):
        """Sets each DataSet's ln_style to the linestyle contained in linestyles by matching indeces.
        e.i. DataSet[i].ln_style = linestyles[i]

        To set an individual DataSet's linestyle 'ln_style', use 
            'THISOBJECT.DataSets[i].ln_style = 'yourlinestyle' '

            Input: 
                line_styles: list of 'linestyle' parameter strings allowed by MatPlotLib.PyPlot
                            with number of elements corresponding to number of DataSets
                            stored in DataBank."""
        assert(len(self.DataSets) == len(linestyles))
        for i, line_style in enumerate(linestyles):
            self.DataSets[i].ln_style = line_style

    def set_markers(self, markers:list[str]):
        """Sets each DataSet's marker to the marker of markers, as determined by index.

        To set an individual DataSet's marker, use 
            'THISOBJECT.DataSets[i].marker = 'yourmarker' '

            Input: 
                markers: list of 'marker' parameter strings allowed by MatPlotLib.PyPlot
                            with number of elements corresponding to number of DataSets
                            stored in DataBank."""
        assert(len(self.DataSets) == len(markers))
        for i, line_style in enumerate(markers):
            self.DataSets[i].ln_style = line_style

# ==============================================================================
#               Plotter
# ==============================================================================
class Plotter(DataBank):       
    def __init__(self, Set: DataSet = None):
        super().__init__(Set)
        ### super inherits all attributes listed below ###
        # self.DataSets = []
        # self.X: list = []
        # self.Y: list = []
        # self.Z: list = []
        # self.domain: dict[str, list[float]] = {'x': (-float('inf'),float('inf')),
        #                 'y': (-float('inf'),float('inf')),
        #                 'z': (-float('inf'),float('inf'))
        #                 }
        # self.labels: dict[str, str] = {'x': None, 'y': None, 'z': None} # strings when set
        # self.scatter_plots: bool = False
        # self.show_fig: bool = True
        # self.auto_labels: bool = True
        # self.connectors: bool = False
        # self.show_legend: bool = True
        # self.Bank_Info: DataInfo = None
        # self.override: bool = False
        ###################################################

        self.ticks = {'x': '', 'y': '', 'z': ''}
        self.m_headers, self.m_axs_lbls = [], []
        self.data_to_be_plotted = {'x': '', 'y': '', 'z': ''}
        # self.ax_labels = {'x': '', 'y': '', 'z': ''}
        self.labels = {'x': '', 'y': '', 'z': ''}
        # self.labels: dict[str, str] = {'x': None, 'y': None, 'z': None} # strings when set
        self.mpl_ax: mpl.axes._axes.Axes = None
        self.mpl_fig: mpl.figure.Figure = None
        self.norm = None
        
        self.units = {'x': '', 'y': '', 'z': ''}
        self.scale = {'x': 1, 'y': 1, 'z': 1}
        self.colors: list = []
        self.names: list = []
        self.markers: list = []
        self.m_line_styles: list = []
        self.my_cmap = None
        self.cmap = None
        self.limits = {'x': [-5.1,5.1], 'y': [-5.1,5.1], 'z': []}
        self.legend_loc = 'upper left'
        self.legend_title = ''

        if len(self.DataSets) > 0:
            self.units = self.Bank_Info.units

            labels = [self.DataSets[0].get_data_name(0),
                    self.DataSets[0].get_data_name(1),
                    self.DataSets[0].get_data_name(-1)]

            labels = self.make_auto_labels(labels[0], labels[1], labels[2])
            self.title = self.Bank_Info.data_name
    
    def append(self, Set: DataSet):
        '''Method for adding DataSets to Plotter'''
        assert(type(Set) == DataSet)
        s_count = len(self.DataSets)
        if s_count == 0:
            self.DataSets.append(Set)
            self.Bank_Info = Set.Info.make_copy()
            self.title = self.Bank_Info.data_name
            self.units = self.Bank_Info.units
        elif Set.Info.gate == self.Bank_Info.gate and Set.Info.test_type == self.Bank_Info.test_type:
            self.DataSets.append(Set)
        else:
            if self.override:
                self.DataSets.append(Set)
            else:
                print("\nError in .append(): Mismatching gate/graph type. Cannot add this data to current set without override.\n")


    def print(self):
        '''Prints information about the Plotter and its DataSets.'''
        length = len(self.DataSets)
        print(f"Data Set count: {length}")
        if length == 0:
            print("No data sets loaded.")
            return
        print(f"Data Set length info:")
        for i in range(length):
            print(f" Data Set {i}'s x length: {self.DataSets[i].m_dim1_count}")
            print(f" Data Set {i}'s y length: {self.DataSets[i].m_dim2_count}")
        print(f"Plotter's gate type: {self.Bank_Info.gate}")
        print(f"Plotter's graph setting: {self.Bank_Info.test_type}")
        print(f"Plotter's attributes are set to...")
        print(f" Plotter.override      = {self.override}")
        print(f" Plotter.scatter_plots = {self.scatter_plots}")
        print(f" Plotter.show_fig      = {self.show_fig}")
        print(f" Plotter.connectors    =  {self.connectors}")

    def legend(self, ax: mpl.axes._axes.Axes):
        '''Given an matplotlib axis "ax", will create a plot's legend for the Plotter object,
        populating the legend with the names and line styles of the Plotter's DataSets. 
        If the Plotter has a non-empty legend_title, the a legend title matching the Plotter's
        legend_title attribute will be added to the legend.'''
        assert(type(ax) == mpl.axes._axes.Axes)
        
        for s in range(len(self.names)):
            if self.scatter_plots:
                plt.scatter([], [], # plot no data, just do this to get legend
                        color = self.colors[s], 
                        marker = self.markers[s],
                        label = self.names[s])
            else:
                plt.plot([], [], 
                        linestyle = self.m_line_styles[s],
                        color = self.colors[s], 
                        marker = self.markers[s],
                        label = self.names[s])
        if self.legend_title:
            ax.legend(title = self.legend_title, loc = self.legend_loc)
        else:
            ax.legend(loc= self.legend_loc) 


    def set_markers(self, markers):
        if type(markers) == list:
            self.markers = markers
        if type(markers) == str:
            self.markers = [markers]

    def set_legend_title(self, title: str):
        '''Sets the legend_title attribute to the provided title. 

            If title is set to an empty string, no legend title will be displayed,
            otherwise, the legend_title will be displayed as the set title. '''
        self.legend_title = title

    # def set_line_styles(self, line_styles):
    #     if type(line_styles) == list:
    #         self.markers = line_styles
    #     if type(line_styles) == str:
    #         self.markers = [line_styles]

    def get_data2d(self, x_idx, y_idx, copy_style: bool):
        '''
        indices
            x_idx = 'x'/'y' or 0/1 and will select data for x-axis of 2D plot
            y_idx = 2/3/-1 and will select data for y-axis of 2D plot
                the non-selected independent axis will be represented via sidebar 
            
            hint: to know which index correpsonds to what header, use the get_indices() method    
        
        copy_style: bool 
            True  -> will overwrite colors and markers with the DataSets'
            False -> will leave colors and markers untouched and set to user set values
                    to change markers or labels use their respective .set_markers()/.set_names() functions. 
        '''
        if len(self.DataSets) == 0:
            print("No data loaded, empty plot will be generated")
            return [], [], [], True, {}, []

        self.names: list = []
        if copy_style:
            self.colors: list = []
            self.markers: list = []
            self.m_line_styles: list = []

        if x_idx == 'x' or x_idx == 0:
            x_idx = [0, 'x']
            x2_idx = [1, 'y']
        elif x_idx == 'y' or x_idx == 1:
            x_idx = [1, 'y']
            x2_idx = [0, 'x']

        X, X2, Y = [], [], []

        for S in self.DataSets:
            x: list = S.get_data(x_idx[0])
            x2: list= S.get_data(x2_idx[0])
            y: list = S.get_data(y_idx)
            
            if x2_idx[0]: # if x2_idx is the 2nd indep variable (corresponding to y axis in 3d plot)
                cols = S.get_slicing(x_idx[0], self.domain[x_idx[1]]) # x vars by columns
                rows = S.get_slicing(x2_idx[0], self.domain[x2_idx[1]]) # y vars by rows
                x2 = x2[ rows[0]:rows[1], 0 ]
                x = x[ 0, cols[0]:cols[1] ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = False # the order of rows and columns is preserved
            else:
                # x varies by columns and y varies by rows, so if x_idx == 'y' and x2_idx == 'x'
                #   then the row and column slicing must be swapped accordingly.
                rows = S.get_slicing(x_idx[0], self.domain[x_idx[1]]) 
                cols = S.get_slicing(x2_idx[0], self.domain[x2_idx[1]]) 
                x2 = x2[ 0, cols[0]: cols[1] ]
                x = x[ rows[0]:rows[1], 0 ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = True # the order of rows and columns is flipped
            dim1, dim2, ydim = len(x), len(x2), len(y)

            X.append( x )
            X2.append(x2)
            Y.append( y )

            if copy_style:
                if rc_reversal and S.marker == '.':
                    self.markers.append(',')
                else:
                    self.markers.append(S.marker)
                self.colors.append(np.array(S.color))
                # self.line_styles.append(S.ln_style)
            self.names.append(S.Info.data_name)
            self.m_line_styles.append(S.ln_style)
        
        meta_col_data, meta_color_data = self.create_projection_mapping(X2)
        # selected_data = {'x':X, 'y':X2, 'z':Y}


        return X, X2, Y, rc_reversal, meta_col_data, meta_color_data                

    def colorbar(self, color_map, discrete:bool=False):
        '''Creates a colorbar given a color_map, which can either be a matplotlib-supported string keyword,
        or a dictionary of curve indices corresponding to RGB color triplet tuples.
        'discrete' => determines whether the colorbar is a continuous gradient or a discrete gradient. 
        '''

        min = -float('inf')
        max =  float('inf')
        X2 = self.data_to_be_plotted['y']
        print(X2)
        x2 = X2[0]
        for S in (X2):
                if min < S.min():
                    min = S.min()
                if max > S.max():
                    max = S.max()
        if type(color_map) == dict: 
            my_cmap = [shade*np.array(self.DataSets[0].color) for shade in color_map[0]]
            my_cmap = mpl.colors.ListedColormap(my_cmap)
        elif type(color_map) == str:
            # my_cmap = plt.get_cmap('coolwarm', 11)
            if discrete:
                my_cmap = plt.get_cmap(color_map, len(x2))
            else:
                my_cmap = plt.get_cmap(color_map)

        norm = plt.Normalize(min, max)
        self.norm = norm

        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p']
        print(letters)
        if discrete:
            step = (x2.max() - x2.min())/(len(x2))
            if step == 0:
                tick_locations = [x2[0]]
                tick_labels = [x2[0]]
            else:
                tick_locations = np.arange(x2.min(), x2.max() + step, step) 
                tick_locations += 0.5*step
                tick_labels = x2#[str(round(float(label), 2)) for label in x2]
        else:            
            step = (x2.max() - x2.min())/10
            if step == 0:
                tick_locations = x2[0]
                tick_labels = [x2[0]]
            else:
                tick_locations = np.arange(X2[0].min(), X2[0].max()+step, step)
                tick_labels = [str(round(float(label), 2)) for label in x2] # location of tick marks matches data
        print("Further in...")
        if discrete:
            print("Discrete")
            self.mpl_fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), 
                    ax = self.mpl_ax,
                    label=self.labels['y'], 
                    format=mpl.ticker.FixedFormatter( tick_labels ), # what values go on the tick marks
                    ticks = tick_locations# the location of where to put the tick marks on the colorbar relative to norm
                    )
        else:
            print("Not Discrete")
            self.mpl_fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), ax = self.mpl_ax,
                label=self.labels['y'], 
                format=mpl.ticker.FixedFormatter(tick_locations), # what values go on the tick marks
                ticks = tick_locations # the location of where to put the tick marks on the colorbar relative to norm
                )

    def _colorbar(self, X2, discrete, cmap, fig, ax1, label):
        ### HANDLE COLORBAR IMPLEMENTATION ###
        if type(cmap) == dict: 
            ###
            my_cmap = [shade*np.array(self.DataSets[0].color) for shade in cmap[0]]
            my_cmap = mpl.colors.ListedColormap(my_cmap)
        elif type(cmap) == str:
            if discrete:
                my_cmap = plt.get_cmap(cmap, len(X2[0]))
            else:
                my_cmap = plt.get_cmap(cmap)
    
        # make colorbar
        norm = plt.Normalize(X2[0].min(), X2[0].max())

        if discrete:
            step = (X2[0].max() - X2[0].min())/(len(X2[0]))
        else: 
            step = (X2[0].max() - X2[0].min())/10
        if step == 0: #step = (X2[0].max() - X2[0].min())/10
            tick_locations = [X2[0]]
            tick_labels = ['{:.2f}'.format(x) for x in X2[0]] # format single value 
        else:
            tick_locations = np.arange(X2[0].min(), X2[0].max() + step, step) 
            if not discrete:
                tick_labels = np.array(['{:.2f}'.format(tick) for tick in tick_locations]) # round to 2 decimals by default
            else:
                tick_labels = np.array(['{:.2f}'.format(tick) for tick in X2[0]]) # round to 2 decimals by default
            
        if discrete and step > 0: # align ticks with center of discrete colorbar colors
            tick_locations += 0.5*step            
        
        if not discrete:
            fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), 
                    ax = ax1,
                    label=label, 
                    format=mpl.ticker.FixedFormatter( tick_labels ), # what values go on the tick marks
                    ticks = tick_locations# the location of where to put the tick marks on the colorbar relative to norm
                    )
        else:
            fig.colorbar(mpl.cm.ScalarMappable(cmap=my_cmap, norm=norm), ax = ax1,
                label=label, 
                format=mpl.ticker.FixedFormatter(tick_labels), # what values go on the tick marks
                ticks = tick_locations # the location of where to put the tick marks on the colorbar relative to norm
                )


    def cmap_quick_plot3d(self, x_idx, y_idx, cmap:str = None, **kwargs):
        """Displays a 3D plot of the DataBank's contents with 
        user-set domain restriction, potential auto-labeling, and possible connectors.
        """        

        ### HANDLE EMPTY PLOT ###
        if len(self.DataSets) == 0:
            ### CREATE EMPTY PLOT ###
            fig, ax1 = plt.subplots(1, 1, subplot_kw={'projection': '3d'})

            print("No data loaded, empty plot generated\n")
            plt.show()
            return
        
        ### CREATE PLOT ###
        if 'figsize' in kwargs.keys():
            if type(kwargs['figsize']) == tuple and len(kwargs['figsize']) == 2: 
                figsize = kwargs['figsize']
                ### CREATE PLOT ###
                fig, ax1 = plt.subplots(
                    1, 1, 
                    figsize = figsize,
                    subplot_kw={'projection': '3d'})
            else:
                print(f"\nERROR: 'figsize' value of {kwargs['figsize']} not allowed.")
                print(" Must be formatted as a tuple of form (width:float, height:float).")
                print(" Defaulting to MatPlotLib's default figsize\n")
                raise ValueError(f"\nERROR: 'figsize' value of {kwargs['figsize']} not allowed.")
        else:
            ### CREATE PLOT ###
            fig, ax1 = plt.subplots(1, 1, subplot_kw={'projection': '3d'})        

        ### PROCESS KWARGS ###
        if 'pov' in kwargs.keys():
            if kwargs['pov'] == 'forwards': 
                pov = 'forwards'
            elif kwargs['pov'] == 'backwards':
                pov = 'backwards'
            else:
                print(f"\nERROR: 'pov' value of {pov} not allowed. Choose from either 'fowards' or 'backwards'. Defaulting to 'pov' of default 'forwards'")
                pov = 'forwards'
        else:
            pov = 'forwards'

        if 'cbar' in kwargs.keys():
            if kwargs['cbar'] == True:
                cbar: bool = True
            elif kwargs['cbar'] == False:
                cbar: bool = False
            else:
                print(f"\nERROR: 'cbar':bool value of {kwargs['cbar']} not allowed. Defaulting to 'cbar' of default True")
                cbar: bool = True
        else:
            cbar: bool = True

        if 'markers' in kwargs.keys():
            if kwargs['markers'] == True:
                markers_toggle: bool = True
            elif kwargs['markers'] == False:
                markers_toggle: bool = False
            else:
                print(f"\nERROR: 'markers':bool value of {kwargs['markers']} not allowed. Defaulting to 'cbar' of default False")
                markers_toggle: bool = False
        else:
            markers_toggle: list = True

        if 'discrete' in kwargs.keys():
            if kwargs['discrete'] == True: 
                discrete = True
            elif kwargs['discrete'] == False:
                discrete = False
            else:
                # print(f"\nERROR: 'discrete' value of {kwargs['discrete']} not allowed. Choose from either True or False. Defaulting to 'discrete' value of True.\n")
                raise ValueError(f"'discrete' value of {kwargs['discrete']} not allowed. Choose from either True or False. Note: default value of 'discrete' is True.\n")
        else:
            discrete = True
        
        if 'view_init' in kwargs.keys():
            if type(kwargs['view_init']) == tuple and len(kwargs['view_init'])==3: 
                ax1.view_init(elev = kwargs['view_init'][0],
                              azim = kwargs['view_init'][1],
                              roll = kwargs['view_init'][2]
                              )
            else:
                 raise ValueError(f"'view_init' value of {kwargs['view_init']} not allowed. Please create a 3 item tuple of (elevation, azimuthal angle, roll)\n")
        else:
            view_init_bool: bool = False


        ### PARSE USER INPUT ###
        if x_idx in [0, 'x']:
            x_idx = [0, 'x']
            x2_idx = [1, 'y']
        elif x_idx in [1, 'y']:
            x_idx = [1, 'y']
            x2_idx = [0, 'x']
        else:
            print(" Error: Invalid x_idx, choose from 0/'x' or 1/'y'")
            return

        ### PREPARE DATA STORAGE CONTAINERS###
        X, X2, Y, X2linear = [], [], [], []
        markers, colors, names, line_styles = [], [], [], []
        # line_names = []  

        ### PREP LABELS AND PLOT ###
        labels = [self.DataSets[0].get_data_name(x_idx[0]),
                    self.DataSets[0].get_data_name(x2_idx[0]),
                    self.DataSets[0].get_data_name(y_idx)]
        if self.auto_labels:
            labels = self.make_auto_labels(labels[0], labels[1], labels[2])

        ax1.set_xlabel(labels[0]) # sets x label on 2d plot
        ax1.set_ylabel(labels[1]) # sets y label on 2d plot
        ax1.set_zlabel(labels[2]) # sets y label on 2d plot

        ax1.set_title(self.Bank_Info.data_name)

        ### FILL DATA CONTAINERS WITH DATA ###
        for S in self.DataSets:
            x: list = S.get_data(x_idx[0])
            x2: list= S.get_data(x2_idx[0])
            y: list = S.get_data(y_idx)
            
            if x2_idx[0]: # if x2_idx is the 2nd indep variable (corresponding to y axis in 3d plot)
                cols = S.get_slicing(x_idx[0], self.domain[x_idx[1]]) # x vars by columns
                rows = S.get_slicing(x2_idx[0], self.domain[x2_idx[1]]) # y vars by rows
                rc_reversal = False # the order of rows and columns is preserved
            else:
                # x varies by columns and y varies by rows, so if x_idx == 'y' and x2_idx == 'x'
                #   then the row and column slicing must be swapped accordingly.
                rows = S.get_slicing(x_idx[0], self.domain[x_idx[1]]) 
                cols = S.get_slicing(x2_idx[0], self.domain[x2_idx[1]])     
                rc_reversal = True # the order of rows and columns is flipped
            x2linear = x2[ rows[0]:rows[1], 0 ]
            x2 = x2[ rows[0]:rows[1], cols[0]:cols[1] ]
            x  =  x[ rows[0]:rows[1], cols[0]:cols[1] ]
            y  =  y[ rows[0]:rows[1], cols[0]:cols[1] ]
            dim1, dim2, ydim = len(x), len(x2), len(y)

            X.append( x )
            X2.append(x2)
            Y.append( y )
            X2linear.append(x2linear)

            if rc_reversal and S.marker == '.':
                markers.append(',')
            else:
                markers.append(S.marker)
            colors.append(np.array(S.color))
            names.append(S.Info.data_name)
            line_styles.append(S.ln_style)

        if markers_toggle == False: 
            markers = ['' for marker in markers]    

        meta_col_data, meta_color_data = self.create_projection_mapping(X2)

        ### DETERMINE DATA PLOTTING ORDERING ###
        if pov == 'forwards': 
            columns = reversed(meta_col_data.keys())
        elif pov == 'backwards':
            columns = meta_col_data.keys()

        ### COLORMAP HANDLING ###
        if cmap:
            cmap = cmap # sets the current cmap in arg to the cmap used
        else:
            cmap = meta_color_data #sets to the calculated cmap

        if type(cmap) == dict: 
            my_cmap = mpl.colors.ListedColormap(cmap)
            for col in columns:
                for s in meta_col_data[col]:
                    colors.append(np.array([meta_color_data[s][col] * colors[s]]))

        elif type(cmap) == str:
            if discrete:
                my_cmap = plt.get_cmap(cmap, len(X2linear[0]))
            else:
                my_cmap = plt.get_cmap(cmap)
            colors = my_cmap(plt.Normalize(X2[0].min(), X2[0].max())(X2[0]))

        ### CREATE COLORBAR ###
        if cbar:
            self._colorbar(X2linear, discrete, cmap, fig, ax1, labels[1])

        ### PLOT DATA ###
        for col in columns:
            for s in meta_col_data[col]:
                # Plot Data
                if not rc_reversal:
                    if self.scatter_plots:
                        ax1.scatter(X[s][col], X2[s][col, :], Y[s][col],
                                color = colors[col][0], 
                                marker = markers[s])
                    else:
                        ax1.plot(X[s][col], X2[s][col, :], Y[s][col],
                            color = colors[col][0],
                            linestyle = line_styles[s],
                            marker = markers[s]
                            )
                else:
                    print("\nERROR: plotting along 'y' direction not yet supported\n")
                    plt.show()
                    return
                    # ax1.scatter(X[s][col, :], X2[s][:, col], Y[s][col, :],
                    #             color = colors[col][0], 
                    #             marker = markers[s])

        ### CREATE LEGEND ###
        if self.show_legend:

            if type(cmap) == str: # if a preset colormap is being used, 
                colors = [(0, 0, 0) for color in colors] # set all line colors to black
            for s in range(len(names)):
                if self.scatter_plots:
                    ax1.scatter([], [], # plot no data, just do this to get legend
                            color = colors[s], 
                            marker = markers[s],
                            label = names[s])
                else:
                    ax1.plot([], [], 
                            linestyle = line_styles[s],
                            color = colors[s], 
                            marker = markers[s],
                            label = names[s])
        
            plt.legend(loc='upper left')

        if self.show_fig:
            plt.show()


    def plot_data2d(self, X, X2, Y, rc_reversal, meta_col_data, meta_color_data, ax):
        ''' Unimplemented function; do not use.
        indices
            x_idx = 'x'/'y' or 0/1 and will select data for x-axis of 2D plot
            y_idx = 2/3/-1 and will select data for y-axis of 2D plot
            the non-selected independent axis will be represented via sidebar 
        hint: to know which index correpsonds to what header, use the get_indices() method    
        '''
        for col, sets in meta_col_data.items():
            for s in sets:
                if type(meta_color_data) == dict:
                    color = meta_color_data[s][col] * self.colors[s]
                else: # type(meta_col_data) == mpl.colors.LinearSegmentedColormap:
                    my_cmap = plt.get_cmap(meta_color_data)
                    color = my_cmap( int(256*plt.Normalize(X2[0].min(0),X2[0].max(0))(X2[s][col])) )
                if not rc_reversal:
                    if self.scatter_plots:
                        ax.scatter(X[s], Y[s][col, :], 
                                color = color,
                                marker = self.markers[s])
                    else:
                        ax.plot(X[s], Y[s][col, :], 
                                color = color,
                                marker = self.markers[s])
                else:
                    ax.scatter(X[s], Y[s][:, col], 
                                color = color, 
                                marker = self.markers[s])

    def quick_div_plot2d(self, x_idx, y_idx, DivSet:DataSet, divIdx, drop_zeros=True, tolerance: float = -1, cmap:str = None):
        ''''''
        if self.mpl_fig and self.mpl_ax: 
            print("Configuring provided MatPlotLib plotting object")
        else:
            mpl_fig, mpl_ax =  plt.subplots(1)#, figsize = (6, 4))
        
        ### PARSE USER INPUT ###
        if x_idx in [0, 'x']:
            x_idx = [0, 'x']
            x2_idx = [1, 'y']
        elif x_idx in [1, 'y']:
            x_idx = [1, 'y']
            x2_idx = [0, 'x']
        else:
            print(" Error: Invalid x_idx, choose from 0/'x' or 1/'y'")
            return


        X, X2, Y, rc_reversal = self.get_div_data2d(x_idx[1], y_idx, DivSet,divIdx, drop_zeros, tolerance)
        meta_col_data, meta_color_data = self.create_projection_mapping(X2)
        # if cmap_name:
        #     cmap = cmap_name
        # else:
        #     cmap = meta_color_data


        ### PREP LABELS AND PLOT ###
        if self.auto_labels:
            labels = [self.DataSets[0].get_data_name(x_idx[0]),
                    self.DataSets[0].get_data_name(x2_idx[0]),
                    'div']
            labels = self.make_auto_labels(labels[0], labels[1], labels[2])

        else:
            labels = self.labels

        mpl_ax.set_xlabel(labels[0]) # sets x label on 2d plot
        mpl_ax.set_ylabel(labels[2]) # sets y label on 2d plot
        
        mpl_ax.set_title(f"Performance Plot Relative to {DivSet.Info.data_name}")
        if self.show_legend:
            self.legend(mpl_ax)
        # colorbar needs self.data_to_be_plotted['y'], so to not "modify" 
        #  that, we'll store it, set it differently, then restore it 
        
        ### HANDLE COLORBAR IMPLEMENTATION ###
        if cmap:
            cmap = cmap # sets the current cmap in arg to the cmap used
        else:
            cmap = meta_color_data #sets to the calculated cmap

        
        # COLORBAR IMPLEMENTATION
        
        # ### HANDLE COLORBAR IMPLEMENTATION ###
        # if cbar == True:
        if len(X2[0]) < 21:
            discrete = True
        else:
            discrete = False
        # print(discrete)
        self._colorbar(X2, discrete, cmap, mpl_fig, mpl_ax, labels[1])

        self.plot_data2d(X, X2, Y, 
            rc_reversal, meta_col_data, cmap, mpl_ax)
        if self.show_fig: 
            plt.show()

    def quick_plot2d(self, x_idx, y_idx, **kwargs):
        """Given the selected independent x-axis and dependent y-axis, generate a 2D plot projected
            onto the second independent x2-axis, representing x2 via greyscaling.
        Input: 
            x_idx = 'x'/'y' or 0/1 and will select data for x-axis of 2D plot
            y_idx = 2/3/-1 and will select data for y-axis of 2D plot
                  the non-selected independent axis will be represented via sidebar 
            hint: to know which index correpsonds to what header, use the get_indices() method    
        """
        if len(self.DataSets) == 0:
            print("No data loaded, empty plot generated")
            plt.show()
            return

        # for k, val in kwargs.items():
        #     print("%s == %s" % (k, val))

        ### PROCESS KWARGS ###
        if 'cmap' in kwargs.keys():
            if type(kwargs['cmap']) == str: 
                cmap = kwargs['cmap']
            elif kwargs['cmap'] == None:
                cmap = None
            else:
                print(f"\nERROR: 'cmap' value of {cmap} not allowed.")
                print(" Choose from either None type or MatPlotPlib's allowed cmap's as specific by their corresponding str label.")
                print(" Defaulting to 'cmap' of default None")
                cmap = None
        else:
            cmap = None

        if 'cbar' in kwargs.keys():
            if kwargs['cbar'] == True:
                cbar: bool = True
            elif kwargs['cbar'] == False:
                cbar: bool = False
            else:
                print(f"\nERROR: 'cbar':bool value of {kwargs['cbar']} not allowed. Defaulting to 'cbar' of default True\n")
                cbar: bool = True
        else:
            cbar: bool = True

        if 'markers' in kwargs.keys():
            if kwargs['markers'] == True:
                markers_toggle: bool = True
            elif kwargs['markers'] == False:
                markers_toggle: bool = False
            else:
                print(f"\nERROR: 'markers':bool value of {kwargs['markers']} not allowed. Defaulting to 'cbar' of default False\n")
                markers_toggle: bool = False
        else:
            markers_toggle: list = True

        if 'discrete' in kwargs.keys():
            if kwargs['discrete'] == True: 
                discrete = True
            elif kwargs['discrete'] == False:
                discrete = False
            else:
                print(f"\nERROR: 'discrete' value of {kwargs['discrete']} not allowed. Choose from either True or False. Defaulting to 'discrete' value of True\n")
                discrete = True
        else:
            discrete = True

        if 'legend_loc' in kwargs.keys():
            legend_loc = kwargs['legend_loc']
        else:
            legend_loc = 'upper left'

        ### CREATE PLOT ###
        if 'figsize' in kwargs.keys():
            if type(kwargs['figsize']) == tuple and len(kwargs['figsize']) == 2: 
                figsize = kwargs['figsize']
                ### CREATE PLOT ###
                fig, ax1 = plt.subplots(
                    1, figsize = figsize)
            else:
                print(f"\nERROR: 'figsize' value of {kwargs['figsize']} not allowed.")
                print(" Must be formatted as a tuple of form (width:float, height:float).")
                print(" Defaulting to MatPlotLib's default figsize\n")
                ### CREATE PLOT ###
                fig, ax1 = plt.subplots(1)
        else:
            ### CREATE PLOT ###
            fig, ax1 = plt.subplots(1)

        # else:
            # figsize = (8, 6)
                # print(" Defaulting to 'figsize' value of figsize = {figsize}\n")


        ### PROCESS USER INPUT ###
        if x_idx in [0, 'x']:
            x_idx = [0, 'x']
            x2_idx = [1, 'y']
        elif x_idx in [1, 'y']:
            x_idx = [1, 'y']
            x2_idx = [0, 'x']
        else:
            print(" Error: Invalid x_idx, choose from 0/'x' or 1/'y'")
            return



        ### PREP DATA CONTAINERS ###
        X, X2, Y = [], [], []
        markers, colors, names, line_styles = [], [], [], []


        ### HANDLE LABELLING ###
        labels = [self.DataSets[0].get_data_name(x_idx[0]),
                    self.DataSets[0].get_data_name(x2_idx[0]),
                    self.DataSets[0].get_data_name(y_idx)]
        if self.auto_labels:
            labels = self.make_auto_labels(labels[0], labels[1], labels[2])

        ax1.set_xlabel(labels[0]) # sets x label on 2d plot
        ax1.set_ylabel(labels[2]) # sets y label on 2d plot

        ax1.set_title(self.Bank_Info.data_name)

        ### FILL CONTAINERS WITH DATASET DATA ###
        for S in self.DataSets:
            x: list = S.get_data(x_idx[0])
            x2: list= S.get_data(x2_idx[0])
            y: list = S.get_data(y_idx)
            
            if x2_idx[0]: # if x2_idx is the 2nd indep variable (corresponding to y axis in 3d plot)
                cols = S.get_slicing(x_idx[0], self.domain[x_idx[1]]) # x vars by columns
                rows = S.get_slicing(x2_idx[0], self.domain[x2_idx[1]]) # y vars by rows
                x2 = x2[ rows[0]:rows[1], 0 ]
                x = x[ 0, cols[0]:cols[1] ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = False # the order of rows and columns is preserved
            else:
                # x varies by columns and y varies by rows, so if x_idx == 'y' and x2_idx == 'x'
                #   then the row and column slicing must be swapped accordingly.
                rows = S.get_slicing(x_idx[0], self.domain[x_idx[1]]) 
                cols = S.get_slicing(x2_idx[0], self.domain[x2_idx[1]]) 
                x2 = x2[ 0, cols[0]: cols[1] ]
                x = x[ rows[0]:rows[1], 0 ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = True # the order of rows and columns is flipped
            dim1, dim2, ydim = len(x), len(x2), len(y)

            X.append( x )
            X2.append(x2)
            Y.append( y )

            if rc_reversal and S.marker == '.':
                markers.append(',')
            else:
                markers.append(S.marker)
            colors.append(np.array(S.color))
            names.append(S.Info.data_name)
            line_styles.append(S.ln_style)

        meta_col_data, meta_color_data = self.create_projection_mapping(X2)

        ### HANDLE COLORBAR IMPLEMENTATION ###
        if cmap:
            cmap = cmap # sets the current cmap in arg to the cmap used
        else:
            cmap = meta_color_data #sets to the calculated cmap

        # ### HANDLE COLORBAR IMPLEMENTATION ###
        if cbar == True:
            self._colorbar(X2, discrete, cmap, fig, ax1, labels[1])

        if markers_toggle == False: 
            markers = ['' for marker in markers]    
        for col, sets in meta_col_data.items():
            for s in sets:
                if type(cmap) == dict:
                    color = meta_color_data[s][col] * colors[s]
                else: # type(meta_col_data) == mpl.colors.LinearSegmentedColormap:
                    my_cmap = plt.get_cmap(cmap)
                    color = my_cmap( int(256* plt.Normalize(X2[0].min(), X2[0].max())(X2[s][col])) )
                if not rc_reversal:
                    if self.scatter_plots:
                        ax1.scatter(X[s], Y[s][col, :], 
                                color = color, 
                                linestyle = line_styles[s],
                                marker = markers[s]
                                )
                    else:
                        ax1.plot(X[s], Y[s][col, :], 
                                color = color,
                                linestyle = line_styles[s],
                                marker = markers[s])
                else:
                    ax1.scatter(X[s], Y[s][:, col], 
                                color = color, 
                                linestyle = line_styles[s],
                                marker = markers[s])
        if self.show_legend:
            if type(cmap) == str: # if a preset colormap is being used, 
                colors = [(0, 0, 0) for color in colors] # set all line colors to black
            for s in range(len(names)):
                if self.scatter_plots:
                    ax1.scatter([], [], # plot no data, just do this to get legend
                            color = colors[s], 
                            marker = markers[s],
                            label = names[s])
                else:
                    ax1.plot([], [], 
                            linestyle = line_styles[s],
                            color = colors[s], 
                            marker = markers[s],
                            label = names[s])
            if self.legend_title:
                ax1.legend(title = self.legend_title, loc = legend_loc)
            else:
                ax1.legend(loc=legend_loc) 

        if self.show_fig:
            plt.show()

    def div_plot2d(self, x_idx, y_idx, DivSet:DataSet, divIdx, drop_zeros=True, tolerance: float = -1):
        '''Unfinished function; do not use.'''
        X, X2, Y, rc_reversal = self.get_div_data2d(x_idx, y_idx, DivSet,divIdx, drop_zeros, tolerance)
        meta_col_data, meta_color_data = self.create_projection_mapping(X2)

        #self.get_div_data2d('x', -1)
        data = {'x': X, 'y': X2, 'z': Y}
        # self.load_data2d()
        self.data_to_be_plotted = data

        labels = [self.DataSets[0].get_data_name(0),
                    self.DataSets[0].get_data_name(1),
                    'div']

        temp = self.make_auto_labels(labels[0], labels[1], labels[2])
        labels[0] = temp[0]
        labels[1] = temp[1]

        self.labels['x'] = labels[0]
        self.labels['y'] = labels[1]
        self.labels['z'] = 'Relative Performance'

        self.legend_title = False
        self.title = f"Performance Plot Relative to {DivSet.Info.data_name}"
        # ax1.set_title()
                

        # self.preconfig2d('It')
        # self.prep_plot2d(True, True)

        # self.preconfig2d('It')
        self.prep_plot2d(False, False)
            # self.plot_data2d(X, X2, Y, rc_reversal, meta_col_data, meta_color_data)
        # self.legend()

        # meta_color_data = 'coolwarm'
        self.colorbar(meta_color_data, discrete=True)

        self.plot_data2d(self.data_to_be_plotted['x'], 
        self.data_to_be_plotted['y'], 
        self.data_to_be_plotted['z'], 
        rc_reversal, meta_col_data, meta_color_data)


        self.print_plot()


    def get_div_data2d(self, x_idx, y_idx, DivSet: DataSet, divIdx, drop_zeros=False, tolerance: float = -1, copy_style:bool=True):
        '''
        indices
            x_idx = 'x'/'y' or 0/1 and will select data for x-axis of 2D plot
            y_idx = 2/3/-1 and will select data for y-axis of 2D plot
            the non-selected independent axis will be represented via sidebar 
        hint: to know which index correpsonds to what header, use the get_indices() method    
        '''
        if len(self.DataSets) == 0:
            print("No data loaded, empty plot will be generated")
            return [], [], [], True, {}, []

        div_data_dims = (DivSet.m_dim1_count, DivSet.m_dim2_count)

        self.names: list = []
        if copy_style:
            self.colors: list = []
            self.markers: list = []
            self.m_line_styles: list = []


        if x_idx in ['x', 0]:
            x_idx, x2_idx = 'x', 'y'
        elif x_idx in ['y', 1]:
            x_idx, x2_idx = 'y', 'x'
        else:
            print("Invalid axis selected: pick from 0/'x' or 1/'y'")
            return

        X, X2, Y = [], [], []

        for i, S in enumerate(self.DataSets):
            S_data_dims = (S.m_dim1_count, S.m_dim2_count)

            # if dimensinos mismatch, omit the data set
            if S_data_dims != div_data_dims:
                print(f"DataSet at index ({i}) does not have matching x,y array dimensions of the dividing DataSet")
                print(f"\t{S_data_dims} =/= {div_data_dims}")
                print(f"Skipping DataSet ({i}) in DataBank")
                # add a "skipped DataSets" list here to keep track of for labelling later down the line
                continue

            ydiv: list = DivSet.get_data(divIdx)
            x: list = S.get_data(self.process_axis(x_idx, num_output=True))
            x2: list= S.get_data(self.process_axis(x2_idx, num_output=True))
            y: list = S.get_data(y_idx)/ydiv

            if drop_zeros:
                ydiv, x, x2, y = self.drop_zeros([ydiv, x, x2, y], tolerance)


            if x2_idx == 'y': # if x2_idx is the 2nd indep variable (corresponding to y axis in 3d plot)
                cols = self.get_slicing(x_idx, self.domain[x_idx], x) # x vars by columns
                rows = self.get_slicing(x2_idx, self.domain[x2_idx], x2) # y vars by rows
                x2 = x2[ rows[0]:rows[1], 0 ]
                x = x[ 0, cols[0]:cols[1] ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = False # the order of rows and columns is preserved
            else:
                # x varies by columns and y varies by rows, so if x_idx == 'y' and x2_idx == 'x'
                #   then the row and column slicing must be swapped accordingly.
                rows = self.get_slicing(x_idx, self.domain[x_idx], x) 
                cols = self.get_slicing(x2_idx, self.domain[x2_idx], x2) 
                x2 = x2[ 0, cols[0]: cols[1] ]
                x = x[ rows[0]:rows[1], 0 ]
                y = y[ rows[0]:rows[1], cols[0]:cols[1] ]
                rc_reversal = True # the order of rows and columns is flipped

            X.append( x )
            X2.append(x2)
            Y.append( y )

            if rc_reversal and S.marker == '.':
                self.markers.append(',')
            else:
                self.markers.append(S.marker)
            self.colors.append(np.array(S.color))
            self.m_line_styles.append(S.ln_style)
            self.names.append(S.Info.data_name)
        
        # meta_col_data, meta_color_data = self.create_projection_mapping(X2)

        return X, X2, Y, rc_reversal               

    def print_plot(self):
        plt.show()


    def prep_plot2d(self, include_lim = True, include_ticks = True):
        '''Unimplemented function; do not use.'''
        mpl.rcParams['mathtext.default'] = 'regular'
        if self.mpl_fig and self.mpl_ax: 
            print("Configuring provided MatPlotLib plotting object")
        else:
            self.mpl_fig, self.mpl_ax = fig, ax1 = plt.subplots(1)#, figsize = (6, 4))

        if include_lim:
            # print(self.limits)
            plt.xlim(self.limits['x'][0], self.limits['x'][1])
            plt.ylim(self.limits['y'][0], self.limits['y'][1])
        if include_ticks:
            plt.xticks(self.ticks['x'], self.ticks['x']); plt.yticks(self.ticks['y'], self.ticks['y'])
        plt.xlabel(self.labels['x']); plt.ylabel(self.labels['z'])
        plt.grid(True, which='both', ls='-')
        plt.axhline(color = 'gray'); plt.axvline(color = 'gray')
        if self.show_legend:
            self.legend()
        

        if self.title:
            plt.title(self.title)
        plt.axhline(color = 'gray'); plt.axvline(color = 'gray')


#     def prep_animation(self):
#         fig, ax = plt.subplots()
#         self.lines = []
#         for i, Set in enumerate(self.m_DataBank.DataSets):
#             print(Set.ln_style)
#             line, = (ax.plot(self.m_DataBank.DataSets[0].m_x_data, self.m_DataBank.DataSets[0].m_y_data[i],color = Set.color, label = Set.m_headers[1],ls = Set.ln_style))
#             self.lines.append(line)
    
#     def update2(self, frame):
#         for count, Set in enumerate(self.m_DataBank.DataSets):
#             scale = 1-0.5*(frame/len(Set.m_y_data))
#             color = (Set.color[0] * scale, Set.color[1] * scale, Set.color[2] * scale)
#             #if It.m_DataBank.Bank_Info.test_type == 0:
#             #    label = f"{It.m_DataBank.DataSets[count].Info.dimensions[0]} μm x {It.m_DataBank.DataSets[count].Info.dimensions[1]} μm"
            
#             self.lines[count].set_color(color)
#             self.lines[count].set_label = Set.m_headers[frame+1]
#             self.lines[count].set_xdata(self.m_DataBank.DataSets[count].m_x_data)
#             self.lines[count].set_ydata(self.m_DataBank.DataSets[count].m_y_data[frame])
#         #print(len(self.lines))
#         return self.lines


#     def animate(self):
#         self.prep_animation()
#         fig, ax = plt.subplots()
#         frames = len(self.m_DataBank.DataSets[0].m_y_data)
#         print(frames)
#         ani = animation.FuncAnimation(fig=fig, func=self.update2, frames= frames, interval=300)
#         plt.show()




    def preconfig3d(self, graph_code: str):
        ''' Unimplemented function; do not use.
        ex: 'It' -> current plot, top gate'''
        if graph_code[1].lower() == 't':
            gate = 't'
            self.title = 'Top Gate Operation'
        elif graph_code[1].lower() == 'b':
            gate = 'b'
            self.title = 'Bottom Gate Operation'

        if graph_code[0] in [0, 'R', 'r']:
            self.Rds_v_Vgs_preconfig(gate)
            self.title = 'Resistance Plot With '+self.title
        elif graph_code[0] in [1, 'I', 'i']:
            self.Id_v_Vds_preconfig(gate)
            self.title = 'Current Plot with '+self.title
        elif graph_code[0] in [-1, 'D', 'd']:
            self.div_plot_preconfig(gate)
            self.title = 'Relative Operation to Baseline Test'
        else:
            print(f"Could not find matching preconfigured graph settings for preset {graph_code}.")
    
    def preconfig2d(self, graph_code: str):
        '''Unimplemented function; do not use.
        ex: 'It' -> current plot, top gate
            dependent_axis = 'z' -> '''
        if graph_code[1].lower() == 't':
            gate = 't'
            self.title = 'Top Gate Operation'
        elif graph_code[1].lower() == 'b':
            gate = 'b'
            self.title = 'Bottom Gate Operation'

        if graph_code[0] in [0, 'R', 'r']:
            self.Rds_v_Vgs_preconfig(gate)
            self.title = 'Resistance Plot With '+self.title
        elif graph_code[0] in [1, 'I', 'i']:
            self.Id_v_Vds_preconfig(gate)
            self.title = 'Current Plot with '+self.title
        elif graph_code[0] in [-1, 'D', 'd']:
            self.div_plot_preconfig(gate)
            self.title = 'Relative Operation to Baseline Test'
        else:
            print(f"Could not find matching preconfigured graph settings for preset {graph_code}.")


    def Rds_v_Vgs_preconfig(self, gate):
        '''Unimplemented function; do not use.'''
        # self.set_units('z', 'kΩ')
        # self.units['y'] = 'kΩ'
        self.set_scale('z', 'k') 
        # self.set_units('y', 'V')
        # self.units['x'] = 'V'
        print(f'Preconfiguring plot to settings:')
        if self.is_top(gate):
            print('Drain-source resistance as a function of top gate voltage.')
            self.title = r'$R_{DS}$ vs $V_{TGS}$ (const $V_{DS}$)'
            #plt.title(r'Bottom-Gate Voltage Effect on GFET Resistance')
            self.labels['x'] = r'Top-gate voltage $V_{BGS}$'+f' ({self.text_prefix(self.scale['x'])+self.units['x']})'
            self.ln_style = '-'
        else:
            print('Drain-source resistance as a function of bottom gate voltage.')  #plt.title(r'Top-Gate Voltage Effect on GFET Resistance')
            self.title = r'$R_{DS}$ vs $V_{BGS}$ (const $V_{DS}$)'
            self.labels['x']= r'Bottom-gate voltage $V_{BGS}$'+f' ({self.text_prefix(self.scale['x'])+self.units['x']})'
            self.ln_style = '--'
        y_ticks = [0, 1, 2, 3, 4, 5, 6]
        x_ticks = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
        # self.ticks['x'] = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
        # self.ticks['y'] = [0, 1, 2, 3, 4, 5]
        self.ticks['x'] = x_ticks
        self.ticks['y'] = y_ticks
        self.set_limit('x', x_ticks[0], x_ticks[-1])
        self.set_limit('y', y_ticks[0], y_ticks[-1])

        self.labels['z'] = r'Drain-source resistance $R_{DS}$'+f' ({self.text_prefix(self.scale['z'])+self.units['z']})' 
        self.legend_loc='lower right'
        self.legend_title = ''
        
            
    def Id_v_Vds_preconfig(self, gate):
        '''Unimplemented function; do not use.'''
        # self.set_units('z', 'mA')
        # self.units['y'] = 'mA'
        self.set_scale('z', 'm') 
        # self.set_units('y', 'V')
        # self.units['x'] = 'V'
        print(f'Preconfiguring plot to settings:')
        print('Drain-source current as a function of D->S voltage')
        if gate in ['top', 't']:#self.is_top(gate):
            print('With different constant top gate voltages')    
            self.title = r'$I_{DS}$ vs $V_{DS}$ (const $V_{TGS}$)'
            self.ln_style = '-'
        else:
            print('With different constant bottom gate voltages')
            self.title = r'$I_{DS}$ vs $V_{DS}$ (const $V_{BGS}$)'
            self.ln_style = '--'
        self.labels['z'] = r'Drain-source current $I_{DS}$' + f' ({self.text_prefix(self.scale['z'])+self.units['z']})'
        self.labels['x'] = r'Drain-source voltage $V_{DS}$' + f' ({self.text_prefix(self.scale['x'])+self.units['x']})'
        x_ticks = [i for i in range(-5, 6, 1)]
        
        # y_ticks = [0.001*i for i in range(-5, 6, 1)]
        #self.y_ticks = [-0.005, -0.004, -0.003, -0.002, -0.001, 0, 0.001, 0.002, 0.003, 0.004, 0.005]
        y_ticks = x_ticks ##THIS IS IN mA!!! Only works if set_scale('m', False) works!
        self.legend_loc='lower right'
        self.legend_title = 'Gate Voltage'
        self.ticks['x'] = x_ticks
        self.ticks['y'] = y_ticks
        
        # self.set_limit('x', -5, 5)
        # self.set_limit('y', -5, 5)
        # print(self.limits['x'], self.limits['y'])
        # print(self.xlim, self.ylim)

    def div_plot_preconfig(self, gate, axis):
        '''Unimplemented function; do not use.'''
        labels = self.make_auto_labels(self, self.labels['x'], self.labels['y'], self.labels['z'])#make_auto_labels(self, xlbl, ylbl, zlbl)
        print(f'Preconfiguring plot to settings:')
        print('Division Plot Measuring Relative Perforance')
        if self.is_top(gate):
            print('With different constant top gate voltages')    
            # self.title = r'$I_{DS}$ vs $V_{DS}$ (const $V_{TGS}$)'
            self.ln_style = '-'
        else:
            print('With different constant bottom gate voltages')
            # self.title = r'$I_{DS}$ vs $V_{DS}$ (const $V_{BGS}$)'
            self.ln_style = '--'
        self.labels['z'] = 'Operational Coefficient' 
        self.labels['x'] = r'Drain-source voltage $V_{DS}$' + f' ({self.text_prefix(self.scale['x'])+self.units['x']})'
        x_ticks = [i for i in range(-5, 6, 1)]
        
        # y_ticks = [0.001*i for i in range(-5, 6, 1)]
        #self.y_ticks = [-0.005, -0.004, -0.003, -0.002, -0.001, 0, 0.001, 0.002, 0.003, 0.004, 0.005]
        y_ticks = x_ticks ##THIS IS IN mA!!! Only works if set_scale('m', False) works!
        self.legend_loc='lower right'
        self.legend_title = 'Gate Voltage'
        self.ticks['x'] = x_ticks
        self.ticks['y'] = y_ticks
        
    
    def plot2d(self, x_idx, y_idx, copy_style:bool ):
        '''Unfinished function; do not use.'''
        X, X2, Y, rc_reversal, meta_col_data, meta_color_data = self.get_data2d(x_idx, y_idx, copy_style)
        meta_col_data, meta_color_data = self.create_projection_mapping(X2)
        if self.my_cmap:
            cmap = self.my_cmap
        else:
            cmap = meta_color_data
        data = {'x': X, 'y': X2, 'z': Y}
        # self.load_data2d()
        self.data_to_be_plotted = data
        self.prep_plot2d(True, False)
        self.set_scale('z', 'm')

        # self.plot_data2d(X, X2, Y, rc_reversal, meta_col_data, meta_color_data)
        if self.scatter_plots:
            self.plot_data2d(self.data_to_be_plotted['x'], 
                            self.data_to_be_plotted['y'], 
                            self.data_to_be_plotted['z'], 
                            rc_reversal, meta_col_data, cmap)
        
        else:
            self.plot_data2d(self.data_to_be_plotted['x'], 
                            self.data_to_be_plotted['y'], 
                            self.data_to_be_plotted['z'], 
                            rc_reversal, meta_col_data, cmap)
        

        self.print_plot()

    # def plot3d(self):
    #     self.plot_data3d()
    #     self.prep_plot3d()
    #     self.print_plot()


    def change_scale(self, axis, factor, prefix = ''):
        '''Unfinished function; do not use.
        Multiplies the data_to_be_plotted of the specified axis by a scaling factor'''
        # need to impliment thing that checks base scale before multiplying by factor
        axis = self.process_axis(axis)
        if prefix and factor != 1: # if a standard scaling via metric prefix is used...
            for s in range(len(self.data_to_be_plotted[axis])): 
                self.data_to_be_plotted[axis][s] /= factor # scale all data by that prefix 
                self.scale[axis] = factor
        else:
            current_scaling = self.scale[axis]
            if current_scaling != 1:
                print(f"Scaling by factor of {factor} from current scaling of {current_scaling}.")
                for s in range(len(self.data_to_be_plotted[axis])): 
                    self.data_to_be_plotted[axis][s] /= factor # scale all data by that prefix 
                    self.scale[axis] = factor

    def set_scale(self, axis, prefix: str):
        '''Unimplemented function; do not use.'''
        axis = self.process_axis(axis)
        prefix, factor = self.process_prefix(prefix)
        prefixes = ['n', 'u', 'μ', 'm', 'c', 'd', '', 'k', 'M' 'G']
        # if prefix in prefixes and prefix != self.text_prefix(self.scale[axis]):
            # change prefix 
            # self.scale[axis] = prefix
        self.change_scale(axis, factor, prefix)


    def process_prefix(self, prefix: str):
        '''Unimplemented function.
        Given a text prefix, return the scaling factor'''
        factor = 1
        if not prefix or prefix.lower() == 'none':
            factor = 1; prefix = ''
        elif prefix == 'n' or prefix.lower() == 'nano':
            factor = 1e-9; prefix = 'n'
        elif prefix == 'μ' or prefix == 'u' or prefix.lower() == 'micro':
            factor = 1e-6; prefix = 'μ'
        elif prefix == 'm' or prefix.lower() == 'milli':
            factor = 0.001; prefix = 'm'
        elif prefix == 'c' or prefix.lower() == 'centi':
            factor = 0.01; prefix = 'c'
        elif prefix == 'd' or prefix.lower() == 'deci':
            factor = 0.1; prefix = 'd'
        elif prefix == 'k' or prefix.lower() == 'kilo':
            factor = 1000; prefix = 'k'
        elif prefix == 'M' or prefix.lower() == 'mega':
            factor = 1000000; prefix = 'M'
        elif prefix == 'G' or prefix.lower() == 'giga':
            factor = 1e9; prefix = 'G'
        return prefix, factor


    def text_prefix(self, scale_factor):
        '''Unimplemented function.
        Returns the metric text prefix associated with a given scaling factor.'''
        if scale_factor == 1:
            return ''
        elif scale_factor == 1e-9:
            return 'n'
        elif scale_factor == 1e-6:
            return 'μ'
        elif scale_factor == 0.001:
            return 'm'
        elif scale_factor == 0.01:
            return 'c'
        elif scale_factor == 0.1:
            return 'd'
        elif scale_factor == 1000:
            return 'k'
        elif scale_factor == 1000000:
            return 'M'
        elif scale_factor == 1e9:
            return 'G'

    # we need to change this one to do 3d plots
    def set_units(self, axis, units: str):
        '''Unimplemented function; do not use.'''
        axis = self.process_axis(axis)
        self.units[axis] = units
    
    def get_units(self, axis):
        return self.units[self.process_axis(axis)]

    def set_limit(self, axis, start: float, stop: float):
        '''Unimplemented function; do not use.
        Setter method for the limit dictionary
            Axis -> Pick from 'x'/0, 'y'/1, or 'z'/2
            start: float -> sets the MatPlotLib plot's lower limit
            stop: float -> sets the MatPlotLib plot's upper limit'''
        axis = self.process_axis(axis)
        self.limits[axis] = [start, stop]

    def is_top(self, gate):
        '''Unimplemented function; do not use.'''
        if gate in [1, 'T', 't', 'top']:
            return True
        elif gate in [0, 'B', 'b', 'bottom']:
            return False
        else:
            print("Error: Gate is either Top: 1/'T'/'t' or Bottom: 0/'B'/'b'")
            return