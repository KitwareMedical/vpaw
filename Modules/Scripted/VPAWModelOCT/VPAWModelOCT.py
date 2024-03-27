import importlib
import logging
import os
import pathlib
import sys
import time

import qt
import slicer
import slicer.ScriptedLoadableModule
import slicer.util


class BusyCursor:
    """
    Context manager for showing a busy cursor.  Ensures that cursor reverts to normal in
    case of an exception.
    """

    def __enter__(self):
        qt.QApplication.setOverrideCursor(qt.Qt.BusyCursor)

    def __exit__(self, exception_type, exception_value, traceback):
        qt.QApplication.restoreOverrideCursor()
        return False


#
# VPAWModelOCT
#


class VPAWModelOCT(slicer.ScriptedLoadableModule.ScriptedLoadableModule):
    """
    Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        slicer.ScriptedLoadableModule.ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "VPAW Model OCT"
        self.parent.categories = ["VPAW"]
        # TODO: add here list of module names that this module requires
        self.parent.dependencies = []
        self.parent.contributors = [
            "Lee Newberg (Kitware, Inc.)",
            "Ebrahim Ebrahim (Kitware, Inc.)",
            "Andinet Enquobahrie (Kitware, Inc.)",
        ]
        # TODO: update with short description of the module and a link to online module
        # documentation
        self.parent.helpText = """
This is the scripted loadable module named VPAW Model OCT.  See more information in
<a href="https://github.com/KitwareMedical/vpaw#VPAWModelOCT">module documentation</a>.
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
# VPAWModelOCTWidget
#


class VPAWModelOCTWidget(
    slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget,
    slicer.util.VTKObservationMixin,
):
    """
    Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is
        initialized.
        """
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.__init__(
            self, parent,
        )
        slicer.util.VTKObservationMixin.__init__(self)

        self.logic = None
        self._updatingGUIFromQSettings = False

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is
        initialized.
        """
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/VPAWModelOCT.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets.  Make sure that in Qt designer the top-level
        # qMRMLWidget's "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each
        # MRML widget's "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Configure 3D view
        viewNode = slicer.app.layoutManager().threeDWidget(0).mrmlViewNode()
        viewNode.SetBackgroundColor(0, 0, 0)
        viewNode.SetBackgroundColor2(0, 0, 0)
        viewNode.SetAxisLabelsVisible(False)
        viewNode.SetBoxVisible(False)
        viewNode.SetOrientationMarkerType(
            slicer.vtkMRMLAbstractViewNode.OrientationMarkerTypeAxes,
        )

        # Create logic class.  Logic implements all computations that should be possible
        # to run in batch mode, without a graphical user interface.
        self.logic = VPAWModelOCTLogic()

        # Connections

        # Connections for actions associated with a scene close.
        self.addObserver(
            slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose,
        )
        self.addObserver(
            slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose,
        )

        # These connections ensure that whenever user changes some settings on the GUI,
        # that is saved to QSettings.
        self.ui.OCTSegDirectory.connect(
            "currentPathChanged(const QString&)", self.updateQSettingsFromGUI,
        )
        self.ui.VPAWOCTConfigFile.connect(
            "currentPathChanged(const QString&)", self.updateQSettingsFromGUI,
        )
        self.ui.OCTSegDirectory.connect(
            "validInputChanged(bool)", self.updateQSettingsFromGUI,
        )
        self.ui.VPAWOCTConfigFile.connect(
            "validInputChanged(bool)", self.updateQSettingsFromGUI,
        )

        # Buttons
        self.ui.VPAWModelButton.connect("clicked(bool)", self.onVPAWModelButton)
        self.ui.VPAWVisualizeButton.connect("clicked(bool)", self.onVPAWVisualizeButton)
        self.ui.HomeButton.connect("clicked(bool)", self.onHomeButton)
        self.ui.VPAWVisualizeOCTButton.connect(
            "clicked(bool)", self.onVPAWVisualizeOCTButton,
        )

        self.ui.linkOCTSegButton.connect("clicked(bool)", self.onLinkOCTSegButton)
        self.ui.runOCTSegButton.connect("clicked(bool)", self.onRunOCTSegButton)

        # No need to call self.updateGUIFromQSettings() because it will be called upon
        # self.enter().

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Initialize the GUI with any saved settings
        self.updateGUIFromQSettings()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        pass

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        pass

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        pass

    def updateGUIFromQSettings(self):
        """
        Load GUI with values from QSettings.
        """
        # Let everyone know that we are updating the GUI so that any reactions to that
        # don't get into an infinite loop.
        self._updatingGUIFromQSettings = True

        # Update node selectors and sliders
        qsettings = qt.QSettings()
        qsettings.beginGroup("VPAWModelOCT")
        self.ui.OCTSegDirectory.currentPath = qsettings.value("OCTSegDirectory", "")
        self.ui.VPAWOCTConfigFile.currentPath = qsettings.value("VPAWOCTConfigFile", "")
        qsettings.endGroup()

        # Now that we've updated the form widgets' input fields, let's update other
        # widgets and other properties.
        self.updateButtonStatesAndTooltips()

        # All the GUI updates are done
        self._updatingGUIFromQSettings = False

    def updateButtonStatesAndTooltips(self):
        self.ui.OCTSegDirectory.toolTip = "Root directory for OCTSeg source code"
        if os.path.isdir(self.ui.OCTSegDirectory.currentPath):
            self.ui.linkOCTSegButton.toolTip = (
                "Link to OCT Segmentation codebase and install dependencies"
            )
            self.ui.linkOCTSegButton.enabled = True
        else:
            self.ui.linkOCTSegButton.toolTip = (
                "Install is disabled; first select a valid source code directory for"
                + " the OCT Segmentation"
            )
            self.ui.linkOCTSegButton.enabled = False

        self.ui.VPAWOCTConfigFile.toolTip = (
            " Location of the configuration file, such as unet_v2_test_1_channel.yaml."
            " Within the file, be sure that"
            " `disk`,"
            " `data_root`,"
            " `path_img` (disk+data_root+path_img is the location of the OCT scans),"
            " `path_gt_seg` (disk+data_root+path_gt_seg is the location of groundtruth"
            " segmentations for testing, can be none),"
            " `path_my_seg` (disk+data_root+path_gt_seg is the location of"
            " segmentations for training, can be none),"
            " `path_my_uncertainty` (disk+data_root+path_gt_seg is the location of"
            " uncertainty maps, can be none),"
            " `filename_dataset` (full path name for file like oct_real_datasets.xlsx),"
            " `filename_split` (full path name for file like split_real.xlsx), and"
            " `model_path` (disk+model_path is the location where model parameters and"
            " testing results are saved)"
            " are set for your local configuration."
        )
        if os.path.isfile(self.ui.VPAWOCTConfigFile.currentPath) and os.access(
            self.ui.VPAWOCTConfigFile.currentPath, os.R_OK,
        ):
            self.ui.runOCTSegButton.toolTip = "Run OCT Segmentation"
            self.ui.runOCTSegButton.enabled = True
        else:
            self.ui.runOCTSegButton.toolTip = (
                "Run is disabled; first select a readable YAML configuration file"
            )
            self.ui.runOCTSegButton.enabled = False

    def setOrRemoveQSetting(self, qsettings, key, value):
        # We can keep the operating system's "registry" cleaner by removing the key
        # entirely when its value is None or "".
        if value is not None and value != "":
            qsettings.setValue(key, value)
        else:
            qsettings.remove(key)

    def updateQSettingsFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.  The changes
        are saved into the QSettomgs (so that they are restored when the application is
        restarted).
        """
        # If we got called to update QSettings because we updated the GUI from QSettings
        # then there's nothing more to do.  (Infinite loops are a drag.)
        if self._updatingGUIFromQSettings:
            return

        qsettings = qt.QSettings()
        qsettings.beginGroup("VPAWModelOCT")
        self.setOrRemoveQSetting(
            qsettings, "OCTSegDirectory", self.ui.OCTSegDirectory.currentPath,
        )
        self.setOrRemoveQSetting(
            qsettings, "VPAWOCTConfigFile", self.ui.VPAWOCTConfigFile.currentPath,
        )
        qsettings.endGroup()

        # Because the widgets' form inputs have changed, we should update other widgets
        # and properties too.
        self._updatingGUIFromQSettings = True
        self.updateButtonStatesAndTooltips()
        self._updatingGUIFromQSettings = False

    def onHomeButton(self):
        """
        Switch to the "Home" module when the user clicks the button.
        """
        slicer.util.selectModule("Home")

    def onVPAWModelButton(self):
        """
        Switch to the "VPAW Model" module when the user clicks the button.
        """
        slicer.util.selectModule("VPAWModel")

    def onVPAWVisualizeButton(self):
        """
        Switch to the "VPAW Visualize" module when the user clicks the button.
        """
        slicer.util.selectModule("VPAWVisualize")

    def onVPAWVisualizeOCTButton(self):
        """
        Switch to the "VPAW Visualize OCT" module when the user clicks the button.
        """
        slicer.util.selectModule("VPAWVisualizeOCT")

    def onLinkOCTSegButton(self):
        """
        Install the OCT Segmentation source code and its dependencies at the
        user's request.
        """
        with slicer.util.tryWithErrorDisplay(
            "Failed to compute results.", waitCursor=True,
        ):
            self.logic.linkOCTSeg(self.ui.OCTSegDirectory.currentPath)

    def onRunOCTSegButton(self):
        """
        Parameters
        ----------
        OCTSegDirectory :
            This is the directory containing the source code for OCTSeg.
        VPAWOCTConfigFile :
            This is the full path name to a top-level configuration file such as
            uncbiag/OCTSeg/configs/unet_v2/unet_v2_test_1_channel.yaml.

        Run the OCT Segmentation pipeline at the user's request.
        """
        with slicer.util.tryWithErrorDisplay(
            "Failed to compute results.", waitCursor=True,
        ):
            self.logic.runOCTSeg(
                self.ui.OCTSegDirectory.currentPath,
                self.ui.VPAWOCTConfigFile.currentPath,
            )


#
# VPAWModelOCTLogic
#


class VPAWModelOCTLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):
    """
    This class should implement all the actual computation done by your module.  The
    interface should be such that other python code can import this class and make use
    of the functionality without requiring an instance of the Widget.  Uses
    ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated.  Can be used for initializing
        member variables.
        """
        slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic.__init__(self)

        # self.python_dependencies should instead be handled as something like a
        # requirements.txt file for OCTSeg.  Because it isn't,
        # self.python_dependencies is a sequence of pairs.  For each pair the first
        # entry is a name that is used with Python `import`.  The second is a name that
        # is used with Python `pip install`, and can include version information.

        self.python_dependencies = (
            ("albumentations", "albumentations"),
            ("blosc", "blosc"),
            ("cv2", "opencv-python"),
            ("imgviz", "imgviz"),
            ("matplotlib", "matplotlib"),
            ("numpy", "numpy"),
            ("openpyxl", "openpyxl"),
            ("pandas", "pandas"),
            ("PIL", "Pillow"),
            ("progressbar", "progressbar"),
            ("scipy", "scipy"),
            ("seaborn", "seaborn"),
            ("skimage", "scikit-image"),
            ("sklearn", "scikit-learn"),
            ("tensorboard", "tensorboard"),
            ("torch", "torch"),
            ("torchvision", "torchvision"),
            ("tqdm", "tqdm"),
            ("yaml", "PyYAML"),
        )

    def setDefaultParameters(self, parameterNode):
        """
        Initialize with default settings.
        """
        pass

    def linkOCTSeg(self, octSegDirectory):
        startTime = time.time()
        logging.info("OCT Segmentation installation started")

        response = self.installAndImportDependencies() and self.ensureModulePath(
            octSegDirectory,
        )

        if response:
            # No error messages have been sent to the user, so let's assure the user
            # that something useful has happened.
            slicer.util.infoDisplay("OCT Segmentation is linked", "Linked")

        stopTime = time.time()
        logging.info(
            f"OCT Segmentation installation completed in {stopTime-startTime:.2f}"
            + " seconds",
        )
        return response

    def ensureModulePath(self, directory):
        self.OCTSeg_directory = str(pathlib.Path(directory))
        if self.OCTSeg_directory not in sys.path:
            sys.path.insert(0, self.OCTSeg_directory)
            importlib.invalidate_caches()
        try:
            # If some of these modules are deprecated / removed in future
            # implementations, they can safely be removed from this checklist.  Ideally,
            # this list should contain only permanent, public API, e.g., as accessed by
            # test_base.py
            for import_name in (
                # "dataset.OCTDataset",
                "dataset.RealOCTBaseDataset",
                # "unet.unet_base",
                "unet.unet_cumsum",
                "unet.unet_dist",
                "unet.unet_dist_detach",
                "unet.unet_grad_cumsum",
                # "unet.unet_model",
                # "unet.unet_multi_cumsum",
                # "unet.unet_multi_res",
                # "util.funcs",
                # "util.utils"
            ):
                importlib.import_module(import_name)
        except ImportError:
            slicer.util.errorDisplay(
                f"Unable to find OCTSeg.{import_name}\nCheck the console for details.",
                "Install Error",
            )
            return False
        return True

    def showInstalledModules(self, installed_modules):
        if installed_modules:
            plural = "" if len(installed_modules) == 1 else "s"
            version_text = "\n".join(
                [
                    f"    {install_name} version: {module.__version__}"
                    if hasattr(module, "__version__")
                    else f"    {install_name} version: unknown"
                    for import_name, install_name, module in installed_modules
                ],
            )
            slicer.util.infoDisplay(
                f"Module{plural} installed:\n" + version_text,
                f"Module{plural} Installed",
            )

    def installAndImportDependencies(self):
        needs_installation = []
        for import_name, install_name in self.python_dependencies:
            try:
                importlib.import_module(import_name)
            except ModuleNotFoundError:
                needs_installation.append((import_name, install_name))
        installed_modules = []
        if needs_installation:
            plural = "" if len(needs_installation) == 1 else "s"
            want_install = slicer.util.confirmYesNoDisplay(
                f"Package{plural} not found: "
                + ", ".join([import_name for import_name, _ in needs_installation])
                + f"\nInstall the package{plural}?",
                "Missing Dependencies" if plural == "s" else "Missing Dependency",
            )
            if not want_install:
                mesg = f"Package{plural} installation declined; giving up."
                slicer.util.errorDisplay(mesg, "Install Error")
                print(mesg)
                return False
            try:
                # Install missing packages
                with BusyCursor():
                    slicer.util.pip_install(["--upgrade", "pip", "setuptools", "wheel"])
                    slicer.util.pip_install(
                        [install_name for _, install_name in needs_installation]
                        + ["--extra-index-url", "https://download.pytorch.org/whl/cpu"],
                    )
                    installed_modules = [
                        (
                            import_name,
                            install_name,
                            importlib.import_module(import_name),
                        )
                        for import_name, install_name in needs_installation
                    ]
            except ModuleNotFoundError as e2:
                slicer.util.errorDisplay(
                    "\n".join(
                        [
                            f"Unable to install package{plural}.",
                            "Check the console for details.",
                        ],
                    ),
                    "Install Error",
                )
                print(e2)
                return False

        # All dependencies were successfully imported
        self.showInstalledModules(installed_modules)
        return True

    def runOCTSeg(
        self,
        octSegDirectory,
        vPAWOCTConfigFile,
    ):
        """
        Run the OCT Segmentation pipeline.
        Can be used without GUI widget.

        Parameters
        ----------
        octSegDirectory : str
            This is the directory containing the source code for OCTSeg.
        vPAWOCTConfigFile : str
            This is the full path name to a top-level configuration file such as
            uncbiag/OCTSeg/configs/unet_v2/unet_v2_test_1_channel.yaml.
        """
        # If self.OCTSeg_directory is not yet set then see if we can set it.
        if not hasattr(self, "OCTSeg_directory") and not (
            os.path.isdir(octSegDirectory) and self.linkOCTSeg(octSegDirectory)
        ):
            # We don't have self.OCTSeg_directory and we couldn't get it.
            return False

        startTime = time.time()
        logging.info("OCT Segmentation pipeline started")

        response = self.runSegmentation(vPAWOCTConfigFile)
        if response:
            model_path = self.getModelPathFromYAML(vPAWOCTConfigFile)
            # Tell the user where to find the results
            slicer.util.infoDisplay(
                "The pipeline has completed.  "
                + f"The results can be found in subdirectories of {model_path!r}.",
                "Pipeline ran",
            )

        stopTime = time.time()
        logging.info(
            f"OCT Segmentation pipeline completed in {stopTime-startTime:.2f}"
            + " seconds",
        )
        return response

    def runSegmentation(self, vPAWOCTConfigFile):
        cwd = os.getcwd()
        response = True
        try:
            os.chdir(self.OCTSeg_directory)
            slicer.util._executePythonModule("test_base", ["-c", vPAWOCTConfigFile])
        except Exception:
            response = False
            slicer.util.errorDisplay("The run failed.", "Run Error")
        finally:
            os.chdir(cwd)
        return response

    def getModelPathFromYAML(self, vPAWOCTConfigFile):
        # Cannot import yaml at file scope because it might not yet be installed at
        # that time.
        import yaml

        with open(vPAWOCTConfigFile) as stream:
            yaml_dict = yaml.safe_load(stream)
        return os.path.join(yaml_dict["disk"], yaml_dict["model_path"])


#
# VPAWModelOCTTest
#


class VPAWModelOCTTest(slicer.ScriptedLoadableModule.ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """
        Do whatever is needed to reset the state - typically a scene clear will be
        enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_VPAWModelOCT1()

    def test_VPAWModelOCT1(self):
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
