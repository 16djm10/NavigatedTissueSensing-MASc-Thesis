import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import numpy as np

#
# SpectrumViewer
#

class SpectrumViewer(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SpectrumViewer" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    parent.contributors = ["Andras Lasso (Queen's University, PERK Lab)"] 
    self.parent.helpText = """
    Show a spectrum curve in real-time from a spectrum image received through OpenIGTLink. First line of the spectrum image contains wavelength, second line of the image contains intensities.
    """
    parent.acknowledgementText = """
    """

#
# SpectrumViewerWidget
#

class SpectrumViewerWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """  
  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    # VTKObservationMixin.__init__(self)
    slicer.mymod = self 
  
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    self.logic = SpectrumViewerLogic()
    
    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # Button to automatically connect to plus server
    #
    self.connectButton = qt.QPushButton()
    self.connectButton.text = "Connect"
    self.connectButton.enabled = True
    self.connectButton.setToolTip("Click to connect to the plus server")
    parametersFormLayout.addRow('Connect to plus server:',self.connectButton)

    #
    # input volume selector
    #
    self.spectrumImageSelector = slicer.qMRMLNodeComboBox()
    self.spectrumImageSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.spectrumImageSelector.selectNodeUponCreation = True
    self.spectrumImageSelector.addEnabled = False
    self.spectrumImageSelector.removeEnabled = False
    self.spectrumImageSelector.noneEnabled = False
    self.spectrumImageSelector.showHidden = False
    self.spectrumImageSelector.showChildNodeTypes = False
    self.spectrumImageSelector.setMRMLScene( slicer.mrmlScene )
    self.spectrumImageSelector.setToolTip( "Pick the spectrum image to visualize." )
    parametersFormLayout.addRow("Input spectrum image: ", self.spectrumImageSelector)
   
    #
    # output array selector
    #
    self.outputArraySelector = slicer.qMRMLNodeComboBox()
    self.outputArraySelector.nodeTypes = ( ("vtkMRMLTableNode"), "" ) # https://slicer.readthedocs.io/en/latest/developer_guide/mrml_overview.html
    self.outputArraySelector.addEnabled = True
    self.outputArraySelector.removeEnabled = True
    self.outputArraySelector.noneEnabled = False 
    self.outputArraySelector.showHidden = False
    self.outputArraySelector.showChildNodeTypes = False
    self.outputArraySelector.setMRMLScene( slicer.mrmlScene )
    self.outputArraySelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output spectrum Table: ", self.outputArraySelector)
   
    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enablePlottingCheckBox = qt.QCheckBox()
    self.enablePlottingCheckBox.checked = 0
    self.enablePlottingCheckBox.setToolTip("If checked, then the spectrum plot will be updated in real-time")
    parametersFormLayout.addRow("Enable plotting", self.enablePlottingCheckBox)

    # connections
    self.enablePlottingCheckBox.connect('stateChanged(int)', self.setEnablePlotting)
    self.connectButton.connect('clicked(bool)', self.onConnectButtonClicked)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass
    
  def setEnablePlotting(self, enable):
    if enable:
      self.logic.startPlotting(self.spectrumImageSelector.currentNode(), self.outputArraySelector.currentNode())
    else:
      self.logic.stopPlotting()


  def onConnectButtonClicked(self):
    nodeList = slicer.util.getNodesByClass('vtkMRMLIGTLConnectorNode') 
    if nodeList == []:
      connectorNode = slicer.vtkMRMLIGTLConnectorNode()
      slicer.mrmlScene.AddNode(connectorNode)
      connectorNode.SetTypeClient('localhost', 18944)
      connectorNode.Start()
      self.connectButton.text = 'Disconnect'
    else:
      connectorNode = nodeList[0]
      if connectorNode.GetState() == 0:
        connectorNode.Start()
        self.connectButton.text = 'Disconnect'
      else:
        connectorNode.Stop()
        self.connectButton.text = 'Connect' 

#
# SpectrumViewerLogic
#

class SpectrumViewerLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    
    self.chartNodeID = None
    self.spectrumImageNode = None
    self.observerTags = []
    self.outputArrayNode = None
    self.resolution = 100
    slicer.mymodLog = self
    self.plotChartNode = None 

  def addObservers(self):
    if self.spectrumImageNode:
      print("Add observer to {0}".format(self.spectrumImageNode.GetName()))
      self.observerTags.append([self.spectrumImageNode, self.spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onSpectrumImageNodeModified)])

  # This function does not work correctly as the plot continues to plot. ***
  def removeObservers(self):
    print("Remove observers")
    for nodeTagPair in self.observerTags:
      nodeTagPair[0].RemoveObserver(nodeTagPair[1])

  def startPlotting(self, spectrumImageNode, outputArrayNode):
    # Change the layout to one that has a chart.
    ln = slicer.util.getNode(pattern='vtkMRMLLayoutNode*')
    ln.SetViewArrangement(24)
    self.removeObservers()
    self.spectrumImageNode=spectrumImageNode
    self.outputArrayNode=outputArrayNode    

    # Start the updates
    self.addObservers()
    self.onSpectrumImageNodeModified(0,0)

  def stopPlotting(self):
    self.removeObservers()  

  def onSpectrumImageNodeModified(self, observer, eventid):
  
    if not self.spectrumImageNode or not self.outputArrayNode:
      return
  
    self.updateOutputTable()
    self.updateChart()
  
  def updateOutputTable(self):
    pass

  def updateChart(self):
    # Get the table created by the selector
    tableNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLTableNode')

    # Throw an error if the image has improper dimensions
    numberOfPoints = self.spectrumImageNode.GetImageData().GetDimensions()[0]
    numberOfRows = self.spectrumImageNode.GetImageData().GetDimensions()[1]
    if numberOfRows!=2:
      logging.error("Spectrum image is expected to have exactly 2 rows, got {0}".format(numberOfRows))
      return

    # Get the image from the volume selector
    specIm = self.spectrumImageNode
    # Convert it to a displayable format
    specArray = slicer.util.arrayFromVolume(specIm)
    specArray = np.squeeze(specArray)
    specArray = np.transpose(specArray)

    # Save results to a new table node
    if slicer.util.getNodesByClass('vtkMRMLTableNode') == []:
      tableNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
    slicer.util.updateTableFromArray(tableNode,specArray,["Wavelength","Intensity"])

    # Create plot
    if slicer.util.getNodesByClass('vtkMRMLPlotSeriesNode') == []:
      plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", specIm.GetName() + " plot")
    plotSeriesNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLPlotSeriesNode") 
    plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
    plotSeriesNode.SetXColumnName("Wavelength")
    plotSeriesNode.SetYColumnName("Intensity")
    plotSeriesNode.SetPlotType(plotSeriesNode.PlotTypeScatter)
    plotSeriesNode.SetColor(0, 0.6, 1.0)

    # Create chart and add plot
    if slicer.util.getNodesByClass('vtkMRMLPlotChartNode') == []:
      plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")
    plotChartNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLPlotChartNode") 
    plotChartNode.SetAndObservePlotSeriesNodeID(plotSeriesNode.GetID())
    plotChartNode.YAxisRangeAutoOn() # The axes can be set or automatic by toggling between on and off
    # plotChartNode.SetYAxisRange(0, 2)
    plotChartNode.SetTitle('Spectrum')
    plotChartNode.SetXAxisTitle('Wavelength [nm]')
    plotChartNode.SetYAxisTitle('Intensity')
    self.plotChartNode = plotChartNode 

    # Show plot in layout
    slicer.modules.plots.logic().ShowChartInLayout(plotChartNode)

class SpectrumViewerTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SpectrumViewer1()

  def test_SpectrumViewer1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay('Test passed! (No testing was actually performed)')
