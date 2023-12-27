'''
Author: David Morton, Queen's University, PERK Lab and Med-i Lab
Email: david.morton@queensu.ca

Module Name: BroadbandSpecModule (Navigated tissue sensing module)
Purpose: To enable the rapid protyping of navigated tissue sensing systems. This module faciliated a live tissue interrogation system which employed an optical spectroscope and electromagnetic tracker.
Description: Module allows for the collection, classification, and visualization of optical spectroscopy data in real-time.
  Data Collection - Records and saves spectroscopy data and associated metadata (e.g. PatientID, DataClass, etc.)
  Model Inference - Classifies the data in real-time using a pre-trained model
  Visualization - Combines tracking data with classification data to create a localized classification map.
'''

# Import statements
import logging
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import numpy as np
import os
import time
try: 
  from joblib import load
except:
  slicer.util.pip_install('joblib')
  from joblib import load
try:
  import sklearn
except:
  slicer.util.pip_install('scikit-learn')
  import sklearn

# Processfunctions is a costume library to include preprocessing pipeline functions
# Slicer doesnt recognize it on startup so you need to reload the module if in use.
# try:
#   import Processfunctions as process
# except:
#   pass


#
# BroadbandSpecModule
#
class BroadbandSpecModule(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Navigated Tissue Sensing"
    self.parent.categories = ["Spectroscopy"]
    self.parent.dependencies = []
    parent.contributors = ["David Morton (Queen's University, PERK Lab)"] 
    self.parent.helpText = """
    Module can display spectrum curve in real-time from a spectrum image received through OpenIGTLink. 
    First line of the spectrum image contains wavelength, 
    second line of the image contains intensities.
    Module also recieves 3D tracking data and plots the 3D position of each spectrum obtained.
    """
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
    """

#
# BroadbandSpecModuleWidget
#
class BroadbandSpecModuleWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)            # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False
    slicer.mymod = self                           # Used to access nodes in the python interactor for experimentation

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/BroadbandSpecModule.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run in batch mode, without a graphical user interface.
    self.logic = BroadbandSpecModuleLogic()
    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()
    self.initializeScene()
    self.logic.setupLists()

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene (in the selected parameter node).

    # Setup tab
    self.ui.connectButton.connect('clicked(bool)', self.onConnectButtonClicked)
    self.ui.spectrumImageSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSpectrumImageChanged)
    self.ui.outputTableSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onOutputTableChanged)
    self.ui.modelFileSelector.connect('currentPathChanged(QString)', self.onModelFileSelectorChanged)
    self.ui.placeFiducialButton.connect('clicked(bool)', self.onPlaceFiducialButtonClicked)
    self.ui.enablePlottingButton.connect('clicked(bool)', self.setEnablePlotting)
    self.ui.enableClassificationButton.connect('clicked(bool)', self.setEnableClassification)
    # Inference tab
    self.ui.scanButton.connect('clicked(bool)', self.onScanButtonClicked)
    self.ui.addControlPointButton.connect('clicked(bool)', self.onAddControlPointButtonClicked)
    self.ui.clearControlPointsButton.connect('clicked(bool)', self.onClearControlPointsButtonClicked)
    self.ui.clearLastPointButton.connect('clicked(bool)', self.onClearLastPointButtonClicked)
    # Data Collection tab
    self.ui.dataClassSelector.connect('currentIndexChanged(int)', self.onDataClassSelectorChanged)
    # add the options cancer and normal to the data class selector
    self.ui.dataClassSelector.addItem("Cancer")
    self.ui.dataClassSelector.addItem("Normal")
    self.ui.patientNumberSelector.connect('currentIndexChanged(int)', self.onPatientNumberSelectorChanged)
    self.ui.saveDirectoryButton.connect('directorySelected(QString)', self.onSaveDirectoryButtonClicked)
    self.ui.samplingDurationSlider.connect('valueChanged(double)', self.onSamplingDurationChanged)
    self.ui.samplingRateSlider.connect('valueChanged(double)', self.onSamplingRateChanged)
    self.ui.collectSampleButton.connect('clicked(bool)', self.onCollectSampleButtonClicked)
    self.ui.continuousCollectionButton.connect('clicked(bool)', self.onContinuousCollectionButtonClicked)

    self.initializeGUI()

  def initializeGUI(self):
    ''' Initializes the GUI with the local settings saved in settings.ini '''
    settings = slicer.app.userSettings()
    # initailize the save directory using settings
    if settings.value(self.logic.SAVE_LOCATION): # if the settings exists
      self.ui.saveDirectoryButton.directory = settings.value(self.logic.SAVE_LOCATION)
    # initailize the path to current model
    if settings.value(self.logic.MODEL_PATH):
      self.ui.modelFileSelector.setCurrentPath(settings.value(self.logic.MODEL_PATH))
    # initialize the savingFlag to False in the parameter node
    self._parameterNode.SetParameter(self.logic.SAVING_STATE, "False")

  def initializeScene(self):
    '''
    Initializes the scene with the following nodes:
    - NeedleModel
    - NeedleTip pointlist
    TODO 
      -  change pointlist to a dictionary, this should add functionality and make it faster to access the points.
      - Improve robustness to name changes of the nodes
    '''
    # If NeedleModel is not in the scene, create and add it
    needleModel = slicer.util.getFirstNodeByName(self.logic.NEEDLE_MODEL)
    if needleModel is None:
        createModelsLogic = slicer.modules.createmodels.logic()
        # creates a needle model with 4 arguments: Length, radius, tip radius, and DepthMarkers
        needleModel = createModelsLogic.CreateNeedle(80,1.0,2.5, 0)
        needleModel.SetName(self.logic.NEEDLE_MODEL)
        # Add it to parameter node
        self._parameterNode.SetNodeReferenceID(self.logic.NEEDLE_MODEL, needleModel.GetID())

    # If pointList_NeedleTip is not in the scene, create and add it
    pointList_EMT = self._parameterNode.GetNodeReference(self.logic.POINTLIST_EMT)
    if pointList_EMT == None:
        # Create a point list for the needle tip in reference coordinates
        pointList_EMT = slicer.vtkMRMLMarkupsFiducialNode()
        pointList_EMT.SetName("pointList_NeedleTip")
        slicer.mrmlScene.AddNode(pointList_EMT)
        # Set the role of the point list
        self._parameterNode.SetNodeReferenceID(self.logic.POINTLIST_EMT, pointList_EMT.GetID())
    
    # Add a point to the point list
    if pointList_EMT.GetNumberOfControlPoints() == 0:
        pointList_EMT.AddControlPoint(np.array([0, 0, 0]))
        pointList_EMT.SetNthControlPointLabel(0, "origin_Tip")

  # GUI functions

  def onContinuousCollectionButtonClicked(self):
    ''' Updates text on continuous collection button, and toggles data collection when clicked '''
    # if the button is checked, start collecting data
    if self.ui.continuousCollectionButton.isChecked():
      self.ui.continuousCollectionButton.setText("Stop Collection")
      self.logic.startDataCollection()
    # if the button is not checked, stop collecting data
    else:
      self.ui.continuousCollectionButton.setText("Start Continuous Collection")
      self.logic.stopDataCollection()
  
  def onDataClassSelectorChanged(self):
    ''' Updates the data class parameter in the parameter node'''
    self.updateParameterNodeFromGUI()
    parameterNode = self.logic.getParameterNode()
    dataClass = self.ui.dataClassSelector.currentText
    parameterNode.SetParameter(self.logic.DATA_CLASS, dataClass)

  def onPatientNumberSelectorChanged(self):
    ''' Updates the patient number parameter in the parameter node'''
    self.updateParameterNodeFromGUI()
    parameterNode = self.logic.getParameterNode()
    patientNumber = self.ui.patientNumberSelector.currentText
    parameterNode.SetParameter(self.logic.PATIENT_NUM, patientNumber)

  def onSamplingDurationChanged(self):
    ''' Updates the sampling duration parameter in the parameter node'''
    self.updateParameterNodeFromGUI()
    parameterNode = self.logic.getParameterNode()
    sampleDuration = self.ui.samplingDurationSlider.value
    parameterNode.SetParameter(self.logic.SAMPLING_DURATION, str(sampleDuration))

  def onSamplingRateChanged(self):
    ''' Updates the sampling rate parameter in the parameter node'''
    self.updateParameterNodeFromGUI()
    parameterNode = self.logic.getParameterNode()
    sampleRate = self.ui.samplingRateSlider.value
    parameterNode.SetParameter(self.logic.SAMPLING_RATE, str(sampleRate))

  def onCollectSampleButtonClicked(self,enable):
    ''' Initiates the collection of a data sample for a fixed duration'''
    self.updateParameterNodeFromGUI()
    # update the parameter node
    parameterNode = self.logic.getParameterNode()
    parameterNode.SetParameter(self.logic.SAVING_STATE, str(enable))
    sampleDuration = parameterNode.GetParameter(self.logic.SAMPLING_DURATION)
    # disable the button
    self.ui.collectSampleButton.setEnabled(False)
    self.logic.recordSample()
    # # start a timer to enable the button after 1 second
    timer = qt.QTimer()
    timer.singleShot(float(sampleDuration)*1000+50, lambda: self.ui.collectSampleButton.setEnabled(True))

  def onConnectButtonClicked(self):
    ''' Creates the IGTLink connection for the Spectrometer and the EMT '''
    self.updateParameterNodeFromGUI()
    # Get parameter node
    parameterNode = self.logic.getParameterNode()
    # Get the connector node from the parameter node
    connectorNode = parameterNode.GetNodeReference(self.logic.CONNECTOR)
    # if the a connector node does not exist, create one
    if connectorNode == None:
      print('No connector node found, creating one')
      # Create a connector node
      connectorNode = slicer.vtkMRMLIGTLConnectorNode()
      # Set the connector node name
      connectorNode.SetName('IGTLConnector_SpecEMT')
      # Add the connector node to the scene
      slicer.mrmlScene.AddNode(connectorNode) 
      connectorNode.SetTypeClient('localhost', 18944)
      connectorNode.Start()
      self.ui.connectButton.text = 'Disconnect'
      # Save the node ID to the parameter node
      parameterNode.SetNodeReferenceID(self.logic.CONNECTOR, connectorNode.GetID())
    # if connector node exists, update the text on the button
    else:
      if connectorNode.GetState() == 0:
        connectorNode.Start()
        print('Connector node started')
        self.ui.connectButton.text = 'Disconnect'
      else:
        connectorNode.Stop()
        print('Connector node stopped')
        self.ui.connectButton.text = 'Connect'

    # Checks to see if connector node exists
    if connectorNode != None:
      # This accesses the transform from the connector node
      transformNode = connectorNode.GetIncomingMRMLNode(1) 
      # if the transform exists, move the needle and origin point to the transform
      if transformNode != None:
        needleModel = parameterNode.GetNodeReference(self.logic.NEEDLE_MODEL)
        needleModel.SetAndObserveTransformNodeID(transformNode.GetID())
        pointList_NeedleTip = parameterNode.GetNodeReference(self.logic.POINTLIST_EMT)
        pointList_NeedleTip.SetAndObserveTransformNodeID(transformNode.GetID())

  def onSaveDirectoryButtonClicked(self, directory):
    ''' Updates the save directory parameter in the user settings '''
    # update settings with the new directory
    settings = slicer.app.userSettings()
    settings.setValue(self.logic.SAVE_LOCATION, directory)
    # Print the save directory 
    print('Save directory: ' + directory)

  def onSpectrumImageChanged(self):
    ''' Updates the parameter node whenever the incoming spectrum changes'''
    self.updateParameterNodeFromGUI()

  def onOutputTableChanged(self):
    ''' Updates the parameter node whenever the output table selection changes'''
    self.updateParameterNodeFromGUI()

  def onModelFileSelectorChanged(self, path):
    ''' Updates the parameter node whenever the model file selector changes'''
    # update settings with the new model path
    settings = slicer.app.userSettings()
    settings.setValue(self.logic.MODEL_PATH, path)
    print('Loading in model from path:', path)
    if not (path == ''): 
      self.logic.model = load(path)

  def onPlaceFiducialButtonClicked(self):
    ''' Initates the placement of a fiducial point'''
    self.updateParameterNodeFromGUI()
    self.logic.placeFiducial()

  def setEnablePlotting(self, enable):
    ''' Initiates the spectrum viewer and toggles the button text'''
    self.updateParameterNodeFromGUI()
    if enable:
      # change the button text to 'Disable Plotting'
      self.ui.enablePlottingButton.text = 'Disable Plotting'
      self.logic.startPlotting()
    else:
      # change the button text to 'Enable Plotting'
      self.ui.enablePlottingButton.text = 'Enable Plotting'
      self.logic.stopPlotting()

  def setEnableClassification(self, enable):
    ''' Initiates the real-time classification and toggles the button text'''
    self.updateParameterNodeFromGUI()
    if enable:
      # change the button text to 'Disable Classification'
      self.ui.enableClassificationButton.text = 'Disable Classification'
    else:
      # change the button text to 'Enable Classification'
      self.ui.enableClassificationButton.text = 'Enable Classification'

  def onClearLastPointButtonClicked(self):
    ''' 
    Initiates removal of the last data point plotted
    TODO - Implement this function after transitioning to a dictionary for the point lists
    '''
    self.updateParameterNodeFromGUI()
    # Check to see if the lists exist, and if not create them
    print("This button is not currently implemented")

  def onClearControlPointsButtonClicked(self):
    ''' Initiates removal of all points visualized'''
    self.updateParameterNodeFromGUI()
    self.logic.clearControlPoints()

  def onAddControlPointButtonClicked(self):
    ''' Initiates the addition of a new data point to the visualization'''
    self.updateParameterNodeFromGUI()
    self.logic.addControlPointToToolTip()

  def onScanButtonClicked(self, checked):
    ''' Initiates the start of the scanning process'''
    self.updateParameterNodeFromGUI()
    if checked:
      self.logic.startScanning()
    else:
      self.logic.stopScanning()
    self.ui.scanButton.text = 'Scanning' if checked else 'Start Scanning'

  # Predefined functions
  
  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.
    self.setParameterNode(self.logic.getParameterNode())

    # Ensure the required lists are created and reference in the parameter node

    # Select default input nodes if nothing is selected yet to save a few clicks for the user
    if not self._parameterNode.GetNodeReference(self.logic.INPUT_VOLUME):
      firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode") # ***
      if firstVolumeNode:
        self._parameterNode.SetNodeReferenceID(self.logic.INPUT_VOLUME, firstVolumeNode.GetID())

    # If the output table does not exist, create one and select it
    if self._parameterNode.GetNodeReference(self.logic.OUTPUT_TABLE) is None:
      # a table node is not selected, create a new one
        firstTableNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLTableNode")
        firstTableNode.SetName('Table')
        slicer.mrmlScene.AddNode(firstTableNode)
        self._parameterNode.SetNodeReferenceID(self.logic.OUTPUT_TABLE, firstTableNode.GetID())

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    # It doesn't update if the paramater node is empty or is already updating the GUI
    if self._parameterNode is None or self._updatingGUIFromParameterNode: 
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # Update node selectors
    self.ui.spectrumImageSelector.setCurrentNode(self._parameterNode.GetNodeReference(self.logic.INPUT_VOLUME))
    self.ui.outputTableSelector.setCurrentNode(self._parameterNode.GetNodeReference(self.logic.OUTPUT_TABLE))

    # Update buttons state
    nodeList = slicer.util.getNodesByClass('vtkMRMLIGTLConnectorNode') # ***
    if nodeList == []:
      pass
    else:
      connectorNode = nodeList[0]
      if connectorNode.GetState() == 0:
        self.ui.connectButton.text = 'Connect'
      else:
        self.ui.connectButton.text = 'Disconnect' 

    # # If SAVING_STATE is not none
    # if self._parameterNode.GetParameter(self.logic.SAVING_STATE) is not None:
    #   # If SAVING_STATE is true
    #   if self._parameterNode.GetParameter(self.logic.SAVING_STATE) == 'True':
    #     # change the button text to 'Saving'
    #     self.ui.collectSampleButton.text = 'Saving'
    #     # disable the button
    #     self.ui.collectSampleButton.enabled = False
    #   # If SAVING_STATE is false
    #   else:
    #     # change the button text to 'Collect Sample'
    #     self.ui.collectSampleButton.text = 'Collect Sample'
    #     # enable the button
    #     self.ui.collectSampleButton.enabled = True

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return
    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch
    # Update Widget ParameterNode
    self._parameterNode.SetNodeReferenceID(self.logic.INPUT_VOLUME, self.ui.spectrumImageSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID(self.logic.OUTPUT_TABLE, self.ui.outputTableSelector.currentNodeID)
    parameterNode = self.logic.getParameterNode() # The parameter node is already linked to the GUI
    # update parameter node with the state of start scanning button
    parameterNode.SetParameter(self.logic.SCANNING_STATE, str(self.ui.scanButton.isChecked()))
    # update parameter node with the state of enable plotting button
    parameterNode.SetParameter(self.logic.PLOTTING_STATE, str(self.ui.enablePlottingButton.isChecked()))
    # update parameter node with the state of enable classification button
    parameterNode.SetParameter(self.logic.CLASSIFYING_STATE, str(self.ui.enableClassificationButton.isChecked()))
    # update parameter node with the current path of the file selector
    parameterNode.SetParameter(self.logic.MODEL_PATH, self.ui.modelFileSelector.currentPath)
    # update parameter node with the current sampling duration and samplling rate
    parameterNode.SetParameter(self.logic.SAMPLING_DURATION, str(self.ui.samplingDurationSlider.value))
    parameterNode.SetParameter(self.logic.SAMPLING_RATE, str(self.ui.samplingRateSlider.value))
    

    self._parameterNode.EndModify(wasModified)
 
  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.logic.removeObservers()
  
  def enter(self):
    """
    Called each time the user opens this module.
    """
    # Make sure parameter node exists and observed
    self.initializeParameterNode()

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore
    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()


#
# BroadbandSpecModuleLogic
#

class BroadbandSpecModuleLogic(ScriptedLoadableModuleLogic,VTKObservationMixin):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  # NAMES
  MODEL_PATH = "ModelPath"                        # Parameter stores the path to the classifier
  CLASSIFICATION = "Classification"               # Parameter stores the classification result
  
  SCANNING_STATE = 'Scanning State'               # Parameter stores whether the scanning is on or off
  PLOTTING_STATE = 'Plotting State'               # Parameter stores whether the plotting is on or off
  CLASSIFYING_STATE = 'Classifying State'         # Parameter stores whether the classification is on or off
  SAVING_STATE = 'Saving State'                   # Parameter stores whether saving is occuring 

  SAMPLING_DURATION = "Sample Duration"           # Parameter stores the duration of the sampling
  SAMPLING_RATE = "Sample Rate"                   # Parameter stores the rate of the sampling
  DATA_CLASS = "Data Class"                       # Parameter stores the data class we are recording
  PATIENT_NUM = "Patient Number"               # Parameter stores the patient number
  SAVE_LOCATION = 'Save Location'                 # Parameter stores the location where the data is saved

  # ROLES 
  INPUT_VOLUME = "InputVolume"                    # Parameter for ID of the input volume
  OUTPUT_TABLE = "OutputTable"                    # Parameter for ID of output table
  POINTLIST_GREEN_WORLD = 'pointList_Green_World' # Parameter for ID of green point list
  POINTLIST_RED_WORLD = 'pointList_Red_World'     # Parameter for ID of red point list
  POINTLIST_EMT = 'pointList_EMT'                 # Parameter for ID of EMT point list
  CONNECTOR = 'Connector'                         # Parameter for ID of connector node
  SAMPLE_SEQUENCE = 'SampleSequence'              # Parameter for ID of sample sequence node
  SAMPLE_SEQ_BROWSER = 'SampleSequenceBrowser'    # Parameter for ID of sample sequence browser node
  OUTPUT_SERIES = "OutputSeries"                  # Parameter for ID of output series node 
  OUTPUT_CHART = "OutputChart"                    # Parameter for ID of output chart node
  NEEDLE_MODEL = 'Needle Model'                   # Parameter for ID of needle model node

  # Constants
  CLASS_LABEL_0 = "ClassLabel0"                   # The label of the first class
  CLASS_LABEL_1 = "ClassLabel1"                   # The label of the second class
  CLASS_LABEL_NONE = "WeakSignal"                 # The label of the class when the signal is too weak
  DISTANCE_THRESHOLD = 1 # in mm





  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)
    self.observerTags = [] # This is reset when the module is reloaded. But not all observers are removed.
    slicer.mymodLog = self
    self.model = None

#
# Backend functions
#

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter(self.CLASSIFICATION):
      parameterNode.SetParameter(self.CLASSIFICATION, '')

  def addObservers(self):
    ''' Adds observers to the scene '''
    parameterNode = self.getParameterNode()
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    if spectrumImageNode:
      self.observerTags.append([spectrumImageNode, spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onSpectrumImageNodeModified)])

  def removeObservers(self):
    ''' Removes observers from the scene '''
    for nodeTagPair in self.observerTags:
      nodeTagPair[0].RemoveObserver(nodeTagPair[1])

#
# Setup functions
# 

  def startDataCollection(self):
    ''' Starts the process of recording spectral data into a sequence '''
    # Load in the parameters
    parameterNode = self.getParameterNode()
    sampleFrequency = parameterNode.GetParameter(self.SAMPLING_RATE)
    image_imageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    browserNode = parameterNode.GetNodeReference(self.SAMPLE_SEQ_BROWSER)
    # Print Collecting sample and the data collection parameters
    print('Starting Collection')
    print('Sample frequency: ' + sampleFrequency)
    if browserNode == None:
      browserNode = slicer.vtkMRMLSequenceBrowserNode()
      slicer.mrmlScene.AddNode(browserNode)
      browserNode.SetName("SampleSequenceBrowser")
      parameterNode.SetNodeReferenceID(self.SAMPLE_SEQ_BROWSER, browserNode.GetID())
    # Check to see if our sequence node exists yet
    if parameterNode.GetNodeReferenceID(self.SAMPLE_SEQUENCE) is None:
      sequenceLogic = slicer.modules.sequences.logic()
      sequenceNode = sequenceLogic.AddSynchronizedNode(None, image_imageNode, browserNode) # Check doc on AddSynchronizedNode to see if there is another way.
      parameterNode.SetNodeReferenceID(self.SAMPLE_SEQUENCE, sequenceNode.GetID())
    sequenceNode = parameterNode.GetNodeReference(self.SAMPLE_SEQUENCE)
    # Clear the sequence node of previous data
    sequenceNode.RemoveAllDataNodes()
    # Initalize the sequence node parameters
    browserNode.SetRecording(sequenceNode, True)
    browserNode.SetPlayback(sequenceNode, True)
    browserNode.SetPlaybackRateFps(float(sampleFrequency))
    # Start the recording
    browserNode.SetRecordingActive(True)

  def stopDataCollection(self):
    ''' Haults the data collection process and initiates the data saving process '''
    print('Stopping Collection')
    # Load in the parameters
    parameterNode = self.getParameterNode()
    browserNode = parameterNode.GetNodeReference(self.SAMPLE_SEQ_BROWSER)
    # Stop the recording
    browserNode.SetRecordingActive(False)
    # Save the sample to csv
    self.saveSample()

  def placeFiducial(self):
    """
    Places a fiducial at the tool tip.
    """
    parameterNode = self.getParameterNode()
    pointListGreen_World = parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD)
    pointList_EMT = parameterNode.GetNodeReference(self.POINTLIST_EMT)
    # The the tip of the probe in world coordinates
    pos = [0,0,0]
    pointList_EMT.GetNthControlPointPositionWorld(0,pos)
    tip_World = pos
    pointListGreen_World.AddControlPoint(tip_World)
    pointListGreen_World.SetNthControlPointLabel(pointListGreen_World.GetNumberOfControlPoints()-1, '')

  def startPlotting(self):
      ''' Starts plotting the spectrum data in the spectrum viewer'''
      print("Start plotting")
      # Change the layout to one that has a chart.
      ln = slicer.util.getNode(pattern='vtkMRMLLayoutNode*')
      ln.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalPlotView)
      # Make sure there aren't already observers
      self.removeObservers()  
      # Start the updates
      self.addObservers()
      self.onSpectrumImageNodeModified(0,0)

  def stopPlotting(self):
    ''' Stops plotting and sets the view back to conventional '''
    print("Stopped plotting")
    ln = slicer.util.getNode(pattern='vtkMRMLLayoutNode*')
    # set view to conventional
    ln.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalView)
    self.removeObservers()  

  def addControlPointToToolTip(self):
    ''' Adds a control point to the point list at the tool tip location '''
    # Get the required nodes
    parameterNode = self.getParameterNode()
    pointListGreen_World = parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD)
    pointListRed_World = parameterNode.GetNodeReference(self.POINTLIST_RED_WORLD)
    pointList_EMT = parameterNode.GetNodeReference(self.POINTLIST_EMT)

    # The the tip of the probe in world coordinates
    pos = [0,0,0]
    pointList_EMT.GetNthControlPointPositionWorld(0,pos)
    tip_World = pos
    # Add control point at tip of probe based on classification
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    # Convert image to volume 
    specArray = slicer.util.arrayFromVolume(spectrumImageNode)
    specArray = np.squeeze(specArray)
    specArray = np.transpose(specArray)
    self.classifySpectra(specArray[790:,:]) # Magic Number ** Also this is very slow to compute
    spectrumLabel = parameterNode.GetParameter(self.CLASSIFICATION)

    if spectrumLabel == self.CLASS_LABEL_0:
      pointListGreen_World.AddControlPoint(tip_World)
      # set label of the control point to ''
      pointListGreen_World.SetNthControlPointLabel(pointListGreen_World.GetNumberOfControlPoints()-1, '')
    elif spectrumLabel == self.CLASS_LABEL_1:
      pointListRed_World.AddControlPoint(tip_World)
      pointListRed_World.SetNthControlPointLabel(pointListRed_World.GetNumberOfControlPoints()-1, '')

  def clearControlPoints(self):
    """
    Clear all control points from the point lists.
    """
    # Check to see if the lists exist, and if not create them
    # self.setupLists()
    parameterNode = self.getParameterNode()
    pointListGreen_World = parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD)
    pointListRed_World = parameterNode.GetNodeReference(self.POINTLIST_RED_WORLD)
    pointListGreen_World.RemoveAllMarkups()
    pointListRed_World.RemoveAllMarkups()

  def startScanning(self):
    # This is currently handled directly in onSpectrumImageNodeModified using a flag
    print('Scanning')

  def stopScanning(self):
    # This is currently handled directly in onSpectrumImageNodeModified using a flag
    print('Stopping Scanning')

#
# Data Collection
#
  def recordSample(self):
    ''' This function will record an N second sample of spectral data, it then calls saveSample to save the data to a csv file '''
    # Load in the parameters
    parameterNode = self.getParameterNode()
    sampleDuration = parameterNode.GetParameter(self.SAMPLING_DURATION)
    sampleFrequency = parameterNode.GetParameter(self.SAMPLING_RATE)
    image_imageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    browserNode = parameterNode.GetNodeReference(self.SAMPLE_SEQ_BROWSER)
    
    if browserNode == None:
      browserNode = slicer.vtkMRMLSequenceBrowserNode()
      slicer.mrmlScene.AddNode(browserNode)
      browserNode.SetName("SampleSequenceBrowser")
      parameterNode.SetNodeReferenceID(self.SAMPLE_SEQ_BROWSER, browserNode.GetID())
    # Check to see if our sequence node exists yet
    if parameterNode.GetNodeReferenceID(self.SAMPLE_SEQUENCE) is None:
      sequenceLogic = slicer.modules.sequences.logic()
      sequenceNode = sequenceLogic.AddSynchronizedNode(None, image_imageNode, browserNode) # Check doc on AddSynchronizedNode to see if there is another way.
      parameterNode.SetNodeReferenceID(self.SAMPLE_SEQUENCE, sequenceNode.GetID())
    sequenceNode = parameterNode.GetNodeReference(self.SAMPLE_SEQUENCE)
    # Clear the sequence node of previous data
    sequenceNode.RemoveAllDataNodes()
    # Initalize the sequence node parameters
    browserNode.SetRecording(sequenceNode, True)
    browserNode.SetPlayback(sequenceNode, True)
    browserNode.SetPlaybackRateFps(float(sampleFrequency))
    # Start the recording
    browserNode.SetRecordingActive(True)
    self.timer = qt.QTimer()
    # NOTE: singleShot will proceed with the next lines of code before the timer is done
    # Call a singleShot to stop the recording after the sample duration
    self.timer.singleShot(float(sampleDuration)*1000, lambda: browserNode.SetRecordingActive(False))
    # Save the sample slightly after the recording is stopped
    self.timer.singleShot(float(sampleDuration)*1000+50, lambda: self.saveSample())

  def saveSample(self):
    ''' Saves the data stored in the SampleSequenceBrowse to a single csv file '''
    # get parameters
    parameterNode = self.getParameterNode()
    dataLabel = parameterNode.GetParameter(self.DATA_CLASS)
    sampleDuration = parameterNode.GetParameter(self.SAMPLING_DURATION)
    # Get the sequence node
    sequenceNode = parameterNode.GetNodeReference(self.SAMPLE_SEQUENCE)

    # Loop through the sequence
    sequenceLength = sequenceNode.GetNumberOfDataNodes()

    # get the number of files in the folder aleady
    # Check to see if any data has been recorded
    if sequenceLength == 0:
      print("No data to save (Preloaded sequences do not work)")
      return

    # Format the empty array
    spectrumArray = slicer.util.arrayFromVolume(sequenceNode.GetNthDataNode(0)) # Get the length of a spectrum
    SpectrumLength = spectrumArray.shape[2]
    spectrumArray2D = np.zeros((sequenceLength + 1, SpectrumLength + 1))        # Create the 2D array, add 1 for wavelength and time
    timeVector = np.linspace(0, float(sampleDuration), sequenceLength)          # create a time vector using the sampleDuration
    spectrumArray2D[1:,0] = timeVector                                          # concatenate the time vector to the spectrum array
    waveLengthVector = spectrumArray[0,0,:]
    spectrumArray2D[0,1:] = waveLengthVector

    for i in range(sequenceLength):
      # Get a spectrum as an array
      spectrumArray = np.squeeze(slicer.util.arrayFromVolume(sequenceNode.GetNthDataNode(i)))
      spectrumArray2D[i+1,1:] = spectrumArray[1,:]
    
    # Create the file path to save to. Date->PatientID->Class
    # Get the save path from settings
    settings = qt.QSettings()
    savePath = settings.value(self.SAVE_LOCATION)
    print(savePath)
    dateStamp = time.strftime("%b%d")
    patientNum = parameterNode.GetParameter(self.PATIENT_NUM)
    savePath = os.path.join(savePath, dateStamp,patientNum,dataLabel)
    # print save path
    print("Saving to: " + savePath)
    # If the save path does not exist, create it
    if not os.path.exists(savePath):
      os.makedirs(savePath)
    
    # Save the array to a csv
    '''File naming convention: TimeStamp_Patient#_#ofFiles_DataLabel.csv with TimeStamp in the format of MMMDD'''
    # timestamp
    FileNum = len([name for name in os.listdir(savePath) if os.path.isfile(os.path.join(savePath, name))]) + 1 # Get the file number
    fileName = dateStamp + "_" + patientNum + "_" + str(FileNum).zfill(3) + "_" + dataLabel + ".csv"

    # fileName = dataLabel + '_' + str(numFiles).zfill(3) + '.csv'
    np.savetxt(os.path.join(savePath, fileName), spectrumArray2D[:,:], delimiter=",")
    # print sample saved as well as name
    print("Sample saved as: " + fileName)

#
# Processing functions
#

  def onSpectrumImageNodeModified(self, observer, eventid):
    ''' 
    This function is called whenever the spectrum image is modified. 
    It handles much of the real-time processing and plotting.
    '''
    parameterNode = self.getParameterNode()
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    outputTableNode = parameterNode.GetNodeReference(self.OUTPUT_TABLE)
    
    # If either somehow don't exist, then don't do anything
    if not spectrumImageNode or not outputTableNode:
      return

    # If the enable plotting button is checked, start the plotting
    if parameterNode.GetParameter(self.PLOTTING_STATE) == "True":
      spectrumArray = self.updateOutputTable()
      # If classification is set to true, then classify the data
      if parameterNode.GetParameter(self.CLASSIFYING_STATE) == "True":
        self.classifySpectra(spectrumArray[790:,:]) # Magic Number **
      else:
        # set the classification to 'Classification Disabled'
        parameterNode.SetParameter(self.CLASSIFICATION, "Classifier Disabled")
      self.updateChart()
      pass

    # If the enable scanning button is checked
    if parameterNode.GetParameter(self.SCANNING_STATE) == "True":
      pointListGreen_World = parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD)
      pointListRed_World = parameterNode.GetNodeReference(self.POINTLIST_RED_WORLD)
      # if the red and green point lists are both empty
      if pointListRed_World.GetNumberOfControlPoints() == 0 and pointListGreen_World.GetNumberOfControlPoints() == 0:
        self.addControlPointToToolTip()
      else: # else check the distance beween the last control point and the tip of the probe
        # The the tip of the probe in world coordinates
        pos = [0,0,0]
        pointList_EMT = parameterNode.GetNodeReference(self.POINTLIST_EMT)
        pointList_EMT.GetNthControlPointPositionWorld(0,pos)
        tip_World = pos
            
        # Get the last control point of green in world coordinates
        pos = [0,0,0]
        pointListGreen_World.GetNthControlPointPositionWorld(pointListGreen_World.GetNumberOfControlPoints()-1,pos)
        lastPointGreen_World = pos
        # Get the last control point of red in world coordinates
        pos = [0,0,0]
        pointListRed_World.GetNthControlPointPositionWorld(pointListRed_World.GetNumberOfControlPoints()-1,pos)
        lastPointRed_World = pos

        # Get the distance between the tip and the last control point
        distanceRed = np.linalg.norm(np.subtract(tip_World, lastPointGreen_World))
        distanceGreen = np.linalg.norm(np.subtract(tip_World, lastPointRed_World))
        # If both distances are greater than the threshold, add a new control point
        if distanceRed > self.DISTANCE_THRESHOLD and distanceGreen > self.DISTANCE_THRESHOLD:
          self.addControlPointToToolTip()
 
  def setupLists(self):
      '''
      This function is used to create the point lists if they're not present.
      '''
      print("Setting up lists")
      # get the parameter node
      parameterNode = self.getParameterNode()

      # Check to see if role pointListGreen_World is present
      if parameterNode.GetNodeReference(self.POINTLIST_GREEN_WORLD) == None:
        # Create a point list for the green points in world coordinates
        pointListGreen_World = slicer.vtkMRMLMarkupsFiducialNode()
        pointListGreen_World.SetName("pointListGreen_World")
        slicer.mrmlScene.AddNode(pointListGreen_World)
        # Set the color of the points to green
        pointListGreen_World.GetDisplayNode().SetSelectedColor(0,1,0)
        # Set the role of the point list
        parameterNode.SetNodeReferenceID(self.POINTLIST_GREEN_WORLD, pointListGreen_World.GetID())

      # Check to see if role pointListRed_World is present
      if parameterNode.GetNodeReference(self.POINTLIST_RED_WORLD) == None:
        # Create a point list for the red points in world coordinates
        pointListRed_World = slicer.vtkMRMLMarkupsFiducialNode()
        pointListRed_World.SetName("pointListRed_World")
        slicer.mrmlScene.AddNode(pointListRed_World)
        # Set the color of the points to red
        pointListRed_World.GetDisplayNode().SetSelectedColor(1,0,0)
        # Set the role of the point list
        parameterNode.SetNodeReferenceID(self.POINTLIST_RED_WORLD, pointListRed_World.GetID())
  
  def updateOutputTable(self):
    '''Handles formating the input spectum for display in the output table'''
    # Get the table created by the selector
    parameterNode = self.getParameterNode()
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    tableNode = parameterNode.GetNodeReference(self.OUTPUT_TABLE)

    # Throw an error if the image has improper dimensions
    numberOfPoints = spectrumImageNode.GetImageData().GetDimensions()[0]
    numberOfRows = spectrumImageNode.GetImageData().GetDimensions()[1]
    if numberOfRows!=2:
      logging.error("Spectrum image is expected to have exactly 2 rows, got {0}".format(numberOfRows))
      return

    # Convert image to a displayable format
    specArray = slicer.util.arrayFromVolume(spectrumImageNode)
    specArray = np.squeeze(specArray)
    specArray = np.transpose(specArray)

    # Save results to a new table node
    if tableNode is None:
      tableNode = slicer.vtkMRMLTableNode()
      slicer.mrmlScene.AddNode(tableNode)
      # Name the table
      tableNode.SetName("OutputTable")
      parameterNode.SetNodeReferenceID(self.OUTPUT_TABLE, tableNode.GetID())
    slicer.util.updateTableFromArray(tableNode,specArray,["Wavelength","Intensity"])

    return specArray # *** Instead of returning the array, should I just save it to the parameter node?
    
  def updateChart(self):
    ''' Update the display chart using output table and classification prediction '''
    # specPred, specLabel = self.classifySpectra(specArray[743:-1,:]) 
    parameterNode = self.getParameterNode()
    spectrumImageNode = parameterNode.GetNodeReference(self.INPUT_VOLUME)
    tableNode = parameterNode.GetNodeReference(self.OUTPUT_TABLE)
    spectrumLabel = parameterNode.GetParameter(self.CLASSIFICATION)

    # Create PlotSeriesNode for the spectra
    plotSeriesNode = parameterNode.GetNodeReference(self.OUTPUT_SERIES)
    # If the plotSeriesNode does not exists then create it, set the role and set default properties
    if plotSeriesNode == None:
      plotSeriesNode = slicer.vtkMRMLPlotSeriesNode()
      slicer.mrmlScene.AddNode(plotSeriesNode)
      plotSeriesNode.SetName("Measured Spectrum")
      parameterNode.SetNodeReferenceID(self.OUTPUT_SERIES, plotSeriesNode.GetID())
      plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
      plotSeriesNode.SetXColumnName("Wavelength")
      plotSeriesNode.SetYColumnName("Intensity")
      plotSeriesNode.SetPlotType(plotSeriesNode.PlotTypeScatter)
      plotSeriesNode.SetColor(0, 0.6, 1.0)

    # Create PlotChartNode for the spectra
    plotChartNode = parameterNode.GetNodeReference(self.OUTPUT_CHART)
    # Create chart and add plot
    if plotChartNode == None:
      plotChartNode = slicer.vtkMRMLPlotChartNode()
      slicer.mrmlScene.AddNode(plotChartNode)
      parameterNode.SetNodeReferenceID(self.OUTPUT_CHART, plotChartNode.GetID())

      plotChartNode.SetAndObservePlotSeriesNodeID(plotSeriesNode.GetID())
      plotChartNode.YAxisRangeAutoOff() # The axes can be set or automatic by toggling between on and off
      plotChartNode.SetYAxisRange(0, 1)
      plotChartNode.SetXAxisTitle('Wavelength [nm]')
      plotChartNode.SetYAxisTitle('Intensity')  
    plotChartNode.SetTitle(str(spectrumLabel))
    # Show plot in layout
    slicer.modules.plots.logic().ShowChartInLayout(plotChartNode)

  def classifySpectra(self,X_test):
    ''' Classifies the spectra using the trained model, returns the predictions and text label '''
    # Get the max value in X_test to see if we will classify or not
    max_value = np.amax(X_test[:,1])
    X_test = self.normalize(X_test)
    X_test = X_test[:,1].reshape(1,-1)
    predicted = self.model.predict(X_test)
    # To ensure a strong, unsaturated signal
    if max_value < 0.0 or max_value > 9.95:
      label = self.CLASS_LABEL_NONE
    elif predicted[0] == 0:
      label = self.CLASS_LABEL_0
    elif predicted[0] == 1:
      label = self.CLASS_LABEL_1
    # Save the prediction to the parameter node
    parameterNode = self.getParameterNode()
    parameterNode.SetParameter(self.CLASSIFICATION, label)
    return predicted, label
  
  def normalize(data):
      ''' Normalizes the data to a range of 0 to 1 '''
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
  
#
# BroadbandSpecModuleTest
#

class BroadbandSpecModuleTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    # Tell user test is not implemented
    print("WARNING: No automated tests implemented for this module yet")
