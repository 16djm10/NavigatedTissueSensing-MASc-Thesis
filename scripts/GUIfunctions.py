"""

GUIfunctions.py

This library is supposed to contain all functions pertaining to graphical user interfaces. This includes displaying plots and results.

"""
import numpy as np
import SimpleITK as sitk
import matplotlib.pyplot as plt
import pandas as pd
# import statistics
from statistics import mode,mean
from scipy import interpolate


# Plots all instances of the spectras in different plots
def plotall(data):
    for i in range(len(data)):
        plt.figure(i+1)
#         scaling = 1.5**i+1
        scaling = 1
        plt.plot(data[i,:]*(scaling))
#         print((scaling))
        plt.title(str(i+1))

# Takes in two 1D arrays as input along with strings for the labels
def plotSpectra(xdata,ydata,xlab,ylab,title):
    plt.figure()
    plt.plot(xdata,ydata)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    plt.title(title)