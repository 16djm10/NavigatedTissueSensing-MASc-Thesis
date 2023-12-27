""" 

Processfunctions.py 

This library is supposed to contain all functions which alter / process the data. This includes normalization, subtracting baseline, data augmentations

"""

# Import all of the requried libraries
import numpy as np
# import SimpleITK as sitk
# import matplotlib.pyplot as plt
# import pandas as pd
# import statistics
# from statistics import mode,mean
from scipy import interpolate


# Normalize peak instensity to 1.0
def normalize(data):
    temp = data.copy()
    if len(temp.shape) == 2:
        temp[:,1] = (temp[:,1] - min(temp[:,1]))
        temp[:,1] = temp[:,1]/max(temp[:,1])
    elif len(temp.shape) == 3:
        for i in range(len(temp)):
            temp[i,:,1] = (temp[i,:,1] - min(temp[i,:,1]))
            temp[i,:,1] = temp[i,:,1]/max(temp[i,:,1])
    else:
        print('Error, array dimension is not 2 or 3')     
    return temp
 
def subtractBaseline(data,baseline):
    temp = data.copy()
    
    for i in range(len(temp)):
        temp[i,:,1] = temp[i,:,1]-baseline
    return temp