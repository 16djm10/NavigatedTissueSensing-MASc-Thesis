""" 

IOfunctions.py 

This library is supposed to contain all functions which act as input
or output code. This includes data input calls and data save calls

"""

# Import statements
# Import all of the requried libraries
import numpy as np
import SimpleITK as sitk
# import matplotlib.pyplot as plt
import pandas as pd
# import statistics
# from statistics import mode,mean
from scipy import interpolate


# This function is used to load the data into python
""" def loadData(datapath):
    p = []
    for i in range(lenth):
        p.append(pd.read_csv(datapath + str(i+1) + '.csv'))
    return p """

def add(a,b):
    ans = a + 3*b
    return ans

# This function combines loading the data with 
def loadDataset(datapath,numfiles,start_index=742,end_index=-1,sep=';'):
    Dataset = []
    for i in range(numfiles):
        # Loading in the data
        if i < 9:
            numAsString = '0' + str(i+1)
        else:
            numAsString + str(i+1)
        filename = datapath + numAsString + '.csv'    
        df = pd.read_csv(filename, sep=sep,engine='python')
        # Extracting Relvant information
        # 32 for start, 774 for 350 nm
#         data = df[32:-1] # ** flag
        data = df[start_index:end_index]
        
        data_arr = data.to_numpy()
        Dataset.append(data_arr)
    Dataset = np.array(Dataset,dtype='float').squeeze()
    return Dataset


def loadSpectrum(path, name, col_name=None,start_index=774,end_index=-1,sep=';'):
#     df = pd.read_csv(path + name,sep=';',engine='python')
    df = pd.read_csv(path + name,sep=sep,engine='python')
    if not(col_name == None):
        df[col_name] = df.index
    data = df[start_index:end_index]
    data_arr = data.to_numpy()
    data_arr = np.array(data_arr,dtype='float')
    return data_arr