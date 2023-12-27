import os
import pandas as pd
import numpy as np
import json

'''
This script is used to load in the data from the March 3rd Kidney Data Collection

The data is stored in the following format:
    - Each patient has a folder
    - Each patient folder has a folder for each sample
    - Each sample folder has a folder for each class

The script navigated the folder structure and loads in the data from each .csv file into a pandas dataframe
'''

### CONSTANTS
START_INDEX = 790 # 360 nm

### FUNCTIONS
def loadSampleset(pathToSamples,start_index=790,separator=','):
    """
    Load the data from the given dataPath, record the time each sample was taken, and return the dataset as a numpy array.
    INPUTS:
        dataPath:       Path to the folder containing the data (example: "./Mar03/PatientA_Sample1_back/Cancer")
        start_index:    The index of the first wavelength value to include in the dataset. Default = 790 (360 nm)
        sep:            The separator used in the csv file. Default = ','
        A csv file contains the following rows:
            - Row 0: Wavelength values
            - Row n: Sample n
        Note: The first column of the csv file contains the time the sample was taken
    """
    samples = []
    collectionTimes = []
    print("Loading in: ", pathToSamples)
    # Loop through all samples collected in the folder
    for file_name in os.listdir(pathToSamples):
        sample_df = pd.read_csv(os.path.join(pathToSamples,file_name), sep=separator,engine='python', header=None) 

        # Extract the relevant sample information
        sample_df = sample_df.iloc[:, start_index:]           # trim to desire wavelength (360 nm)
        sample_arr = sample_df.to_numpy()
        spectrum_arr = np.mean(sample_arr[1:, 1:],axis=0)     # Average the intermediary readings to get as single 1 second sample *** sampling rate isnt constant
        wavelength_arr = sample_arr[0, 1:]                    # Grab the wavelength values from the first row
        sample_arr = np.concatenate((wavelength_arr.reshape(-1,1), spectrum_arr.reshape(-1,1)), axis=1)
        samples.append(sample_arr)                            # append to the dataset

        # Get the time of the sample was collected. We have to use modified time because the creation time changed when data was copied over
        time_collected = os.path.getmtime(os.path.join(pathToSamples,file_name))
        collectionTimes.append(time_collected)
    samples = np.array(samples,dtype='float')
    collectionTimes = np.array(collectionTimes,dtype='float')
    return samples, collectionTimes

### Define required parameters
datasetName = 'KidneyData_march3_test'
pathToTrialData = "C:/Users/David/OneDrive - Queen's University/1 Graduate Studies/1 Thesis Research/KidneyData_march3/March3_KidneyCollectionWithDrRen/Mar03"
formattedDataset_fileName = os.path.join(pathToTrialData, datasetName + '_Formatted_Dataset.csv')

sampleNameList = [f for f in os.listdir(pathToTrialData) if f.startswith('Patient')]
class0_name = 'Normal'
class1_name = 'Cancer'

# define a pandas df to store the incoming data
formatted_dataset_df = pd.DataFrame(columns=['PatientID', 'SampleID', 'Label (numeric)', 'Label', 'Data', 'Time']) 

for sampleName in sampleNameList:
    # Extract the information required to traverse the tree: Get the patientID and sampleID from the sampleName
    patientID = sampleName.split('_')[0]
    sampleID = sampleName.split('_')[1] + '_' +sampleName.split('_')[2]
    # Get a list of folders containing class information
    classNameList = [f for f in os.listdir(os.path.join(pathToTrialData,sampleName)) if f.startswith('Cancer') or f.startswith('Normal')]
    # Remove those folders which contain the ambient light: names containing AmbientLight
    classNameList = [f for f in classNameList if not f.endswith('AmbientLight')]
    print(classNameList)
    for className in classNameList:
        # set the label based on the className
        if class0_name in className:
            label = 0
        else:
            label = 1
        dataPath = os.path.join(pathToTrialData,sampleName,className)
        # Check to see if the path exists
        if os.path.exists(dataPath):
            data, time = loadSampleset(dataPath,start_index=START_INDEX, separator=',')
            # for each data file, append to the dataset
            for i in range(data.shape[0]):
                new_row = {'PatientID':patientID, 
                        'SampleID':sampleID, 
                        'Label (numeric)':label, 
                        'Label':className, 
                        'Data':data[i,:,:],
                        'Time': time[i]
                }
                formatted_dataset_df = pd.concat([formatted_dataset_df, pd.DataFrame([new_row])], ignore_index=True)
    # For each Data, convert the array to a string and save it to a csv file
    formatted_dataset_df['Data'] = formatted_dataset_df['Data'].apply(lambda x: json.dumps(x.tolist()))
    # Save the dataset to a csv file
    formatted_dataset_df.to_csv(formattedDataset_fileName, index=False)