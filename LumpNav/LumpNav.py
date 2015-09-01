import os, datetime
import unittest
from __main__ import vtk, qt, ctk, slicer

from GuideletLib import *
import logging
import time

#
# LumpNav ###
#

class LumpNav(GuideletLoadable):
  """Uses GuideletLoadable class, available at:
  """

  def __init__(self, parent):
    GuideletLoadable.__init__(self, parent)
    self.parent.title = "Lumpectomy Navigation"
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Tamas Ungi (Perk Lab)"]
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.    

#
# LumpNavWidget
#

class LumpNavWidget(GuideletWidget):
  """Uses GuideletWidget base class, available at:
  """

  def __init__(self, parent = None):
    GuideletWidget.__init__(self, parent)
    self.selectedConfigurationName = 'Default'
    
  def setup(self):
    # Adds default configurations to Slicer.ini
    self.addDefaultConfiguration()
    
    GuideletWidget.setup(self)
    
  def addLauncherWidgets(self):  
    GuideletWidget.addLauncherWidgets(self)
    
    # Configurations
    self.addConfigurationsSelector()
    
    # BreachWarning
    self.breachWarningLight()  
    
  # Adds a default configurations to Slicer.ini
  def addDefaultConfiguration(self):
    settings = slicer.app.userSettings() 
    settings.beginGroup(self.moduleName + '/Configurations/Default')
    if not settings.allKeys(): # If no keys in /Configurations/Default     
      settings.setValue('EnableBreachWarningLight', 'True')
      settings.setValue('TipToSurfaceDistanceCrossHair', 'True')
      settings.setValue('TipToSurfaceDistanceText', 'True')
      settings.setValue('TipToSurfaceDistanceTrajectory', 'True')
      settings.setValue('needleModelToNeedleTip', '0 1 0 0 0 0 1 0 1 0 0 0 0 0 0 1')
      settings.setValue('cauteryModelToCauteryTip', '0 0 1 0 0 -1 0 0 1 0 0 0 0 0 0 1')      
      logging.debug('Default configuration added')                
    settings.endGroup()      

  # Adds a list box populated with the available configurations in the Slicer.ini file
  def addConfigurationsSelector(self):
    self.configurationsComboBox = qt.QComboBox()
    configurationsLabel = qt.QLabel("Select Configuration: ")
    hBox = qt.QHBoxLayout()
    hBox.addWidget(configurationsLabel)
    hBox.addWidget(self.configurationsComboBox)    
    hBox.setStretch(1,2)
    self.launcherFormLayout.addRow(hBox)
    
    # Populate configurationsComboBox with available configurations
    settings = slicer.app.userSettings() 
    settings.beginGroup(self.moduleName + '/Configurations')
    configurations = settings.childGroups()
    for configuration in configurations:
      self.configurationsComboBox.addItem(configuration)
    settings.endGroup()
    
    # Set latest used configuration
    if settings.value(self.moduleName + '/MostRecentConfiguration'):
      idx = self.configurationsComboBox.findText(settings.value(self.moduleName + '/MostRecentConfiguration'))
      self.configurationsComboBox.setCurrentIndex(idx)      
    
    self.configurationsComboBox.connect('currentIndexChanged(const QString &)', self.onConfigurationChanged)
    
  def onConfigurationChanged(self, selectedConfigurationName):
    self.selectedConfigurationName = selectedConfigurationName
    settings = slicer.app.userSettings() 
    settings.setValue(self.moduleName + '/MostRecentConfiguration', selectedConfigurationName)   
    lightEnabled = settings.value(self.moduleName + '/Configurations/' + selectedConfigurationName + '/EnableBreachWarningLight')    
    self.breachWarningLightCheckBox.checked = (lightEnabled == 'True')  
    
  def breachWarningLight(self):
    lnNode = slicer.util.getNode(self.moduleName)
    
    self.breachWarningLightCheckBox = qt.QCheckBox()
    checkBoxLabel = qt.QLabel()
    hBoxCheck = qt.QHBoxLayout()
    hBoxCheck.setAlignment(0x0001)
    checkBoxLabel.setText("Use Breach Warning Light: ")
    hBoxCheck.addWidget(checkBoxLabel)
    hBoxCheck.addWidget(self.breachWarningLightCheckBox)
    hBoxCheck.setStretch(1,2)
    self.launcherFormLayout.addRow(hBoxCheck)

    if(lnNode is not None and lnNode.GetParameter('EnableBreachWarningLight')):
        # logging.debug("There is already a connector EnableBreachWarningLight parameter " + lnNode.GetParameter('EnableBreachWarningLight'))
        self.breachWarningLightCheckBox.checked = lnNode.GetParameter('EnableBreachWarningLight')
        self.breachWarningLightCheckBox.setDisabled(True)
    else:
        self.breachWarningLightCheckBox.setEnabled(True)
        settings = slicer.app.userSettings()
        lightEnabled = settings.value(self.moduleName + '/Configurations/' + self.selectedConfigurationName + '/EnableBreachWarningLight', 'True')
        self.breachWarningLightCheckBox.checked = (lightEnabled == 'True')
        
    self.breachWarningLightCheckBox.connect('stateChanged(int)', self.onBreachWarningLightChanged)
  
  def onBreachWarningLightChanged(self, state):    
    lightEnabled = ''
    if self.breachWarningLightCheckBox.checked:
      lightEnabled = 'True'
    elif not self.breachWarningLightCheckBox.checked:
      lightEnabled = 'False'    
    settings = slicer.app.userSettings()   
    settings.setValue(self.moduleName + '/Configurations/' + self.selectedConfigurationName + '/EnableBreachWarningLight', lightEnabled)
  
  def collectParameterList(self):
    parameterlist = GuideletWidget.collectParameterList(self)

    # BreachWarning
    if(self.breachWarningLightCheckBox.isEnabled()):
        lightEnabled = 'False'
        if self.breachWarningLightCheckBox.isChecked():
          lightEnabled = 'True'
        if parameterlist!=None:
          parameterlist['EnableBreachWarningLight'] = lightEnabled
        settings = slicer.app.userSettings()
        settings.setValue(self.moduleName + '/Configurations/' + self.selectedConfigurationName + '/EnableBreachWarningLight', lightEnabled)

    # Configuration   
    settings = slicer.app.userSettings() 
    settings.beginGroup(self.moduleName + '/Configurations/' + self.selectedConfigurationName)    
    keys = settings.allKeys()
    for key in keys:
      parameterlist[key] = settings.value(key) 
    settings.endGroup()
    
    return parameterlist

  def createGuideletInstance(self, parameterList = None):
    return LumpNavGuidelet(None, self.guideletLogic,  self.selectedConfigurationName, parameterList)

  def createGuideletLogic(self):
    return LumpNavLogic()

#
# LumpNavLogic ###
#

class LumpNavLogic(GuideletLogic):
  """Uses GuideletLogic base class, available at:
  """ #TODO add path

  def __init__(self, parent = None):
    GuideletLogic.__init__(self, parent)

  def createParameterNode(self):
    node = GuideletLogic.createParameterNode(self)
    parameterList = {'RecordingFilenamePrefix': "LumpNavRecording-",
                     'RecordingFilenameExtension': ".mhd",
                     'DefaultSavedScenesPath': os.path.dirname(slicer.modules.lumpnav.path)+'/SavedScenes',
                     'PivotCalibrationErrorThresholdMm':  0.9,
                     'PivotCalibrationDurationSec': 5,
                     'EnableBreachWarningLight':'True',
                     'BreachWarningLightMarginSizeMm':2.0,
                     'TestMode':'False',
                     }

    for parameter in parameterList:
      if not node.GetParameter(parameter):
        node.SetParameter(parameter, str(parameterList[parameter]))

    return node
	
#	
#	LumpNavTest ###
#

class LumpNavTest(GuideletTest):
  """This is the test case for your scripted module.
  """
  
  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    GuideletTest.runTest(self)
    #self.test_LumpNav1() #add applet specific tests here

class LumpNavGuidelet(Guidelet):

  def __init__(self, parent, logic, configurationName='Default', parameterList=None, widgetClass=None):
    Guidelet.__init__(self, parent, logic, configurationName, parameterList, widgetClass)
    logging.debug('LumpNavGuidelet.__init__')

    moduleDirectoryPath = slicer.modules.lumpnav.path.replace('LumpNav.py', '')

    # Set up main frame.

    self.sliceletDockWidget.setObjectName('LumpNavPanel')
    self.sliceletDockWidget.setWindowTitle('LumpNav')
    self.mainWindow.setWindowTitle('Lumpectomy navigation')
    self.mainWindow.windowIcon = qt.QIcon(moduleDirectoryPath + '/Resources/Icons/LumpNav.png')
    
    self.pivotCalibrationLogic=slicer.modules.pivotcalibration.logic()

    self.addConnectorObservers()
    
    # Setting up callback functions for widgets.
    self.setupConnections()
    
    # Set needle and cautery transforms and models
    self.tumorMarkups_Needle = None
    self.tumorMarkups_NeedleObserver = None
    self.setupScene()

    # Setup LIM specific
    self.setupLumpNavLIM('C:/Mikael/src/LumpNavLIM/Data/')
    
    # Setting button open on startup.
    self.calibrationCollapsibleButton.setProperty('collapsed', False)
    
    self.showFullScreen()

  def createFeaturePanels(self):
    featurePanelList = Guidelet.createFeaturePanels(self)

     # Create GUI panels.

    self.calibrationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.addTumorContouringToUltrasoundPanel()
    self.navigationCollapsibleButton = ctk.ctkCollapsibleButton()

    self.setupCalibrationPanel()
    self.setupNavigationPanel()

    featurePanelList[len(featurePanelList):] = [self.calibrationCollapsibleButton, self.navigationCollapsibleButton]

    return featurePanelList

  def __del__(self):#common
    self.cleanup()

  # Clean up when slicelet is closed
  def cleanup(self):#common
    Guidelet.cleanup(self)
    logging.debug('cleanup')
    self.breachWarningNode.UnRegister(slicer.mrmlScene)
    self.setAndObserveTumorMarkupsNode(None)
    self.breachWarningLightLogic.stopLightFeedback()
    
  def setupConnections(self):
    logging.debug('LumpNav.setupConnections()')
    Guidelet.setupConnections(self)

    self.calibrationCollapsibleButton.connect('toggled(bool)', self.onCalibrationPanelToggled)
    self.navigationCollapsibleButton.connect('toggled(bool)', self.onNavigationPanelToggled)

    self.cauteryPivotButton.connect('clicked()', self.onCauteryPivotClicked)
    self.needlePivotButton.connect('clicked()', self.onNeedlePivotClicked)
    self.placeButton.connect('clicked(bool)', self.onPlaceClicked)
    self.deleteLastFiducialButton.connect('clicked()', self.onDeleteLastFiducialClicked)
    self.deleteLastFiducialDuringNavigationButton.connect('clicked()', self.onDeleteLastFiducialClicked)    
    self.deleteAllFiducialsButton.connect('clicked()', self.onDeleteAllFiducialsClicked)
    
    #self.rightCameraButton.connect('clicked()', self.onRightCameraButtonClicked)
    self.leftCameraButton.connect('clicked()', self.onLeftCameraButtonClicked)

    self.setupIntuitiveViewButton.connect('clicked()', self.onSetupIntuitiveViewClicked) 
    self.setFocalPointRButton.connect('clicked()', self.setFocalPointRClicked)
    self.setFocalPointAButton.connect('clicked()', self.setFocalPointAClicked)  
    self.setFocalPointSButton.connect('clicked()', self.setFocalPointSClicked)
     
    self.placeTumorPointAtCauteryTipButton.connect('clicked(bool)', self.onPlaceTumorPointAtCauteryTipClicked)

    self.pivotSamplingTimer.connect('timeout()',self.onPivotSamplingTimeout)

    import Viewpoint
    self.viewpointLogic = Viewpoint.ViewpointLogic()
    self.cameraViewAngleSlider.connect('valueChanged(double)', self.viewpointLogic.SetCameraViewAngleDeg)
    self.cameraXPosSlider.connect('valueChanged(double)', self.viewpointLogic.SetCameraXPosMm)
    self.cameraYPosSlider.connect('valueChanged(double)', self.viewpointLogic.SetCameraYPosMm)
    self.cameraZPosSlider.connect('valueChanged(double)', self.viewpointLogic.SetCameraZPosMm)    
    
  def setupScene(self): #applet specific
    print (self.parameterNode.GetParameter('EnableBreachWarningLight')=='True')
    logging.debug('setupScene')
    Guidelet.setupScene(self)

    logging.debug('Create transforms')

    self.cauteryTipToCautery = slicer.util.getNode('CauteryTipToCautery')
    if not self.cauteryTipToCautery:
      self.cauteryTipToCautery=slicer.vtkMRMLLinearTransformNode()
      self.cauteryTipToCautery.SetName("CauteryTipToCautery")
      m = self.readTransformFromSettings('CauteryTipToCautery') 
      if m:
        self.cauteryTipToCautery.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.cauteryTipToCautery)

    self.cauteryModelToCauteryTip = slicer.util.getNode('CauteryModelToCauteryTip')
    if not self.cauteryModelToCauteryTip:
      self.cauteryModelToCauteryTip=slicer.vtkMRMLLinearTransformNode()
      self.cauteryModelToCauteryTip.SetName("CauteryModelToCauteryTip")
      m = self.readTransformFromSettings('CauteryModelToCauteryTip') 
      if m:
        self.cauteryTipToCautery.SetMatrixTransformToParent(m)
      self.cauteryModelToCauteryTip.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.cauteryModelToCauteryTip)

    self.needleTipToNeedle = slicer.util.getNode('NeedleTipToNeedle')
    if not self.needleTipToNeedle:
      self.needleTipToNeedle=slicer.vtkMRMLLinearTransformNode()
      self.needleTipToNeedle.SetName("NeedleTipToNeedle")
      m = self.readTransformFromSettings('NeedleTipToNeedle') 
      if m:
        self.needleTipToNeedle.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.needleTipToNeedle)      
      
    self.needleModelToNeedleTip = slicer.util.getNode('NeedleModelToNeedleTip')
    if not self.needleModelToNeedleTip:
      self.needleModelToNeedleTip=slicer.vtkMRMLLinearTransformNode()
      self.needleModelToNeedleTip.SetName("NeedleModelToNeedleTip")
      m = self.readTransformFromSettings('NeedleModelToNeedleTip') 
      if m:
        self.cauteryTipToCautery.SetMatrixTransformToParent(m)
      self.needleModelToNeedleTip.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.needleModelToNeedleTip)

    self.cauteryCameraToCautery = slicer.util.getNode('CauteryCameraToCautery')
    if not self.cauteryCameraToCautery:
      self.cauteryCameraToCautery=slicer.vtkMRMLLinearTransformNode()
      self.cauteryCameraToCautery.SetName("CauteryCameraToCautery")
      m = vtk.vtkMatrix4x4()
      m.SetElement( 0, 0, 0 )
      m.SetElement( 0, 2, -1 )
      m.SetElement( 1, 1, 0 )
      m.SetElement( 1, 0, 1 )
      m.SetElement( 2, 2, 0 )
      m.SetElement( 2, 1, -1 )
      self.cauteryCameraToCautery.SetMatrixTransformToParent(m)
      slicer.mrmlScene.AddNode(self.cauteryCameraToCautery)

    self.CauteryToNeedle = slicer.util.getNode('CauteryToNeedle')
    if not self.CauteryToNeedle:
      self.CauteryToNeedle=slicer.vtkMRMLLinearTransformNode()
      self.CauteryToNeedle.SetName("CauteryToNeedle")
      slicer.mrmlScene.AddNode(self.CauteryToNeedle)
      
    # Create transforms that will be updated through OpenIGTLink
      
    self.cauteryToReference = slicer.util.getNode('CauteryToReference')
    if not self.cauteryToReference:
      self.cauteryToReference=slicer.vtkMRMLLinearTransformNode()
      self.cauteryToReference.SetName("CauteryToReference")
      slicer.mrmlScene.AddNode(self.cauteryToReference)

    self.needleToReference = slicer.util.getNode('NeedleToReference')
    if not self.needleToReference:
      self.needleToReference=slicer.vtkMRMLLinearTransformNode()
      self.needleToReference.SetName("NeedleToReference")
      slicer.mrmlScene.AddNode(self.needleToReference)
      
    # Cameras
    logging.debug('Create cameras')
      
    self.LeftCamera = slicer.util.getNode('Left Camera')
    if not self.LeftCamera:
      self.LeftCamera=slicer.vtkMRMLCameraNode()
      self.LeftCamera.SetName("Left Camera")
      slicer.mrmlScene.AddNode(self.LeftCamera)

    self.RightCamera = slicer.util.getNode('Right Camera')
    if not self.RightCamera:
      self.RightCamera=slicer.vtkMRMLCameraNode()
      self.RightCamera.SetName("Right Camera")
      slicer.mrmlScene.AddNode(self.RightCamera)
    
    # Models
    logging.debug('Create models')

    self.cauteryModel_CauteryTip = slicer.util.getNode('CauteryModel')
    if not self.cauteryModel_CauteryTip:
      if (self.parameterNode.GetParameter('TestMode')=='True'):
          moduleDirectoryPath = slicer.modules.lumpnav.path.replace('LumpNav.py', '')
          slicer.util.loadModel(qt.QDir.toNativeSeparators(moduleDirectoryPath + '../../../models/temporary/cautery.stl'))
          self.cauteryModel_CauteryTip=slicer.util.getNode(pattern="cautery")
      else:
          slicer.modules.createmodels.logic().CreateNeedle(100,1.0,2.5,0)
          self.cauteryModel_CauteryTip=slicer.util.getNode(pattern="NeedleModel")
          self.cauteryModel_CauteryTip.GetDisplayNode().SetColor(1.0, 1.0, 0)
      self.cauteryModel_CauteryTip.SetName("CauteryModel")

    self.needleModel_NeedleTip = slicer.util.getNode('NeedleModel')
    if not self.needleModel_NeedleTip:
      slicer.modules.createmodels.logic().CreateNeedle(80,1.0,2.5,0)
      self.needleModel_NeedleTip=slicer.util.getNode(pattern="NeedleModel")
      self.needleModel_NeedleTip.GetDisplayNode().SetColor(0.333333, 1.0, 1.0)
      self.needleModel_NeedleTip.SetName("NeedleModel")
      self.needleModel_NeedleTip.GetDisplayNode().SliceIntersectionVisibilityOn()

    # Create surface from point set
    
    logging.debug('Create surface from point set')

    self.tumorModel_Needle = slicer.util.getNode('TumorModel')
    if not self.tumorModel_Needle:
      self.tumorModel_Needle = slicer.vtkMRMLModelNode()
      self.tumorModel_Needle.SetName("TumorModel")
      sphereSource = vtk.vtkSphereSource()
      sphereSource.SetRadius(0.001)
      self.tumorModel_Needle.SetPolyDataConnection(sphereSource.GetOutputPort())      
      slicer.mrmlScene.AddNode(self.tumorModel_Needle)
      # Add display node
      modelDisplayNode = slicer.vtkMRMLModelDisplayNode()
      modelDisplayNode.SetColor(0,1,0) # Green
      modelDisplayNode.BackfaceCullingOff()
      modelDisplayNode.SliceIntersectionVisibilityOn()
      modelDisplayNode.SetSliceIntersectionThickness(4)
      modelDisplayNode.SetOpacity(0.3) # Between 0-1, 1 being opaque
      slicer.mrmlScene.AddNode(modelDisplayNode)
      self.tumorModel_Needle.SetAndObserveDisplayNodeID(modelDisplayNode.GetID())

    tumorMarkups_Needle = slicer.util.getNode('T')
    if not tumorMarkups_Needle:
      tumorMarkups_Needle = slicer.vtkMRMLMarkupsFiducialNode()
      tumorMarkups_Needle.SetName("T")
      slicer.mrmlScene.AddNode(tumorMarkups_Needle)
      tumorMarkups_Needle.CreateDefaultDisplayNodes()
      tumorMarkups_Needle.GetDisplayNode().SetTextScale(0)
    self.setAndObserveTumorMarkupsNode(tumorMarkups_Needle)

    # Set up breach warning node
    logging.debug('Set up breach warning')
    self.breachWarningNode = slicer.util.getNode('LumpNavBreachWarning')

    if not self.breachWarningNode:
      self.breachWarningNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLBreachWarningNode')
      self.breachWarningNode.SetName("LumpNavBreachWarning")
      slicer.mrmlScene.AddNode(self.breachWarningNode)
      self.breachWarningNode.SetPlayWarningSound(True)
      self.breachWarningNode.SetWarningColor(1,0,0)
      self.breachWarningNode.SetOriginalColor(self.tumorModel_Needle.GetDisplayNode().GetColor())
      self.breachWarningNode.SetAndObserveToolTransformNodeId(self.cauteryTipToCautery.GetID())
      self.breachWarningNode.SetAndObserveWatchedModelNodeID(self.tumorModel_Needle.GetID())
      
    # Set up breach warning light
    import BreachWarningLight
    # logging.debug('Set up breach warning light')
    # self.breachWarningLightLogic = BreachWarningLight.BreachWarningLightLogic()
    # self.breachWarningLightLogic.setMarginSizeMm(float(self.parameterNode.GetParameter('BreachWarningLightMarginSizeMm')))
    # if (self.parameterNode.GetParameter('EnableBreachWarningLight')=='True'):
      # logging.debug("BreachWarningLight: active")
      # self.breachWarningLightLogic.startLightFeedback(self.breachWarningNode, self.connectorNode)
    # else:
      # logging.debug("BreachWarningLight: shutdown")
    # self.breachWarningLightLogic.shutdownLight(self.connectorNode)

    # Build transform tree
    logging.debug('Set up transform tree')
    self.cauteryToReference.SetAndObserveTransformNodeID(self.ReferenceToRas.GetID())
    self.cauteryCameraToCautery.SetAndObserveTransformNodeID(self.cauteryToReference.GetID())
    self.cauteryTipToCautery.SetAndObserveTransformNodeID(self.cauteryToReference.GetID())
    self.cauteryModelToCauteryTip.SetAndObserveTransformNodeID(self.cauteryTipToCautery.GetID())
    self.needleToReference.SetAndObserveTransformNodeID(self.ReferenceToRas.GetID())
    self.needleTipToNeedle.SetAndObserveTransformNodeID(self.needleToReference.GetID())
    self.needleModelToNeedleTip.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID())
    self.cauteryModel_CauteryTip.SetAndObserveTransformNodeID(self.cauteryModelToCauteryTip.GetID())
    self.needleModel_NeedleTip.SetAndObserveTransformNodeID(self.needleModelToNeedleTip.GetID())
    self.tumorModel_Needle.SetAndObserveTransformNodeID(self.needleToReference.GetID())
    self.tumorMarkups_Needle.SetAndObserveTransformNodeID(self.needleToReference.GetID())      
    # self.liveUltrasoundNode_Reference.SetAndObserveTransformNodeID(self.ReferenceToRas.GetID())
    
    # Hide slice view annotations (patient name, scale, color bar, etc.) as they
    # decrease reslicing performance by 20%-100%
    logging.debug('Hide slice view annotations')
    import DataProbe
    dataProbeUtil=DataProbe.DataProbeLib.DataProbeUtil()
    dataProbeParameterNode=dataProbeUtil.getParameterNode()
    dataProbeParameterNode.SetParameter('showSliceViewAnnotations', '0')

###############################################################################
### Start LIM stuff     
###############################################################################

  def setupLumpNavLIM(self, folderPath):
    logging.info('setupLumpNavLIM')
    
    self.cauteryTipToNeedleTip = None
    
    self.cmdUpdateTransform = slicer.modulelogic.vtkSlicerOpenIGTLinkCommand()
    self.cmdUpdateTransform.SetCommandTimeoutSec(15);
    self.cmdUpdateTransform.SetCommandName('UpdateTransform')   
    
    # Load breast model and texture plus corresponding fiducials
    slicer.util.loadMarkupsFiducialList(folderPath + 'FiducialsBreastModel.fcsv')
    slicer.util.loadModel(folderPath + 'BreastModel.obj')
    slicer.util.loadVolume(folderPath + 'BreastModelTexture.png')
    
    self.breastModel = slicer.util.getNode(pattern="BreastModel")
    if self.breastModel:
      self.breastModel.SetDisplayVisibility(False)
      
    self.fiducialsBreastModel = slicer.util.getNode(pattern="FiducialsBreastModel")
    if self.fiducialsBreastModel:
      self.fiducialsBreastModel.SetDisplayVisibility(False)
    
    self.breastModelTexture = slicer.util.getNode(pattern="BreastModelTexture")
    if self.breastModelTexture:
      self.breastModelTexture.SetDisplayVisibility(False)
      
    # Create transforms
    self.breastModelToBreast = slicer.util.getNode('BreastModelToBreast')    
    if not self.breastModelToBreast:
      self.breastModelToBreast = slicer.vtkMRMLLinearTransformNode()
      self.breastModelToBreast.SetName('BreastModelToBreast')
      slicer.mrmlScene.AddNode(self.breastModelToBreast)

    self.fRBLToSLPR = slicer.util.getNode('FRBLToSLPR')    
    if not self.fRBLToSLPR:
      self.fRBLToSLPR = slicer.vtkMRMLLinearTransformNode()
      self.fRBLToSLPR.SetName('FRBLToSLPR')
      slicer.mrmlScene.AddNode(self.fRBLToSLPR)
      
    # Create fiducials
    self.fiducialsFRBL = slicer.util.getNode('FiducialsFRBL')    
    if not self.fiducialsFRBL:
      self.fiducialsFRBL = slicer.vtkMRMLMarkupsFiducialNode()
      self.fiducialsFRBL.SetName('FiducialsFRBL')
      slicer.mrmlScene.AddNode(self.fiducialsFRBL)
      self.fiducialsFRBL.SetDisplayVisibility(False)
      
    self.fiducialsSLPR = slicer.util.getNode('FiducialsSLPR')    
    if not self.fiducialsSLPR:
      self.fiducialsSLPR = slicer.vtkMRMLMarkupsFiducialNode()
      self.fiducialsSLPR.SetName('FiducialsSLPR')
      self.fiducialsSLPR.AddFiducial(0, 100, 0)
      self.fiducialsSLPR.SetNthFiducialLabel(0, 'S')
      self.fiducialsSLPR.AddFiducial(-100, 0, 0)
      self.fiducialsSLPR.SetNthFiducialLabel(1, 'L')
      self.fiducialsSLPR.AddFiducial(0, -100, 0)
      self.fiducialsSLPR.SetNthFiducialLabel(2, 'P')
      self.fiducialsSLPR.AddFiducial(100, 0, 0)
      self.fiducialsSLPR.SetNthFiducialLabel(3, 'R')   
      slicer.mrmlScene.AddNode(self.fiducialsSLPR)
      self.fiducialsSLPR.SetDisplayVisibility(False)
    
    # Build transform tree
    self.ReferenceToRas.SetAndObserveTransformNodeID(self.fRBLToSLPR.GetID())
    self.fiducialsBreastModel.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID()) 
    self.breastModelToBreast.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID())        
    self.breastModel.SetAndObserveTransformNodeID(self.breastModelToBreast.GetID())
    
    # Import distanceToModelLogic
    import DistanceToModel
    self.distanceToModelLogic = DistanceToModel.DistanceToModelLogic(self.tumorModel_Needle)
    
    # Show ultrasound in red view again.
    layoutManager = self.layoutManager
    redSlice = layoutManager.sliceWidget('Red')
    redSliceLogic = redSlice.sliceLogic()
    redSliceLogic.GetSliceCompositeNode().SetBackgroundVolumeID(slicer.util.getNode('Image_Reference').GetID())
    
  # Uses: Fiducial Registration module in 3D Slicer
  def fiducialRegistration(self, saveTransform, fixedLandmarks, movingLandmarks, transformType):
    logging.info("Fiducial registration starts")
    parameters = {}
    rms = 0
    parameters["fixedLandmarks"] = fixedLandmarks.GetID()
    parameters["movingLandmarks"] = movingLandmarks.GetID()
    parameters["saveTransform"] = saveTransform.GetID()
    parameters["rms"] = rms 
    parameters["transformType"] = transformType
    fidReg = slicer.modules.fiducialregistration
    slicer.cli.run(fidReg, None, parameters)
    logging.info("Fiducial registration finished")
    
    return True

  # From: PLUS Remote module in 3D Slicer
  def updatePlusTransform(self, connectorNodeId, transformNode):
    # Get transform matrix as string
    transformMatrix = transformNode.GetMatrixTransformToParent()
    transformValue = ""
    for i in range(0,4):
      for j in range(0,4):
        transformValue = transformValue + str(transformMatrix.GetElement(i,j)) + " "
    transformValue = transformValue[:-1] # remove last character (extra space at the end)
    # Get transform date as string
    transformDate = str(datetime.datetime.now())

    self.cmdUpdateTransform.SetCommandAttribute('TransformName', transformNode.GetName())
    self.cmdUpdateTransform.SetCommandAttribute('TransformValue', transformValue)
    self.cmdUpdateTransform.SetCommandAttribute('TransformDate', transformDate)
    slicer.modules.openigtlinkremote.logic().SendCommand(self.cmdUpdateTransform, connectorNodeId)
    
    logging.info('INFO | ' + transformNode.GetName() + ' added to PLUS.')
    
  def onSetupIntuitiveViewClicked(self):
    if self.setupIntuitiveViewButton.text == 'Record Front Position':
      self.recordCauteryTipToNeedleTipPoint()
      self.setupIntuitiveViewButton.setText('Record Right Position')     
      
    elif self.setupIntuitiveViewButton.text == 'Record Right Position':
      self.recordCauteryTipToNeedleTipPoint()
      self.setupIntuitiveViewButton.setText('Record Back Position')  
      
    elif self.setupIntuitiveViewButton.text == 'Record Back Position':
      self.recordCauteryTipToNeedleTipPoint()
      self.setupIntuitiveViewButton.setText('Record Left Position')  
      
    elif self.setupIntuitiveViewButton.text == 'Record Left Position':
      self.setupIntuitiveViewButton.enabled = False
      self.addTextureToModel(self.breastModel, self.breastModelTexture)
      self.recordCauteryTipToNeedleTipPoint()
      self.registerBreastModelToBreast()
      self.align3dViewToRAS()
      self.startDistanceToModel()
      self.setupIntuitiveViewButton.setText('Breast Model Added')
  
  # Show a texture on a model
  def addTextureToModel(self, modelNode, texture): 
    modelDisplayNode=modelNode.GetDisplayNode() 
    textureImageFlipVert=vtk.vtkImageFlip() 
    textureImageFlipVert.SetFilteredAxis(1) 
    textureImageFlipVert.SetInputConnection(texture.GetImageDataConnection()) 
    modelDisplayNode.SetTextureImageDataConnection(textureImageFlipVert.GetOutputPort()) 
    
    logging.info('INFO | BreastModel texturized.')
    
  def startDistanceToModel(self):
    self.distanceToModelLogic.SetMembers(self.tumorModel_Needle, self.needleToReference, self.cauteryTipToCautery, self.cauteryToReference)
    self.distanceToModelLogic.addCalculateDistanceObserver()  
  
  def recordCauteryTipToNeedleTipPoint(self): 
    if not self.cauteryTipToNeedleTip:
      self.cauteryTipToNeedleTip = slicer.util.getNode('CauteryTipToNeedleTi')    
    
    if self.cauteryTipToNeedleTip:
      point = [0,0,0]     
      m = vtk.vtkMatrix4x4()
      self.cauteryTipToNeedleTip.GetMatrixTransformToWorld(m)
      point[0] = m.GetElement(0, 3)
      point[1] = m.GetElement(1, 3)
      point[2] = m.GetElement(2, 3)      
      self.fiducialsFRBL.AddFiducial(point[0], point[1], point[2])      
      
  def align3dViewToRAS(self):   
    logging.debug('align3dViewToRAS')  
    self.fiducialsFRBL.SetAndObserveTransformNodeID(self.needleTipToNeedle.GetID()) 
    
    fiducialsWorldFRBL = slicer.util.getNode('FiducialsWorldFRBL')
    if not fiducialsWorldFRBL:
      # Create a fiducial list containing fiducialsFRBLs world coordinates
      fiducialsWorldFRBL=slicer.vtkMRMLMarkupsFiducialNode()
      fiducialsWorldFRBL.SetName('FiducialsWorldFRBL')
      ras = [0,0,0,1]
      for fiducialIdx in range(self.fiducialsFRBL.GetNumberOfFiducials()):
        self.fiducialsFRBL.GetNthFiducialWorldCoordinates(fiducialIdx, ras)
        fiducialsWorldFRBL.AddFiducial(ras[0], ras[1], ras[2])
      slicer.mrmlScene.AddNode(fiducialsWorldFRBL)
      fiducialsWorldFRBL.SetDisplayVisibility(False)
      
    self.fiducialRegistration(self.fRBLToSLPR, self.fiducialsSLPR, fiducialsWorldFRBL, "Rigid")
    self.setFocalPointByAxes(ctk.ctkAxesWidget.Anterior) 
       
  def registerBreastModelToBreast(self):     
    logging.debug('registerBreastModelToBreast')
    self.breastModel.GetDisplayNode().SetOpacity(0.35)
    self.breastModel.GetDisplayNode().SetBackfaceCulling(True)
    self.breastModel.GetDisplayNode().SetFrontfaceCulling(False)
    self.fiducialRegistration(self.breastModelToBreast, self.fiducialsFRBL, self.fiducialsBreastModel, "Rigid")
    self.breastModel.SetDisplayVisibility(True)

  def setFocalPointRClicked(self):
    self.setFocalPointByAxes(ctk.ctkAxesWidget.Right)
    
  def setFocalPointSClicked(self):
    self.setFocalPointByAxes(ctk.ctkAxesWidget.Superior)
    
  def setFocalPointAClicked(self):
    self.setFocalPointByAxes(ctk.ctkAxesWidget.Anterior)
        
  def setFocalPointByAxes(self, ctkAxes):
    lm=slicer.app.layoutManager() 
    view=lm.threeDWidget(0).threeDView() 
    view.lookFromViewAxis(ctkAxes)
    
    # This is for the case of two available 3D views where we don't know which one gets chosen by view=lm.threeDWidget(0).threeDView() 
    threeDWidget=lm.threeDWidget(1)
    if threeDWidget:
      view = threeDWidget.threeDView() 
      view.lookFromViewAxis(ctkAxes) 
      
###############################################################################
### End LIM stuff     
###############################################################################

  def disconnect(self):#TODO see connect
    logging.debug('LumpNav.disconnect()')
    Guidelet.disconnect(self)
      
    # Remove observer to old parameter node
    if self.tumorMarkups_Needle and self.tumorMarkups_NeedleObserver:
      self.tumorMarkups_Needle.RemoveObserver(self.tumorMarkups_NeedleObserver)
      self.tumorMarkups_NeedleObserver = None

    self.calibrationCollapsibleButton.disconnect('toggled(bool)', self.onCalibrationPanelToggled)
    self.navigationCollapsibleButton.disconnect('toggled(bool)', self.onNavigationPanelToggled)

    self.cauteryPivotButton.disconnect('clicked()', self.onCauteryPivotClicked)
    self.needlePivotButton.disconnect('clicked()', self.onNeedlePivotClicked)
    self.deleteLastFiducialButton.disconnect('clicked()', self.onDeleteLastFiducialClicked)
    self.deleteLastFiducialDuringNavigationButton.disconnect('clicked()', self.onDeleteLastFiducialClicked)    
    self.deleteAllFiducialsButton.disconnect('clicked()', self.onDeleteAllFiducialsClicked)
    self.placeButton.disconnect('clicked(bool)', self.onPlaceClicked)

    #self.rightCameraButton.disconnect('clicked()', self.onRightCameraButtonClicked)
    self.leftCameraButton.disconnect('clicked()', self.onLeftCameraButtonClicked)

    self.setupIntuitiveViewButton.disconnect('clicked()', self.onSetupIntuitiveViewClicked) 
    self.setFocalPointRButton.disconnect('clicked()', self.setFocalPointRClicked)
    self.setFocalPointAButton.disconnect('clicked()', self.setFocalPointAClicked)  
    self.setFocalPointSButton.disconnect('clicked()', self.setFocalPointSClicked)
    
    self.pivotSamplingTimer.disconnect('timeout()',self.onPivotSamplingTimeout)

    self.cameraViewAngleSlider.disconnect('valueChanged(double)', self.viewpointLogic.SetCameraViewAngleDeg)
    self.cameraXPosSlider.disconnect('valueChanged(double)', self.viewpointLogic.SetCameraXPosMm)
    self.cameraYPosSlider.disconnect('valueChanged(double)', self.viewpointLogic.SetCameraYPosMm)
    self.cameraZPosSlider.disconnect('valueChanged(double)', self.viewpointLogic.SetCameraZPosMm)
    
    self.placeTumorPointAtCauteryTipButton.disconnect('clicked(bool)', self.onPlaceTumorPointAtCauteryTipClicked)
    
  def onPivotSamplingTimeout(self):#lumpnav
    self.countdownLabel.setText("Pivot calibrating for {0:.0f} more seconds".format(self.pivotCalibrationStopTime-time.time())) 
    if(time.time()<self.pivotCalibrationStopTime):
      # continue
      self.pivotSamplingTimer.start()
    else:
      # calibration completed
      self.onStopPivotCalibration()

  def startPivotCalibration(self, toolToReferenceTransformName, toolToReferenceTransformNode, toolTipToToolTransformNode):#lumpnav
    self.needlePivotButton.setEnabled(False)
    self.cauteryPivotButton.setEnabled(False)
    self.pivotCalibrationResultTargetNode =  toolTipToToolTransformNode
    self.pivotCalibrationResultTargetName = toolToReferenceTransformName
    self.pivotCalibrationLogic.SetAndObserveTransformNode( toolToReferenceTransformNode );
    self.pivotCalibrationStopTime=time.time()+float(self.parameterNode.GetParameter('PivotCalibrationDurationSec'))
    self.pivotCalibrationLogic.SetRecordingState(True)
    self.onPivotSamplingTimeout()

  def onStopPivotCalibration(self):#lumpnav
    self.pivotCalibrationLogic.SetRecordingState(False)
    self.needlePivotButton.setEnabled(True)
    self.cauteryPivotButton.setEnabled(True)
    self.pivotCalibrationLogic.ComputePivotCalibration()
    if(self.pivotCalibrationLogic.GetPivotRMSE() >= float(self.parameterNode.GetParameter('PivotCalibrationErrorThresholdMm'))):
        self.countdownLabel.setText("Calibration failed, error = %f mm, please calibrate again!"  % self.pivotCalibrationLogic.GetPivotRMSE())
        self.pivotCalibrationLogic.ClearToolToReferenceMatrices()
        return
    tooltipToToolMatrix = vtk.vtkMatrix4x4()
    self.pivotCalibrationLogic.GetToolTipToToolMatrix(tooltipToToolMatrix)
    self.pivotCalibrationLogic.ClearToolToReferenceMatrices()
    self.pivotCalibrationResultTargetNode.SetMatrixTransformToParent(tooltipToToolMatrix)
    self.writeTransformToSettings(self.pivotCalibrationResultTargetName, tooltipToToolMatrix)
    self.countdownLabel.setText("Calibration completed, error = %f mm" % self.pivotCalibrationLogic.GetPivotRMSE())
    logging.debug("Pivot calibration completed. Tool: {0}. RMSE = {1} mm".format(self.pivotCalibrationResultTargetNode.GetName(), self.pivotCalibrationLogic.GetPivotRMSE()))
    self.updatePlusTransform(self.connectorNode.GetID(), self.cauteryTipToCautery)
        
  def onCauteryPivotClicked(self):#lumpnav
    logging.debug('onCauteryPivotClicked')
    self.updatePlusTransform(self.connectorNode.GetID(), self.needleTipToNeedle)
    self.startPivotCalibration('CauteryTipToCautery', self.CauteryToNeedle, self.cauteryTipToCautery)
    
  def onNeedlePivotClicked(self):#lumpnav
    logging.debug('onNeedlePivotClicked')
    self.startPivotCalibration('NeedleTipToNeedle', self.needleToReference, self.needleTipToNeedle)

  def onPlaceClicked(self, pushed):
    logging.debug('onPlaceClicked')
    interactionNode = slicer.app.applicationLogic().GetInteractionNode()
    if pushed:
      # activate placement mode
      selectionNode = slicer.app.applicationLogic().GetSelectionNode()
      selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLMarkupsFiducialNode")
      selectionNode.SetActivePlaceNodeID(self.tumorMarkups_Needle.GetID())
      interactionNode.SetPlaceModePersistence(1)
      interactionNode.SetCurrentInteractionMode(interactionNode.Place)
    else:
      # deactivate placement mode
      interactionNode.SetCurrentInteractionMode(interactionNode.ViewTransform)

  def onDeleteLastFiducialClicked(self):
    numberOfPoints = self.tumorMarkups_Needle.GetNumberOfFiducials()
    self.tumorMarkups_Needle.RemoveMarkup(numberOfPoints-1)
    if numberOfPoints<=1:
        self.deleteLastFiducialButton.setEnabled(False)
        self.deleteAllFiducialsButton.setEnabled(False)
        self.deleteLastFiducialDuringNavigationButton.setEnabled(False)

  def onDeleteAllFiducialsClicked(self):
    self.tumorMarkups_Needle.RemoveAllMarkups()
    self.deleteLastFiducialButton.setEnabled(False)
    self.deleteAllFiducialsButton.setEnabled(False)
    self.deleteLastFiducialDuringNavigationButton.setEnabled(False)
    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetRadius(0.001)
    self.tumorModel_Needle.SetPolyDataConnection(sphereSource.GetOutputPort())      
    self.tumorModel_Needle.Modified()

  def onPlaceTumorPointAtCauteryTipClicked(self):
    cauteryTipToNeedle = vtk.vtkMatrix4x4()
    self.cauteryTipToCautery.GetMatrixTransformToNode(self.needleToReference, cauteryTipToNeedle)
    self.tumorMarkups_Needle.AddFiducial(cauteryTipToNeedle.GetElement(0,3), cauteryTipToNeedle.GetElement(1,3), cauteryTipToNeedle.GetElement(2,3))
      
  def setupCalibrationPanel(self):
    logging.debug('setupCalibrationPanel')

    self.calibrationCollapsibleButton.setProperty('collapsedHeight', 20)
    setButtonStyle(self.calibrationCollapsibleButton, 2.0)
    self.calibrationCollapsibleButton.text = 'Tool calibration'
    self.sliceletPanelLayout.addWidget(self.calibrationCollapsibleButton)

    self.calibrationLayout = qt.QFormLayout(self.calibrationCollapsibleButton)
    self.calibrationLayout.setContentsMargins(12, 4, 4, 4)
    self.calibrationLayout.setSpacing(4)

    self.cauteryPivotButton = qt.QPushButton('Start cautery calibration')
    setButtonStyle(self.cauteryPivotButton)
    self.calibrationLayout.addRow(self.cauteryPivotButton)

    self.needlePivotButton = qt.QPushButton('Start needle calibration')
    setButtonStyle(self.needlePivotButton)
    self.calibrationLayout.addRow(self.needlePivotButton)

    self.countdownLabel = qt.QLabel()
    self.calibrationLayout.addRow(self.countdownLabel)

    self.pivotSamplingTimer = qt.QTimer()
    self.pivotSamplingTimer.setInterval(500)
    self.pivotSamplingTimer.setSingleShot(True)

  def addTumorContouringToUltrasoundPanel(self):

    self.ultrasoundCollapsibleButton.text = "Tumor contouring"

    self.placeButton = qt.QPushButton("Mark points")
    self.placeButton.setCheckable(True)
    self.placeButton.setIcon(qt.QIcon(":/Icons/MarkupsMouseModePlace.png"))
    setButtonStyle(self.placeButton)
    self.ultrasoundLayout.addRow(self.placeButton)

    self.deleteLastFiducialButton = qt.QPushButton("Delete last")
    self.deleteLastFiducialButton.setIcon(qt.QIcon(":/Icons/MarkupsDelete.png"))
    setButtonStyle(self.deleteLastFiducialButton)
    self.deleteLastFiducialButton.setEnabled(False)

    self.deleteAllFiducialsButton = qt.QPushButton("Delete all")
    self.deleteAllFiducialsButton.setIcon(qt.QIcon(":/Icons/MarkupsDeleteAllRows.png"))
    setButtonStyle(self.deleteAllFiducialsButton)
    self.deleteAllFiducialsButton.setEnabled(False)

    hbox = qt.QHBoxLayout()
    hbox.addWidget(self.deleteLastFiducialButton)
    hbox.addWidget(self.deleteAllFiducialsButton)
    self.ultrasoundLayout.addRow(hbox)

  def setupNavigationPanel(self):
    logging.debug('setupNavigationPanel')

    self.sliderTranslationDefaultMm = 0
    self.sliderTranslationMinMm     = -500
    self.sliderTranslationMaxMm     = 500
    self.sliderViewAngleDefaultDeg  = 30
    self.cameraViewAngleMinDeg      = 5.0  # maximum magnification
    self.cameraViewAngleMaxDeg      = 150.0 # minimum magnification
    
    self.sliderSingleStepValue = 1
    self.sliderPageStepValue   = 10

    self.navigationCollapsibleButton.setProperty('collapsedHeight', 20)
    setButtonStyle(self.navigationCollapsibleButton, 2.0)
    self.navigationCollapsibleButton.text = "Navigation"
    self.sliceletPanelLayout.addWidget(self.navigationCollapsibleButton)

    self.navigationCollapsibleLayout = qt.QFormLayout(self.navigationCollapsibleButton)
    self.navigationCollapsibleLayout.setContentsMargins(12, 4, 4, 4)
    self.navigationCollapsibleLayout.setSpacing(4)

    self.setupIntuitiveViewButton = qt.QPushButton('Record Front Position')
    setButtonStyle(self.setupIntuitiveViewButton)
    self.navigationCollapsibleLayout.addRow(self.setupIntuitiveViewButton)
    
    self.leftCameraButton = qt.QPushButton("Setup left camera")
    self.leftCameraButton.setCheckable(True)
    setButtonStyle(self.leftCameraButton)
    self.navigationCollapsibleLayout.addRow(self.leftCameraButton)

    # Select View Direction
    self.rightCameraCollapsibleButton = ctk.ctkCollapsibleGroupBox()
    self.rightCameraCollapsibleButton.collapsed=False
    self.rightCameraCollapsibleButton.title = "Select View Direction"
    self.navigationCollapsibleLayout.addRow(self.rightCameraCollapsibleButton)

    self.rightCameraFormLayout = qt.QFormLayout(self.rightCameraCollapsibleButton)
    
    self.setFocalPointRButton = qt.QPushButton("Right")
    setButtonStyle(self.setFocalPointRButton)
    self.setFocalPointAButton = qt.QPushButton("Anterior")
    setButtonStyle(self.setFocalPointAButton)
    self.setFocalPointSButton = qt.QPushButton("Superior")
    setButtonStyle(self.setFocalPointSButton)
    
    hboxRow = qt.QHBoxLayout()
    hboxRow.addWidget(self.setFocalPointRButton)
    hboxRow.addWidget(self.setFocalPointAButton)
    hboxRow.addWidget(self.setFocalPointSButton)
    
    self.rightCameraFormLayout.addRow(hboxRow)
    
    # "Camera Control" Collapsible
    self.zoomCollapsibleButton = ctk.ctkCollapsibleGroupBox()
    self.zoomCollapsibleButton.collapsed=True
    self.zoomCollapsibleButton.title = "Zoom"
    self.navigationCollapsibleLayout.addRow(self.zoomCollapsibleButton)

    # Layout within the collapsible button
    self.zoomFormLayout = qt.QFormLayout(self.zoomCollapsibleButton)
    
    # Camera distance to focal point slider
    self.cameraViewAngleLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.cameraViewAngleLabel.setText("Field of view [degrees]: ")
    self.cameraViewAngleSlider = slicer.qMRMLSliderWidget()
    self.cameraViewAngleSlider.minimum = self.cameraViewAngleMinDeg
    self.cameraViewAngleSlider.maximum = self.cameraViewAngleMaxDeg
    self.cameraViewAngleSlider.value = self.sliderViewAngleDefaultDeg
    self.cameraViewAngleSlider.singleStep = self.sliderSingleStepValue
    self.cameraViewAngleSlider.pageStep = self.sliderPageStepValue
    self.cameraViewAngleSlider.setDisabled(True)
    self.zoomFormLayout.addRow(self.cameraViewAngleLabel,self.cameraViewAngleSlider)
    
    # "Camera Control" Collapsible
    self.translationCollapsibleButton = ctk.ctkCollapsibleGroupBox()
    self.translationCollapsibleButton.title = "Translation"
    self.translationCollapsibleButton.collapsed=True
    self.navigationCollapsibleLayout.addRow(self.translationCollapsibleButton)

    # Layout within the collapsible button
    self.translationFormLayout = qt.QFormLayout(self.translationCollapsibleButton)        

    self.cameraXPosLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.cameraXPosLabel.text = "Left/Right [mm]: "
    self.cameraXPosSlider = slicer.qMRMLSliderWidget()
    setButtonStyle(self.cameraXPosSlider)
    self.cameraXPosSlider.minimum = self.sliderTranslationMinMm
    self.cameraXPosSlider.maximum = self.sliderTranslationMaxMm
    self.cameraXPosSlider.value = self.sliderTranslationDefaultMm
    self.cameraXPosSlider.singleStep = self.sliderSingleStepValue
    self.cameraXPosSlider.pageStep = self.sliderPageStepValue
    self.cameraXPosSlider.setDisabled(True)
    self.translationFormLayout.addRow(self.cameraXPosLabel,self.cameraXPosSlider)
    
    self.cameraYPosLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.cameraYPosLabel.setText("Down/Up [mm]: ")
    self.cameraYPosSlider = slicer.qMRMLSliderWidget()
    setButtonStyle(self.cameraYPosSlider)
    self.cameraYPosSlider.minimum = self.sliderTranslationMinMm
    self.cameraYPosSlider.maximum = self.sliderTranslationMaxMm
    self.cameraYPosSlider.value = self.sliderTranslationDefaultMm
    self.cameraYPosSlider.singleStep = self.sliderSingleStepValue
    self.cameraYPosSlider.pageStep = self.sliderPageStepValue
    self.cameraYPosSlider.setDisabled(True)
    self.translationFormLayout.addRow(self.cameraYPosLabel,self.cameraYPosSlider)
    
    self.cameraZPosLabel = qt.QLabel(qt.Qt.Horizontal,None)
    self.cameraZPosLabel.setText("Front/Back [mm]: ")
    self.cameraZPosSlider = slicer.qMRMLSliderWidget()
    setButtonStyle(self.cameraZPosSlider)
    self.cameraZPosSlider.minimum = self.sliderTranslationMinMm
    self.cameraZPosSlider.maximum = self.sliderTranslationMaxMm
    self.cameraZPosSlider.value = self.sliderTranslationDefaultMm
    self.cameraZPosSlider.singleStep = self.sliderSingleStepValue
    self.cameraZPosSlider.pageStep = self.sliderPageStepValue
    self.cameraZPosSlider.setDisabled(True)
    self.translationFormLayout.addRow(self.cameraZPosLabel,self.cameraZPosSlider)

    # "Contour adjustment" Collapsible
    self.contourAdjustmentCollapsibleButton = ctk.ctkCollapsibleGroupBox()
    self.contourAdjustmentCollapsibleButton.title = "Contour adjustment"
    self.contourAdjustmentCollapsibleButton.collapsed=True
    self.navigationCollapsibleLayout.addRow(self.contourAdjustmentCollapsibleButton)

    # Layout within the collapsible button
    self.contourAdjustmentFormLayout = qt.QFormLayout(self.contourAdjustmentCollapsibleButton)

    self.placeTumorPointAtCauteryTipButton = qt.QPushButton("Mark point at cautery tip")
    setButtonStyle(self.placeTumorPointAtCauteryTipButton)
    self.contourAdjustmentFormLayout.addRow(self.placeTumorPointAtCauteryTipButton)
    
    self.deleteLastFiducialDuringNavigationButton = qt.QPushButton("Delete last")
    self.deleteLastFiducialDuringNavigationButton.setIcon(qt.QIcon(":/Icons/MarkupsDelete.png"))
    setButtonStyle(self.deleteLastFiducialDuringNavigationButton)
    self.deleteLastFiducialDuringNavigationButton.setEnabled(False)
    self.contourAdjustmentFormLayout.addRow(self.deleteLastFiducialDuringNavigationButton)

  def onCalibrationPanelToggled(self, toggled):
    if toggled == False:
      return

    logging.debug('onCalibrationPanelToggled: {0}'.format(toggled))
    
    self.onViewSelect(self.viewUltrasound3d) 

  def onUltrasoundPanelToggled(self, toggled):
    Guidelet.onUltrasoundPanelToggled(self, toggled)
    
    if self.tumorMarkups_Needle:
        self.tumorMarkups_Needle.SetDisplayVisibility(1)
  
  def createTumorFromMarkups(self):
    logging.debug('createTumorFromMarkups')
    #self.tumorMarkups_Needle.SetDisplayVisibility(0)
    
    # Create polydata point set from markup points
    points = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()
    
    numberOfPoints = self.tumorMarkups_Needle.GetNumberOfFiducials()

    if numberOfPoints>0:
        self.deleteLastFiducialButton.setEnabled(True)
        self.deleteAllFiducialsButton.setEnabled(True)
        self.deleteLastFiducialDuringNavigationButton.setEnabled(True)
    
    # Surface generation algorithms behave unpredictably when there are not enough points
    # return if there are very few points
    if numberOfPoints<1:
      return

    points.SetNumberOfPoints(numberOfPoints)
    new_coord = [0.0, 0.0, 0.0]

    for i in range(numberOfPoints):
      self.tumorMarkups_Needle.GetNthFiducialPosition(i,new_coord)
      points.SetPoint(i, new_coord)

    cellArray.InsertNextCell(numberOfPoints)
    for i in range(numberOfPoints):
      cellArray.InsertCellPoint(i)

    pointPolyData = vtk.vtkPolyData()
    pointPolyData.SetLines(cellArray)
    pointPolyData.SetPoints(points)
    
    delaunay = vtk.vtkDelaunay3D()

    if numberOfPoints<10:
      logging.debug("use glyphs")
      sphere = vtk.vtkCubeSource()
      glyph = vtk.vtkGlyph3D()
      glyph.SetInputData(pointPolyData)
      glyph.SetSourceConnection(sphere.GetOutputPort())
      #glyph.SetVectorModeToUseNormal()
      #glyph.SetScaleModeToScaleByVector()
      #glyph.SetScaleFactor(0.25)
      delaunay.SetInputConnection(glyph.GetOutputPort())
    else:
      delaunay.SetInputData(pointPolyData)

    surfaceFilter = vtk.vtkDataSetSurfaceFilter()
    surfaceFilter.SetInputConnection(delaunay.GetOutputPort())

    smoother = vtk.vtkButterflySubdivisionFilter()
    smoother.SetInputConnection(surfaceFilter.GetOutputPort())
    smoother.SetNumberOfSubdivisions(3)
    smoother.Update()
    
    forceConvexShape = True

    if (forceConvexShape == True):
        delaunaySmooth = vtk.vtkDelaunay3D()
        delaunaySmooth.SetInputData(smoother.GetOutput())
        delaunaySmooth.Update()
    
        smoothSurfaceFilter = vtk.vtkDataSetSurfaceFilter()
        smoothSurfaceFilter.SetInputConnection(delaunaySmooth.GetOutputPort())
        self.tumorModel_Needle.SetPolyDataConnection(smoothSurfaceFilter.GetOutputPort())
    else:
        self.tumorModel_Needle.SetPolyDataConnection(smoother.GetOutputPort())
    
    self.tumorModel_Needle.Modified()

  def setupViewpoint(self):
    rightView = slicer.util.getNode("view2")
    self.RightCamera.SetActiveTag(rightView.GetID())
    leftView = slicer.util.getNode("view1")
    self.LeftCamera.SetActiveTag(leftView.GetID())

  def setDisableSliders(self, disable):
    self.cameraViewAngleSlider.setDisabled(disable)
    self.cameraXPosSlider.setDisabled(disable)
    self.cameraZPosSlider.setDisabled(disable)
    self.cameraYPosSlider.setDisabled(disable)

  def onRightCameraButtonClicked(self):
    logging.debug("onRightCameraButtonClicked {0}".format(self.rightCameraButton.isChecked()))
    if (self.rightCameraButton.isChecked()== True):
        self.leftCameraButton.setDisabled(True)
        self.viewpointLogic.setCameraNode(self.RightCamera)
        self.viewpointLogic.setTransformNode(self.cauteryCameraToCautery)
        self.viewpointLogic.startViewpoint()
        self.setDisableSliders(False)
    else:
        self.setDisableSliders(True)
        self.viewpointLogic.stopViewpoint()
        self.leftCameraButton.setDisabled(False)

  def onLeftCameraButtonClicked(self):
    logging.debug("onLeftCameraButtonClicked {0}".format(self.leftCameraButton.isChecked()))
    if (self.leftCameraButton.isChecked() == True):
      self.viewpointLogic.setCameraNode(self.LeftCamera)
      self.viewpointLogic.setTransformNode(self.cauteryCameraToCautery)
      self.viewpointLogic.startViewpoint()
      #self.rightCameraButton.setDisabled(True)
      self.setDisableSliders(False)
    else:
      self.setDisableSliders(True)
      self.viewpointLogic.stopViewpoint()
      #self.rightCameraButton.setDisabled(False)

  def onNavigationPanelToggled(self, toggled):
    if toggled == False:
      return

    logging.debug('onNavigationPanelToggled')
    self.onViewSelect(self.viewDual3d)
    self.tumorMarkups_Needle.SetDisplayVisibility(0)
    self.setupViewpoint()

    ## Stop live ultrasound.
    #if self.connectorNode != None:
    #  self.connectorNode.Stop()

  def onTumorMarkupsNodeModified(self, observer, eventid):
    self.createTumorFromMarkups()

  def setAndObserveTumorMarkupsNode(self, tumorMarkups_Needle):
    if tumorMarkups_Needle == self.tumorMarkups_Needle and self.tumorMarkups_NeedleObserver:
      # no change and node is already observed
      return
    # Remove observer to old parameter node
    if self.tumorMarkups_Needle and self.tumorMarkups_NeedleObserver:
      self.tumorMarkups_Needle.RemoveObserver(self.tumorMarkups_NeedleObserver)
      self.tumorMarkups_NeedleObserver = None
    # Set and observe new parameter node
    self.tumorMarkups_Needle = tumorMarkups_Needle
    if self.tumorMarkups_Needle:
      self.tumorMarkups_NeedleObserver = self.tumorMarkups_Needle.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onTumorMarkupsNodeModified)
     