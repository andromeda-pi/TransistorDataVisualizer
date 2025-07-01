from TransistorDataVisualizer import DataFile

################################################
# Set your path in this file to where you are  # 
#    storing your easyEXPERT CSV files         #
################################################

FILEPATH = $$$SET_FILE_PATH_HERE$$$
# once you have your FILEPATH setup, it is recommended to add this file (TransistorDataFiles.py) to git_ignore
#    so it doesn't get reset when doing git pull for future version releases

###        Setting up FILEPATH Example       ###
################################################
# Example pathing for the KeySight_easyEXPERT_dataExport 
#   root file stored in the E: drive of a PC:
# PCPATH = # Example path: 'E:\\KeySight_easyEXPERT_dataExport\\'
#   
# FILEPATH = PCPPATH
#
################################################



###              Usage Example               ###
################################################
# once your FILEPATH is set, you can import this file
# eg. `import TransistorDataFiles as fls`
# and then access all existing tests. 
# 
# For instance: `fls.It7` will get the path and test type in the DataFile format necessary to
#     begin creating Files and DataSets
#
# Example: fetching a test and quickly plotting its results:
# ```
# import TransistorDataVisualizer as tdv
# import TransistorDataFiles as fls
# 
# DS1 = tdv.DataSet( fls.It7 )
# DS1.quick_plot3d(-1)
# ```
################################################

T1 = None
T2 = '\\S31_#2_50x50_P25247'
T3 = '\\S31_#3_100x100_P25246'
T4 = '\\S31_#4_50x50_P25245'
T5 = None
T6 = '\\S31_#6_200x200_P25244'
T7 = '\\S31_#7_50x50_P25243'
T7_PRE = '\\S31_#7_50x50_P25243_pre_epoxy' # pre epoxy
T7_POST = '\\S31_#7_50x50_P25243_post_epoxy' # post epoxy
T8 = '\\S31_#8_50x50_P25242'
T8_1 = '\\8'
CRYO = '\\Cryo'



Rb2 = DataFile('Rb2', FILEPATH + T2 + '\\Rds v Vbgs [(2) _ 7_19_2023 3_42_41 PM].csv')
Rb3 = DataFile('Rb3', FILEPATH + T3 + '\\Rds v Vbgs_n1.csv', 'bad device?')
Rb4 = DataFile('Rb4', FILEPATH + T4 + '\\Rds v Vbgs_n2.csv')
Rb6 = DataFile('Rb6', FILEPATH + T6 + '\\Rds v Vbgs_n3.csv')
Rb7 = DataFile('Rb7', FILEPATH + T7 + '\\Rds v Vbgs_n2.csv')
Rb7pre_n1 = DataFile('Rb7', FILEPATH + T7_PRE + '\\Rds v Vbgs_n1.csv')
Rb7pre_n2 = DataFile('Rb7', FILEPATH + T7_PRE + '\\Rds v Vbgs_n2.csv')
Rb7pre_n3 = DataFile('Rb7', FILEPATH + T7_PRE + '\\Rds v Vbgs_n3.csv')
Rb7post_n1 = DataFile('Rb7', FILEPATH + T7_POST + '\\Rds v Vbgs_n1.csv', 'post-epoxy')
Rb7post_n2 = DataFile('Rb7', FILEPATH + T7_POST + '\\Rds v Vbgs_n2.csv', 'post-epoxy')
Rb7post_n3 = DataFile('Rb7', FILEPATH + T7_POST + '\\Rds v Vbgs_n3.csv', 'post-epoxy')
Rb8 = DataFile('Rb8', FILEPATH + T8 + '\\Rds v Vbgs_n3.csv')

Rt2 = DataFile('Rt2', FILEPATH + T2 + '\\Rds v Vtgs [(2) _ 7_19_2023 3_39_41 PM].csv')
Rt3 = DataFile('Rt3', FILEPATH + T3 + '\\Rds v Vtgs_n3.csv', 'broken test')
Rt4 = DataFile('Rt4', FILEPATH + T4 + '\\Rds v Vtgs_n1.csv')
Rt6 = DataFile('Rt6', FILEPATH + T6 + '\\Rds v Vtgs_n1.csv')
Rt7 = DataFile('Rt7', FILEPATH + T7 + '\\Rds v Vtgs_n1.csv')
Rt7pre_n1 = DataFile('Rt7', FILEPATH + T7_PRE + '\\Rds v Vtgs_n1.csv')
Rt7pre_n2 = DataFile('Rt7', FILEPATH + T7_PRE + '\\Rds v Vtgs_n2.csv')
Rt7pre_n3 = DataFile('Rt7', FILEPATH + T7_PRE + '\\Rds v Vtgs_n3.csv')
Rt7post_n1 = DataFile('Rt7', FILEPATH + T7_POST + '\\Rds v Vtgs_n1.csv', 'post-epoxy')
Rt7post_n2 = DataFile('Rt7', FILEPATH + T7_POST + '\\Rds v Vtgs_n2.csv', 'post-epoxy')
Rt7post_n3 = DataFile('Rt7', FILEPATH + T7_POST + '\\Rds v Vtgs_n3.csv', 'post-epoxy')
Rt8 = DataFile('Rt8', FILEPATH + T8 + '\\Rds v Vtgs_n1.csv')

Ib2 = DataFile('Ib2', FILEPATH + T2 + '\\Id-Vds var const Vbgs_n1.csv')
Ib3 = DataFile('Ib3', FILEPATH + T3 + '\\Id-Vds var const Vbgs_n1-2.csv', 'poor quality')
Ib4 = DataFile('Ib4', FILEPATH + T4 + '\\Id-Vds var const Vbgs_n1.csv')
Ib6 = DataFile('Ib6', FILEPATH + T6 + '\\Id-Vds var const Vbgs_n1.csv')
Ib7 = DataFile('Ib7', FILEPATH + T7 + '\\Id-Vds var const Vbgs_n1.csv')
Ib7pre_n1 = DataFile('Ib7', FILEPATH + T7_PRE + '\\Id-Vds var const Vbgs_n1.csv')
Ib7pre_n2 = DataFile('Ib7', FILEPATH + T7_PRE + '\\Id-Vds var const Vbgs_n2.csv')
Ib7pre_n3 = DataFile('Ib7', FILEPATH + T7_PRE + '\\Id-Vds var const Vbgs_n3.csv')
Ib7post_n1 = DataFile('Ib7', FILEPATH + T7_POST + '\\Id-Vds var const Vbgs_n1.csv', 'post-epoxy')
Ib7post_n2 = DataFile('Ib7', FILEPATH + T7_POST + '\\Id-Vds var const Vbgs_n2.csv', 'post-epoxy')
Ib7post_n3 = DataFile('Ib7', FILEPATH + T7_POST + '\\Id-Vds var const Vbgs_n3.csv', 'post-epoxy')
Ib8 = DataFile('Ib8', FILEPATH + T8 + '\\Ib8.csv')

It2 = DataFile('It2', FILEPATH + T2 + '\\Id-Vds var const Vtgs_n1.csv')
It3 = DataFile('It3', FILEPATH + T3 + '\\Id-Vds var const Vtgs_n1.csv', 'poor quality')
It4 = DataFile('It4', FILEPATH + T4 + '\\Id-Vds var const Vtgs_n1.csv')
It6 = DataFile('It6', FILEPATH + T6 + '\\Id-Vds var const Vtgs_n1.csv')
It7 = DataFile('It7', FILEPATH + T7 + '\\Id-Vds var const Vtgs_n1.csv')
It7pre_n1 = DataFile('It7', FILEPATH + T7_PRE + '\\Id-Vds var const Vtgs_n1.csv')
It7pre_n2 = DataFile('It7', FILEPATH + T7_PRE + '\\Id-Vds var const Vtgs_n2.csv')
It7pre_n3 = DataFile('It7', FILEPATH + T7_PRE + '\\Id-Vds var const Vtgs_n3.csv')
It7post_n1 = DataFile('It7', FILEPATH + T7_POST + '\\Id-Vds var const Vtgs_n1.csv', 'post-epoxy')
It7post_n2 = DataFile('It7', FILEPATH + T7_POST + '\\Id-Vds var const Vtgs_n2.csv', 'post-epoxy')
It7post_n3 = DataFile('It7', FILEPATH + T7_POST + '\\Id-Vds var const Vtgs_n3.csv', 'post-epoxy')
It8 = DataFile('It8', FILEPATH + T8 + '\\Id-Vds var const Vtgs_n1.csv')

Rts2_n1 = DataFile('Rt2', FILEPATH + T2 + '\\Rds v Vtgs var const Vds_n1.csv')
Rts3_n1 = DataFile('Rt3', FILEPATH + T3 + '\\Rds v Vtgs var const Vds_n1.csv')
Rts3_n2 = DataFile('Rt3', FILEPATH + T3 + '\\Rds v Vtgs var const Vds_n2.csv')
Rts3_n3 = DataFile('Rt3', FILEPATH + T3 + '\\Rds v Vtgs var const Vds_n3.csv')
Rbs4_n1 = DataFile('Rb4', FILEPATH + T4 + '\\Rds v Vbgs var const Vds_n3.csv')
Rts4_n1 = DataFile('Rt4', FILEPATH + T4 + '\\Rds v Vtgs var const Vds_n1.csv')
Rts4_n2 = DataFile('Rt4', FILEPATH + T4 + '\\Rds v Vtgs var const Vds_n2.csv')

It8cryo = DataFile('It8', FILEPATH + CRYO + '\\Id-Vds var const Vtgs_n1.csv', 'cryo')