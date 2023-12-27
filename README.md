# Navigated tissue sensing module

Codebase for the project titled "*Development of a research testbed for intraoperative optical spectroscopy tumour margin assessment*" conducted by David Morton 2021-2023. 

**Project abstract**: Surgical intervention is a primary treatment option for early-stage cancers. However, the difficulty of intraoperative tumor margin assessment contributes to a high rate of incomplete tumor resection, necessitating revision surgery. This work aims to develop and evaluate a prototype of a tracked tissue sensing research testbed for navigated tumor margin assessment. Our testbed employs diffuse reflection broadband optical spectroscopy for tissue characterization and electromagnetic tracking for navigation. Spectroscopy data and a trained classifier are used to predict tissue types. Navigation allows these predictions to be superimposed on the scanned tissue, creating a spatial classification map. We evaluate the real-time operation of our testbed using an ex vivo tissue phantom. Furthermore, we use the testbed to interrogate ex vivo human kidney tissue and establish a modeling pipeline to classify cancerous and non-neoplastic tissue. The testbed recorded latencies of 125 ± 11 ms and 167 ± 26 ms for navigation and classification respectively. The testbed achieved a Dice similarity coefficient of 93%, and an accuracy of 94% for the spatial classification.  These results demonstrated the capabilities of our testbed for the real-time interrogation of an arbitrary tissue volume. Our modeling pipeline attained a balanced accuracy of 91% ± 9% on the classification of cancerous and non-neoplastic human kidney tissue. Our tracked tissue sensing research testbed prototype shows potential for facilitating the development and evaluation of intraoperative tumor margin assessment technologies across tissue types. The capacity to assess tumor margin status intraoperatively has the potential to increase surgeon confidence in complete tumor resection, thereby reducing the rates of revision surgeries.

### System information
**Overview of module**: For more detailed information please see Chapter 3.1 of the thesis document.

**Setup and Operation**: See System Documentation --> Testbed Documentation for a detailed setup guide. 

### Overview of codebase
##### 3D Slicer module and documentation
- System Documentation: DETAILED OVERVIEW of how to get the system running
- BroadbandSpecModule: Contains source code for the navigated tissue sensing 3D slicer module.
- SpectrumViewerModule: Contains the source code for a module that simply displays the current input spectrum. This was the basis for BroadSpecModule but is **not required** to operate it.
- thesis: Contains the full written thesis document
##### Configuration files
- PLUS-config-files: Contains the configuration files for use in the PLUS application to connect with the Thorlabs spectrometer and NDI EMT used in these experiments
##### Scripts
- 202304 - Data2Model.ipynb: Source code for a script to train an ML model for use in the module
- 202307 - ExploratoryDataAnalysis-MLpipelineExperimentation.ipynb: Source code for the exploratory data analysis and subsequent experimentation with a preprocessing pipeline
- 202308 - Thesis-results-generation-AblationStudy.ipynb: Source code used to preprocess, train, and evaluate ML models to generate an ablation study of input parameters. 
- scripts: Contains scripts used during the development of this project that are **no longer in use**.
##### Demo models, scenes, recorded spectral data
- Demo - CavityReconstruction: Used for a physical demo where the system was used to reconstruct a tumour cavity phantom.
- Demo - SavedScenes: Contains 3D slicer scenes which can be loaded into the module
- Demo - Spectroscopy data sequence: Contains a prerecorded spectroscopic sequence to see the spectrum viewer in action.
- Demo - TrainedModels: Contains some pre-trained models that can be loaded into the module.

### Resources
##### Software
- PLUS version: PlusApp-2.9.0.20230118-ThorLabs-Win32
- 3D Slicer version: 5.2.1

##### 3D Slicer Extensions
- DebuggingTools: 25d65a5     (2022-11-24)
- MarkupsToModel: 835453f     (2022-11-24)
- SlicerIGSIO: 78d65fe        (2022-12-11)
- SlicerIGT: d3fd2b2          (2022-11-24)
- SlicerOpenIGTLink: af9659f  (2022-11-24)

##### Datasets
- Datasets for Chapter 3 and Chapter 4 of the thesis are found in p drive @ P:\data\BroadbandSpecData




