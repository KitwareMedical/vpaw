import importlib
import logging
import os
import pathlib
import qt
import slicer
import slicer.ScriptedLoadableModule
import slicer.util
import sys
import time
import vtk


class BusyCursor:
    """Context manager for showing a busy cursor. Ensures that cursor reverts to normal in case of an exception."""

    def __enter__(self):
        qt.QApplication.setOverrideCursor(qt.Qt.BusyCursor)

    def __exit__(self, exception_type, exception_value, traceback):
        qt.QApplication.restoreOverrideCursor()
        return False


#
# VPAWModel
#


class VPAWModel(slicer.ScriptedLoadableModule.ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        slicer.ScriptedLoadableModule.ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "VPAW Model"
        self.parent.categories = ["VPAW"]
        self.parent.dependencies = (
            []
        )  # TODO: add here list of module names that this module requires
        self.parent.contributors = [
            "Andinet Enquobahrie (Kitware, Inc.)",
            "Shreeraj Jadhav (Kitware, Inc.)",
            "Jean-Christophe Fillion-Robin (Kitware, Inc.)",
            "Ebrahim Ebrahim (Kitware, Inc.)",
            "Lee Newberg (Kitware, Inc.)",
        ]
        # TODO: update with short description of the module and a link to online module
        # documentation
        self.parent.helpText = """
This is the scripted loadable module named VPAW Model.  See more information in
<a href="https://github.com/KitwareMedical/vpaw#VPAWModel">module documentation</a>.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was built from template originally developed by Jean-Christophe Fillion-Robin,
Kitware Inc., Andras Lasso, PerkLab, and Steve Pieper, Isomics, Inc. and was partially
funded by NIH grant 3P41RR013218-12S1.
"""
        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """
    Add data sets to Sample Data module.
    """
    # It is always recommended to provide sample data for users to make it easy to try
    # the module, but if no sample data is available then this method (and associated
    # startupCompeted signal connection) can be removed.

    pass


#
# VPAWModelWidget
#


class VPAWModelWidget(
    slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget,
    slicer.util.VTKObservationMixin,
):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is
        initialized.
        """
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.__init__(
            self, parent
        )
        # needed for parameter node observation:
        slicer.util.VTKObservationMixin.__init__(self)
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is
        initialized.
        """
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/VPAWModel.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level
        # qMRMLWidget's "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each
        # MRML widget's.  "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Configure 3D view
        viewNode = slicer.app.layoutManager().threeDWidget(0).mrmlViewNode()
        viewNode.SetBackgroundColor(0, 0, 0)
        viewNode.SetBackgroundColor2(0, 0, 0)
        viewNode.SetAxisLabelsVisible(False)
        viewNode.SetBoxVisible(False)
        viewNode.SetOrientationMarkerType(
            slicer.vtkMRMLAbstractViewNode.OrientationMarkerTypeAxes
        )

        # Create logic class. Logic implements all computations that should be possible
        # to run in batch mode, without a graphical user interface.
        self.logic = VPAWModelLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(
            slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose
        )
        self.addObserver(
            slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose
        )

        # These connections ensure that whenever user changes some settings on the GUI,
        # that is saved in the MRML scene (in the selected parameter node).
        self.ui.PediatricAirwayAtlasDirectory.connect(
            "currentPathChanged(const QString&)", self.updateParameterNodeFromGUI
        )
        self.ui.VPAWRootDirectory.connect(
            "currentPathChanged(const QString&)", self.updateParameterNodeFromGUI
        )
        self.ui.PAAConfigFile.connect(
            "currentPathChanged(const QString&)", self.updateParameterNodeFromGUI
        )
        self.ui.PAASegmentationConfigFile.connect(
            "currentPathChanged(const QString&)", self.updateParameterNodeFromGUI
        )

        # Buttons
        self.ui.VPAWVisualizeButton.connect("clicked(bool)", self.onVPAWVisualizeButton)
        self.ui.HomeButton.connect("clicked(bool)", self.onHomeButton)
        self.ui.installPediatricAirwayAtlasButton.connect(
            "clicked(bool)", self.onInstallPediatricAirwayAtlasButton
        )
        self.ui.runPediatricAirwayAtlasButton.connect(
            "clicked(bool)", self.onRunPediatricAirwayAtlasButton
        )

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

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
        # Do not react to parameter node changes (GUI wlil be updated when the user
        # enters into the module)
        self.removeObserver(
            self._parameterNode,
            vtk.vtkCommand.ModifiedEvent,
            self.updateGUIFromParameterNode,
        )

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
        # If this module is shown while the scene is closed then recreate a new
        # parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections,
        # etc.  so that when the scene is saved and reloaded, these settings are
        # restored.

        self.setParameterNode(self.logic.getParameterNode())

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.  Observation is needed because when the
        parameter node is changed then the GUI must be updated immediately.
        """
        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly
        # selected.  Changes of parameter node are observed so that whenever parameters
        # are changed by a script or any other module those are reflected immediately in
        # the GUI.
        if self._parameterNode is not None and self.hasObserver(
            self._parameterNode,
            vtk.vtkCommand.ModifiedEvent,
            self.updateGUIFromParameterNode,
        ):
            self.removeObserver(
                self._parameterNode,
                vtk.vtkCommand.ModifiedEvent,
                self.updateGUIFromParameterNode,
            )
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(
                self._parameterNode,
                vtk.vtkCommand.ModifiedEvent,
                self.updateGUIFromParameterNode,
            )

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.  The module GUI is
        updated to show the current state of the parameter node.
        """
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause
        # infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.PediatricAirwayAtlasDirectory.currentPath = (
            self._parameterNode.GetParameter("PediatricAirwayAtlasDirectory")
        )
        self.ui.VPAWRootDirectory.currentPath = self._parameterNode.GetParameter(
            "VPAWRootDirectory"
        )
        self.ui.PAAConfigFile.currentPath = self._parameterNode.GetParameter(
            "PAAConfigFile"
        )
        self.ui.PAASegmentationConfigFile.currentPath = (
            self._parameterNode.GetParameter("PAASegmentationConfigFile")
        )

        # Update buttons states and tooltips
        if os.path.isdir(self.ui.PediatricAirwayAtlasDirectory.currentPath):
            self.ui.installPediatricAirwayAtlasButton.toolTip = (
                "Install Pediatric Airway Atlas and Dependencies"
            )
            self.ui.installPediatricAirwayAtlasButton.enabled = True
        else:
            self.ui.installPediatricAirwayAtlasButton.toolTip = (
                "Install is disabled;"
                + " first select a valid source code directory for the Pediatric Airway Atlas"
            )
            self.ui.installPediatricAirwayAtlasButton.enabled = True
        if (
            os.path.isdir(self.ui.VPAWRootDirectory.currentPath)
            and os.path.isfile(self.ui.PAAConfigFile.currentPath)
            and os.path.isfile(self.ui.PAASegmentationConfigFile.currentPath)
        ):
            self.ui.runPediatricAirwayAtlasButton.toolTip = "Run Pediatric Airway Atlas"
            self.ui.runPediatricAirwayAtlasButton.enabled = True
        else:
            self.ui.runPediatricAirwayAtlasButton.toolTip = (
                "Run is disabled;"
                + " first select input/output root directory and both configuration files"
            )
            self.ui.runPediatricAirwayAtlasButton.enabled = False

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.  The changes
        are saved into the parameter node (so that they are restored when the scene is
        saved and loaded).
        """
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = (
            self._parameterNode.StartModify()
        )  # Modify all properties in a single batch

        self._parameterNode.SetParameter(
            "PediatricAirwayAtlasDirectory",
            self.ui.PediatricAirwayAtlasDirectory.currentPath,
        )
        self._parameterNode.SetParameter(
            "VPAWRootDirectory", self.ui.VPAWRootDirectory.currentPath
        )
        self._parameterNode.SetParameter(
            "PAAConfigFile", self.ui.PAAConfigFile.currentPath
        )
        self._parameterNode.SetParameter(
            "PAASegmentationConfigFile", self.ui.PAASegmentationConfigFile.currentPath
        )

        self._parameterNode.EndModify(wasModified)

    def onHomeButton(self):
        """
        Switch to the "Home" module when the user clicks the button.
        """
        slicer.util.selectModule("Home")

    def onVPAWVisualizeButton(self):
        """
        Switch to the "VPAW Visualize" module when the user clicks the button.
        """
        slicer.util.selectModule("VPAWVisualize")

    def onInstallPediatricAirwayAtlasButton(self):
        """
        Install the Pediatric Airway Atlas source code and its dependencies at the
        user's request.
        """
        with slicer.util.tryWithErrorDisplay(
            "Failed to compute results.", waitCursor=True
        ):
            self.logic.installPediatricAirwayAtlas(
                self.ui.PediatricAirwayAtlasDirectory.currentPath
            )

    def onRunPediatricAirwayAtlasButton(self):
        """
        Using the supplied
            VPAWRootDirectory :
                input/output directory (e.g., "path/to/vpaw-data-root"),
            PAAConfigFile :
                config file (e.g., "configs/config_large_dataset_large_train.yaml")
            PAASegmentationConfigFile :
                segmentation config file (e.g.,
                "segmentation/segmentation_settings_largetrain_step_2.yaml")
        run the Pediatric Airway Atlas pipeline at the user's request.
        """
        with slicer.util.tryWithErrorDisplay(
            "Failed to compute results.", waitCursor=True
        ):
            self.logic.runPediatricAirwayAtlas(
                self.ui.VPAWRootDirectory.currentPath,
                self.ui.PAAConfigFile.currentPath,
                self.ui.PAASegmentationConfigFile.currentPath,
            )


#
# VPAWModelLogic
#


class VPAWModelLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member
        variables.
        """
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic.__init__(self)
        # self.python_dependencies should instead be handled as something like a
        # requirements.txt file for pediatric_airway_atlas.  Because it isn't,
        # self.python_dependencies is a sequence of pairs.  For each pair the first
        # entry is a name that is used with Python `import`.  The second is a name that
        # is used with Python `pip install`, and can include version information.
        self.python_dependencies = (
            ("itk", "itk"),
            ("matplotlib", "matplotlib"),
            ("monai", "monai"),
            ("numpy", "numpy"),
            ("pandas", "pandas"),
            ("ruffus", "ruffus"),
            ("shapely", "shapely"),
            ("SimpleITK", "SimpleITK"),
            ("skimage", "scikit-image"),
            ("tensorboard", "tensorboard"),
            ("torchvision", "torchvision"),
            ("tqdm", "tqdm"),
            ("trimesh", "trimesh"),
            ("vtk", "vtk"),
            ("yaml", "pyyaml"),
        )

    def installPediatricAirwayAtlas(self, pediatricAirwayAtlasDirectory):
        startTime = time.time()
        logging.info("Pediatric Airway Atlas installation started")

        if self.installAndImportDependencies() and self.ensureModulePath(
            pediatricAirwayAtlasDirectory
        ):
            # No error messages have been sent to the user, so let's be friendly
            slicer.util.infoDisplay("Pediatric Airway Atlas is installed", "Installed")

        stopTime = time.time()
        logging.info(
            "Pediatric Airway Atlas installation completed"
            + f" in {stopTime-startTime:.2f} seconds"
        )

    def ensureModulePath(self, directory):
        directory = str(pathlib.Path(directory))
        if directory not in sys.path:
            sys.path.insert(0, directory)
            importlib.invalidate_caches()
        try:
            for module_name in (
                "conversion_utils.generate_pixel_space_landmarks",
                "atlas_builder_configurable",
            ):
                imported = importlib.import_module(module_name)
        except:
            slicer.util.errorDisplay(
                f"Unable to find pediatric_airway_atlas/{module_name}\n"
                + "Check the console for details.",
                "Install Error",
            )
            return False
        return True

    def showInstalledModules(self, installed_modules):
        if installed_modules:
            plural = "" if len(installed_modules) == 1 else "s"
            version_text = "\n".join(
                [
                    f"    {module_name} version: {module.__version__}"
                    if hasattr(module, "__version__")
                    else f"    {module_name} version: unknown"
                    for module_name, module in installed_modules.items()
                ]
            )
            slicer.util.infoDisplay(
                "Module{plural} installed:\n" + version_text,
                f"Module{plural} Installed",
            )

    def installAndImportDependencies(self):
        needs_installation = []
        for module_name, pip_install_name in self.python_dependencies:
            try:
                importlib.import_module(module_name)
            except ModuleNotFoundError as e1:
                needs_installation.append((module_name, pip_install_name))
        installed_modules = {}
        if needs_installation:
            plural = "" if len(needs_installation) == 1 else "s"
            want_install = slicer.util.confirmYesNoDisplay(
                f"Package{plural} not found: "
                + ", ".join([module_name for module_name, _ in needs_installation])
                + f"\nInstall the package{plural}?  (This may take a while)",
                "Missing Dependencies" if plural == "s" else "Missing Dependency"
            )
            if not want_install:
                mesg = f"Package{plural} installation declined; giving up."
                slicer.util.errorDisplay(mesg, "Install Error")
                print(mesg)
                return False
            try:
                # Install missing packages
                with BusyCursor():
                    slicer.util.pip_install(["-U", "pip", "setuptools", "wheel"])
                    slicer.util.pip_install(
                        [pip_install_name for _, pip_install_name in needs_installation]
                    )
                    installed_modules = {
                        module_name: importlib.import_module(module_name)
                        for module_name, _ in needs_installation
                    }
            except ModuleNotFoundError as e2:
                slicer.util.errorDisplay(
                    "\n".join(
                        [
                            f"Unable to install package{plural}.",
                            "Check the console for details.",
                        ]
                    ),
                    "Install Error",
                )
                print(e2)
                return False

        # All dependencies were successfully imported
        self.showInstalledModules(installed_modules)
        return True

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        pass

    def runPediatricAirwayAtlas(
        self, vPAWRootDirectory, pAAConfigFile, pAASegmentationConfigFile
    ):
        """
        Run the Pediatric Airway Atlas pipeline.
        Can be used without GUI widget.

        Parameters
        ----------
        vPAWRootDirectory : str
            input/output directory (e.g., "path/to/vpaw-data-root"),
        pAAConfigFile : str
            config file (e.g., "configs/config_large_dataset_large_train.yaml")
        pAASegmentationConfigFile : str
            segmentation config file (e.g.,
            "segmentation/segmentation_settings_largetrain_step_2.yaml")
        """
        startTime = time.time()
        logging.info("Pediatric Airway Atlas pipeline started")

        # self.convertCTScansToNRRD(vPAWRootDirectory)
        self.convertFCSVLandmarksToP3(vPAWRootDirectory)
        self.runSegmentation(pAAConfigFile, pAASegmentationConfigFile)

        stopTime = time.time()
        logging.info(
            f"Pediatric Airway Atlas pipeline completed in {stopTime-startTime:.2f} seconds"
        )

    def convertFCSVLandmarksToP3(self, vPAWRootDirectory):
        import conversion_utils.generate_pixel_space_landmarks

        conversion_utils.generate_pixel_space_landmarks.convert_landmarks(
            os.path.join(vPAWRootDirectory, "images"),
            os.path.join(vPAWRootDirectory, "landmarks"),
            os.path.join(vPAWRootDirectory, "transformed_landmarks"),
        )

    def runSegmentation(self, pAAConfigFile, pAASegmentationConfigFile):
        import atlas_builder_configurable

        atlas_builder_configurable.atlas_builder_configurable(
            pAAConfigFile, pAASegmentationConfigFile
        )


#
# VPAWModelTest
#


class VPAWModelTest(slicer.ScriptedLoadableModule.ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be
        enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_VPAWModel1()

    def test_VPAWModel1(self):
        """
        Ideally we should have several levels of tests.  At the lowest level tests
        should exercise the functionality of the logic with different inputs (both valid
        and invalid).  At higher levels our tests should emulate the way the user would
        interact with our code and confirm that it still works the way we intended.

        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of our module.
        For example, if a developer removes a feature that we depend on, our test should
        break so they know that the feature is needed.
        """
        self.delayDisplay("Starting the test")

        # Get/create input data

        self.delayDisplay("Test skipped")
