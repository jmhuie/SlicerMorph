import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import fnmatch
import  numpy as np
import random
import math


#
# MergeMarkups
#

class MergeMarkups(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "MergeMarkups" # TODO make this more human readable by adding spaces
    self.parent.categories = ["SlicerMorph.SlicerMorph Utilities"]
    self.parent.dependencies = []
    self.parent.contributors = ["Sara Rolfe (UW), Murat Maga (UW)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
      This module interactively merges markups nodes.
      <p>For more information see the <a href="https://github.com/SlicerMorph/SlicerMorph/tree/master/Docs/MergeMarkups">online documentation.</a>.</p>
      """
    #self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
      This module was developed by Sara Rolfe, and Murat Maga for SlicerMorph. SlicerMorph was originally supported by an NSF/DBI grant, "An Integrated Platform for Retrieval, Visualization and Analysis of 3D Morphology From Digital Biological Collections"
      awarded to Murat Maga (1759883), Adam Summers (1759637), and Douglas Boyer (1759839).
      https://nsf.gov/awardsearch/showAward?AWD_ID=1759883&HistoricalAwards=false
      """ # replace with organization, grant and thanks.

    # Additional initialization step after application startup is complete
    slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#

def registerSampleData():
  """
  Add data sets to Sample Data module.
  """
  # It is always recommended to provide sample data for users to make it easy to try the module,
  # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

  import SampleData
  iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

  # To ensure that the source code repository remains small (can be downloaded and installed quickly)
  # it is recommended to store data sets that are larger than a few MB in a Github release.

  # TemplateKey1
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='TemplateKey',
    sampleName='TemplateKey1',
    # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
    # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
    thumbnailFileName=os.path.join(iconsPath, 'TemplateKey1.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
    fileNames='TemplateKey1.nrrd',
    # Checksum to ensure file integrity. Can be computed by this command:
    #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
    checksums = 'SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
    # This node name will be used when the data set is loaded
    nodeNames='TemplateKey1'
  )

  # TemplateKey2
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='TemplateKey',
    sampleName='TemplateKey2',
    thumbnailFileName=os.path.join(iconsPath, 'TemplateKey2.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
    fileNames='TemplateKey2.nrrd',
    checksums = 'SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
    # This node name will be used when the data set is loaded
    nodeNames='TemplateKey2'
  )


#
# MergeMarkupsWidget
#

class MergeMarkupsWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    # Set up tabs to split workflow
    tabsWidget = qt.QTabWidget()
    curvesTab = qt.QWidget()
    curvesTabLayout = qt.QFormLayout(curvesTab)
    fiducialsTab = qt.QWidget()
    fiducialsTabLayout = qt.QFormLayout(fiducialsTab)
    batchTab = qt.QWidget()
    batchTabLayout = qt.QFormLayout(batchTab)

    tabsWidget.addTab(curvesTab, "Merge Curves")
    tabsWidget.addTab(fiducialsTab, "Merge Landmark Sets")
    tabsWidget.addTab(batchTab, "Batch Merge Landmark Sets")
    self.layout.addWidget(tabsWidget)
    ################## Curves Tab
    #
    # Parameters Area
    #
    parametersCurveCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCurveCollapsibleButton.text = "Curve Viewer"
    curvesTabLayout.addRow(parametersCurveCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersCurveFormLayout = qt.QFormLayout(parametersCurveCollapsibleButton)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.continuousCurvesCheckBox = qt.QCheckBox()
    self.continuousCurvesCheckBox.checked = 0
    self.continuousCurvesCheckBox.setToolTip("If checked, redundant points will be removed on merging.")
    parametersCurveFormLayout.addRow("Contiuous curves", self.continuousCurvesCheckBox)

    #
    # markups view
    #
    self.markupsView = slicer.qMRMLSubjectHierarchyTreeView()
    self.markupsView.setMRMLScene(slicer.mrmlScene)
    self.markupsView.setMultiSelection(True)
    self.markupsView.setAlternatingRowColors(True)
    self.markupsView.setDragDropMode(qt.QAbstractItemView().DragDrop)
    self.markupsView.setColumnHidden(self.markupsView.model().transformColumn, True)
    self.markupsView.sortFilterProxyModel().setNodeTypes(["vtkMRMLMarkupsCurveNode"])
    parametersCurveFormLayout.addRow(self.markupsView)

    #
    # Merge Button
    #
    self.mergeButton = qt.QPushButton("Merge highlighted nodes")
    self.mergeButton.toolTip = "Generate a single merged markup file from the selected nodes"
    self.mergeButton.enabled = False
    parametersCurveFormLayout.addRow(self.mergeButton)

    # connections
    self.mergeButton.connect('clicked(bool)', self.onMergeButton)
    self.markupsView.connect('currentItemChanged(vtkIdType)', self.updateMergeButton)

    ################ Landmark Set Tab
    #
    # Parameters Area
    #
    parametersLMCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersLMCollapsibleButton.text = "Landmark Viewer"
    fiducialsTabLayout.addRow(parametersLMCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersLMFormLayout = qt.QGridLayout(parametersLMCollapsibleButton)

    #
    # markups view
    #
    self.markupsFiducialView = slicer.qMRMLSubjectHierarchyTreeView()
    self.markupsFiducialView.setMRMLScene(slicer.mrmlScene)
    self.markupsFiducialView.setMultiSelection(True)
    self.markupsFiducialView.setAlternatingRowColors(True)
    self.markupsFiducialView.setDragDropMode(qt.QAbstractItemView().DragDrop)
    self.markupsFiducialView.setColumnHidden(self.markupsView.model().transformColumn, True)
    self.markupsFiducialView.sortFilterProxyModel().setNodeTypes(["vtkMRMLMarkupsFiducialNode"])
    parametersLMFormLayout.addWidget(self.markupsFiducialView,0,0,1,3)

    #
    # Set landmark type menu
    #
    boxLabel = qt.QLabel("Select landmark type description to apply: ")
    self.LandmarkTypeSelection = qt.QComboBox()
    self.LandmarkTypeSelection.addItems(["Select","Fixed", "Semi", "No description"])
    parametersLMFormLayout.addWidget(boxLabel,1,0)
    parametersLMFormLayout.addWidget(self.LandmarkTypeSelection,1,1)


    #
    # Apply Landmark Type Button
    #
    self.ApplyLMButton = qt.QPushButton("Apply to highlighted nodes")
    self.ApplyLMButton.toolTip = "Apply the selected landmark type to points in the the selected nodes"
    self.ApplyLMButton.enabled = False
    parametersLMFormLayout.addWidget(self.ApplyLMButton,1,2)

    #
    # Merge Button
    #
    self.mergeLMButton = qt.QPushButton("Merge highlighted nodes")
    self.mergeLMButton.toolTip = "Generate a single merged markup file from the selected nodes"
    self.mergeLMButton.enabled = False
    parametersLMFormLayout.addWidget(self.mergeLMButton,2,0,1,3)

    # connections
    self.mergeLMButton.connect('clicked(bool)', self.onMergeLMButton)
    self.ApplyLMButton.connect('clicked(bool)', self.onApplyLMButton)
    self.markupsFiducialView.connect('currentItemChanged(vtkIdType)', self.updateMergeLMButton)
    self.LandmarkTypeSelection.connect('currentIndexChanged(int)', self.updateApplyLMButton)

    ################ Batch Run LM Merge Tab
    #
    # Fixed LM Area
    #
    fixedBatchCollapsibleButton = ctk.ctkCollapsibleButton()
    fixedBatchCollapsibleButton.text = "Fixed LM File Selection"
    batchTabLayout.addRow(fixedBatchCollapsibleButton)

    # Layout within the dummy collapsible button
    fixedBatchLayout = qt.QFormLayout(fixedBatchCollapsibleButton)

    #
    # Browse Fixed LM Button
    #
    self.browseFixedLMButton = qt.QPushButton("Select files...")
    self.browseFixedLMButton.toolTip = "Select one fixed landmark file for each subject"
    self.browseFixedLMButton.enabled = True
    fixedBatchLayout.addRow(self.browseFixedLMButton)

    #
    # File viewer box
    #
    self.fixedFileTable = qt.QTextEdit()
    fixedBatchLayout.addRow(self.fixedFileTable)

    #
    # Semi LM Area
    #
    semiBatchCollapsibleButton = ctk.ctkCollapsibleButton()
    semiBatchCollapsibleButton.text = "Semi LM File Selection"
    batchTabLayout.addRow(semiBatchCollapsibleButton)

    # Layout within the dummy collapsible button
    semiBatchLayout = qt.QFormLayout(semiBatchCollapsibleButton)

    #
    # Browse Fixed LM Button
    #
    self.browseSemiLMButton = qt.QPushButton("Select files...")
    self.browseSemiLMButton.toolTip = "Select one semi-landmark file for each subject, in the same order as the fixed landmarks"
    self.browseSemiLMButton.enabled = True
    semiBatchLayout.addRow(self.browseSemiLMButton)

    #
    # File viewer box
    #
    self.semiFileTable = qt.QTextEdit()
    semiBatchLayout.addRow(self.semiFileTable)

    #
    # Merge LM Area
    #
    batchMergeCollapsibleButton = ctk.ctkCollapsibleButton()
    batchMergeCollapsibleButton.text = "Run merge"
    batchTabLayout.addRow(batchMergeCollapsibleButton)

    # Layout within the dummy collapsible button
    batchMergeLayout = qt.QFormLayout(batchMergeCollapsibleButton)

    #
    # Select output landmark directory
    #
    self.outputDirectorySelector = ctk.ctkPathLineEdit()
    self.outputDirectorySelector.filters = ctk.ctkPathLineEdit.Dirs
    self.outputDirectorySelector.toolTip = "Select the output directory where the merged landmark nodes will be saved"
    batchMergeLayout.addRow("Select output landmark directory: ", self.outputDirectorySelector)

    #
    # Batch Merge Button
    #
    self.batchMergeButton = qt.QPushButton("Merge fixed and semi-landmark nodes")
    self.batchMergeButton.toolTip = "Generate a single merged markup file from the selected nodes"
    self.batchMergeButton.enabled = False
    batchMergeLayout.addRow(self.batchMergeButton)

    #
    # Clear Button
    #
    self.clearButton = qt.QPushButton("Clear landmark file selections")
    self.clearButton.toolTip = "Clear the landmark files selected in the viewer boxes"
    self.clearButton.enabled = False
    batchMergeLayout.addRow(self.clearButton)

    # connections
    self.browseFixedLMButton.connect('clicked(bool)', self.addFixedByBrowsing)
    self.browseSemiLMButton.connect('clicked(bool)', self.addSemiByBrowsing)
    self.outputDirectorySelector.connect('validInputChanged(bool)', self.onSelectDirectory)
    self.batchMergeButton.connect('clicked(bool)', self.onBatchMergeButton)
    self.clearButton.connect('clicked(bool)', self.onClearButton)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onMergeButton(self):
    logic = MergeMarkupsLogic()
    logic.runCurves(self.markupsView, self.continuousCurvesCheckBox.checked)

  def updateMergeButton(self):
    nodes=self.markupsView.selectedIndexes()
    self.mergeButton.enabled = bool(nodes)

  def updateMergeLMButton(self):
    nodes=self.markupsFiducialView.selectedIndexes()
    self.mergeLMButton.enabled = bool(nodes)

  def onMergeLMButton(self):
    logic = MergeMarkupsLogic()
    logic.runFiducials(self.markupsFiducialView)

  def updateApplyLMButton(self):
    self.ApplyLMButton.enabled = not bool(self.LandmarkTypeSelection.currentText == "Select")

  def onApplyLMButton(self):
    logic = MergeMarkupsLogic()
    if self.LandmarkTypeSelection.currentText == "No description":
      label = ""
    else:
      label = self.LandmarkTypeSelection.currentText
    logic.runApplyLandmarksType(self.markupsFiducialView, label)

  def addFixedByBrowsing(self):
    self.fixedFileTable.clear()
    self.fixedFilePaths = []
    filter = "landmark files (*.fcsv *.json)"
    self.fixedFilePaths = qt.QFileDialog().getOpenFileNames(None, "Window name", "", filter)
    self.fixedFileTable.plainText = '\n'.join(self.fixedFilePaths)
    self.clearButton.enabled = True

  def addSemiByBrowsing(self):
    self.semiFileTable.clear()
    self.semiFilePaths = []
    filter = "landmark files (*.fcsv *.json)"
    self.semiFilePaths = qt.QFileDialog().getOpenFileNames(None, "Window name", "", filter)
    self.semiFileTable.plainText = '\n'.join(self.semiFilePaths)
    self.clearButton.enabled = True

  def onSelectDirectory(self):
    self.batchMergeButton.enabled = bool (self.outputDirectorySelector.currentPath)

  def onBatchMergeButton(self):
    logic = MergeMarkupsLogic()
    if len(self.fixedFilePaths) == 0 or len(self.semiFilePaths)==0:
      warning = "Error: There are 0 files selected to merge."
      logging.debug(warning)
      slicer.util.messageBox(warning)
      return False
    if len(self.fixedFilePaths) != len(self.semiFilePaths):
      warning = "Error: The number of files in the fixed and semi-landmark selection boxes needs to be equal."
      logging.debug(warning)
      slicer.util.messageBox(warning)
      return False
    for index in range(len(self.fixedFilePaths)):
      fixed =  slicer.util.loadMarkups(self.fixedFilePaths[index])
      semi =  slicer.util.loadMarkups(self.semiFilePaths[index])
      logic.mergeLMNodes(fixed,semi)
      fixed.SetName(fixed.GetName()+'_merged')
      rootName, ext = os.path.splitext(self.fixedFilePaths[index])
      rootName, secondExt = os.path.splitext(rootName)
      outputFilePath = os.path.join(self.outputDirectorySelector.currentPath, fixed.GetName() + secondExt + ext)
      slicer.util.saveNode(fixed, outputFilePath)
      slicer.mrmlScene.RemoveNode(fixed)
      slicer.mrmlScene.RemoveNode(semi)
    return True

  def onClearButton(self):
    self.fixedFileTable.clear()
    self.fixedFilePaths = []
    self.semiFileTable.clear()
    self.semiFilePaths = []
    self.clearButton.enabled = False

#
# MergeMarkupsLogic
#

class MergeMarkupsLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
  def mergeLMNodes(self, fixedLM, semiLM):
    # merges semilandmarks into the fixed landmark set
    # if there are no landmark descriptions, these will be set according to the
    # fixed/semiLM box they were entered in
    for index in range(fixedLM.GetNumberOfControlPoints()):
      fiducialDescription = fixedLM.GetNthControlPointDescription(index)
      if fiducialDescription == "":
        fixedLM.SetNthControlPointDescription(index,"Fixed")
    for index in range(semiLM.GetNumberOfControlPoints()):
      pt = semiLM.GetNthControlPointPositionVector(index)
      fiducialLabel = semiLM.GetNthControlPointLabel(index)
      fiducialDescription = semiLM.GetNthControlPointDescription(index)
      fixedLM.AddControlPoint(pt,fiducialLabel)
      mergedIndex = fixedLM.GetNumberOfControlPoints()-1
      if fiducialDescription == "":
        fixedLM.SetNthControlPointDescription(mergedIndex,"Semi")
      else:
        fixedLM.SetNthControlPointDescription(mergedIndex,fiducialDescription)

  def runApplyLandmarksType(self, markupsTreeView, label):
    nodeIDs=markupsTreeView.selectedIndexes()
    for id in nodeIDs:
      if id.column() == 0:
        currentNode = slicer.util.getNode(id.data())
        self.setAllLandmarkDescriptions(currentNode, label)

  def setAllLandmarkDescriptions(self,landmarkNode, landmarkDescription):
    for controlPointIndex in range(landmarkNode.GetNumberOfControlPoints()):
      landmarkNode.SetNthControlPointDescription(controlPointIndex, landmarkDescription)

  def runFiducials(self, markupsTreeView):
    nodeIDs=markupsTreeView.selectedIndexes()
    nodeList = vtk.vtkCollection()
    for id in nodeIDs:
      if id.column() == 0:
        currentNode = slicer.util.getNode(id.data())
        nodeList.AddItem(currentNode)
    mergedNodeName = "mergedMarkupsNode"
    mergedNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', mergedNodeName)
    purple=[1,0,1]
    mergedNode.GetDisplayNode().SetSelectedColor(purple)
    self.mergeList(nodeList, mergedNode)
    return True

  def runCurves(self, markupsTreeView, continuousCurveOption):
    nodeIDs=markupsTreeView.selectedIndexes()
    nodeList = vtk.vtkCollection()
    for id in nodeIDs:
      if id.column() == 0:
        currentNode = slicer.util.getNode(id.data())
        nodeList.AddItem(currentNode)
    mergedNodeName = "mergedMarkupsNode"
    mergedNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsCurveNode', mergedNodeName)
    purple=[1,0,1]
    mergedNode.GetDisplayNode().SetSelectedColor(purple)
    self.mergeList(nodeList, mergedNode, continuousCurveOption)
    return True

  def mergeList(self, nodeList,mergedNode, continuousCurveOption=False):
    pointList=[]
    connectingNode=False
    # Add semi-landmark points within triangle patches
    for currentNode in nodeList:
      for index in range(currentNode.GetNumberOfControlPoints()):
        if not(index==0 and continuousCurveOption and connectingNode):
          pt = currentNode.GetNthControlPointPositionVector(index)
          pt_array = [pt.GetX(), pt.GetY(), pt.GetZ()]
          if pt_array not in pointList:
            pointList.append(pt_array)
            fiducialLabel = currentNode.GetNthControlPointLabel(index)
            fiducialDescription = currentNode.GetNthControlPointDescription(index)
            mergedNode.AddControlPoint(pt,fiducialLabel)
            mergedIndex = mergedNode.GetNumberOfControlPoints()-1
            mergedNode.SetNthControlPointDescription(mergedIndex,fiducialDescription)
      connectingNode=True
    return True

  def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """

    if not inputVolume or not outputVolume:
      raise ValueError("Input or output volume is invalid")

    import time
    startTime = time.time()
    logging.info('Processing started')

    # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
    cliParams = {
      'InputVolume': inputVolume.GetID(),
      'OutputVolume': outputVolume.GetID(),
      'ThresholdValue' : imageThreshold,
      'ThresholdType' : 'Above' if invert else 'Below'
      }
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
    # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    slicer.mrmlScene.RemoveNode(cliNode)

    stopTime = time.time()
    logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')


class MergeMarkupsTest(ScriptedLoadableModuleTest):
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
    self.test_MergeMarkups1()

  def test_MergeMarkups1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    registerSampleData()
    inputVolume = SampleData.downloadSample('TemplateKey1')
    self.delayDisplay('Loaded test data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 695)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 100

    # Test the module logic

    logic = MergeMarkupsLogic()

    # Test algorithm with non-inverted threshold
    logic.process(inputVolume, outputVolume, threshold, True)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], threshold)

    # Test algorithm with inverted threshold
    logic.process(inputVolume, outputVolume, threshold, False)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], inputScalarRange[1])

    self.delayDisplay('Test passed')
