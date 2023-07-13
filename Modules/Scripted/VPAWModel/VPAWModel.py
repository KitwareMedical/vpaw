import importlib
import logging
import os
import pathlib
import qt
import slicer
import slicer.ScriptedLoadableModule
import slicer.util
import sys
import tempfile
import time
import vtk


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
# VPAWModel
#


class VPAWModel(slicer.ScriptedLoadableModule.ScriptedLoadableModule):
    """
    Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        slicer.ScriptedLoadableModule.ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "VPAW Model"
        self.parent.categories = ["VPAW"]
        # TODO: add here list of module names that this module requires
        self.parent.dependencies = []
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
            slicer.vtkMRMLAbstractViewNode.OrientationMarkerTypeAxes
        )

        # Create logic class.  Logic implements all computations that should be possible
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
        self.ui.VPAWModelsDirectory.connect(
            "currentPathChanged(const QString&)", self.updateParameterNodeFromGUI
        )
        self.ui.PatientPrefix.connect(
            "textChanged(const QString&)", self.updateParameterNodeFromGUI
        )
        self.ui.PediatricAirwayAtlasDirectory.connect(
            "validInputChanged(bool)", self.updateParameterNodeFromGUI
        )
        self.ui.VPAWRootDirectory.connect(
            "validInputChanged(bool)", self.updateParameterNodeFromGUI
        )
        self.ui.VPAWModelsDirectory.connect(
            "validInputChanged(bool)", self.updateParameterNodeFromGUI
        )

        # Buttons
        self.ui.VPAWVisualizeButton.connect("clicked(bool)", self.onVPAWVisualizeButton)
        self.ui.HomeButton.connect("clicked(bool)", self.onHomeButton)
        self.ui.linkPediatricAirwayAtlasButton.connect(
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
        # etc. so that when the scene is saved and reloaded, these settings are
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
        self.ui.VPAWModelsDirectory.currentPath = self._parameterNode.GetParameter(
            "VPAWModelsDirectory"
        )
        self.ui.PatientPrefix.text = self._parameterNode.GetParameter("PatientPrefix")

        # Update buttons states and tooltips
        self.ui.PediatricAirwayAtlasDirectory.toolTip = "Root directory for source code"
        if os.path.isdir(self.ui.PediatricAirwayAtlasDirectory.currentPath):
            self.ui.linkPediatricAirwayAtlasButton.toolTip = (
                "Link to Pediatric Airway Atlas codebase and install dependencies"
            )
            self.ui.linkPediatricAirwayAtlasButton.enabled = True
        else:
            self.ui.linkPediatricAirwayAtlasButton.toolTip = (
                "Install is disabled; first select a valid source code directory for"
                + " the Pediatric Airway Atlas"
            )
            self.ui.linkPediatricAirwayAtlasButton.enabled = False

        self.ui.VPAWRootDirectory.toolTip = (
            "Directory containing FilteredControlBlindingLogUniqueScanFiltered.xls,"
            + " images/*, and landmarks/*."
        )
        self.ui.VPAWModelsDirectory.toolTip = (
            "Directory containing file named like '116(158.10-38.AM.24.Mar).pth'"
        )
        self.ui.PatientPrefix.toolTip = (
            "Process only files with this prefix.  Blank means all files."
        )
        if os.path.isdir(self.ui.VPAWRootDirectory.currentPath) and os.path.isdir(
            self.ui.VPAWModelsDirectory.currentPath
        ):
            self.ui.runPediatricAirwayAtlasButton.toolTip = (
                "Run Pediatric Airway Atlas (This may take many hours)"
            )
            self.ui.runPediatricAirwayAtlasButton.enabled = True
        else:
            self.ui.runPediatricAirwayAtlasButton.toolTip = (
                "Run is disabled; first select input/output root directory and models"
                + " directory"
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

        # Modify all properties in a single batch
        wasModified = self._parameterNode.StartModify()

        self._parameterNode.SetParameter(
            "PediatricAirwayAtlasDirectory",
            self.ui.PediatricAirwayAtlasDirectory.currentPath,
        )
        self._parameterNode.SetParameter(
            "VPAWRootDirectory", self.ui.VPAWRootDirectory.currentPath
        )
        self._parameterNode.SetParameter(
            "VPAWModelsDirectory", self.ui.VPAWModelsDirectory.currentPath
        )
        self._parameterNode.SetParameter("PatientPrefix", self.ui.PatientPrefix.text)

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
            self.logic.linkPediatricAirwayAtlas(
                self.ui.PediatricAirwayAtlasDirectory.currentPath
            )

    def onRunPediatricAirwayAtlasButton(self):
        """
        Parameters
        ----------
        VPAWRootDirectory :
            This is the input/output directory, e.g., "path/to/vpaw-data-root".  It must
            contain FilteredControlBlindingLogUniqueScanFiltered.xls, images/*, and
            landmarks/*.
        VPAWModelsDirectory :
            It must contain a file with name like "116(158.10-38.AM.24.Mar).pth".
        PatientPrefix :
            Process only files with this prefix.  Blank means all files.

        Run the Pediatric Airway Atlas pipeline at the user's request.
        """
        with slicer.util.tryWithErrorDisplay(
            "Failed to compute results.", waitCursor=True
        ):
            self.logic.runPediatricAirwayAtlas(
                self.ui.VPAWRootDirectory.currentPath,
                self.ui.VPAWModelsDirectory.currentPath,
                self.ui.PatientPrefix.text,
            )


#
# VPAWModelLogic
#


class VPAWModelLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):
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
        # requirements.txt file for pediatric_airway_atlas.  Because it isn't,
        # self.python_dependencies is a sequence of pairs.  For each pair the first
        # entry is a name that is used with Python `import`.  The second is a name that
        # is used with Python `pip install`, and can include version information.
        self.python_dependencies = (
            ("colour", "colour"),
            ("cv2", "opencv-python"),
            ("itk", "itk"),
            ("matplotlib", "matplotlib"),
            ("monai", "monai"),
            ("mplcursors", "mplcursors"),
            ("nrrd", "pynrrd"),
            ("numpy", "numpy"),
            ("pandas", "pandas"),
            ("pydicom", "pydicom"),
            ("pyransac3d", "pyransac3d"),
            ("pyrender", "pyrender"),
            ("pytorch_lightning", "pytorch_lightning"),
            ("rtree", "rtree"),
            ("ruffus", "ruffus"),
            ("shapely", "shapely"),
            ("SimpleITK", "SimpleITK"),
            ("skimage", "scikit-image"),
            ("sklearn", "scikit-learn"),
            ("skspatial", "scikit-spatial"),
            ("tensorboard", "tensorboard"),
            ("torchvision", "torchvision"),
            ("tqdm", "tqdm"),
            ("trimesh", "trimesh"),
            ("vtk", "vtk"),
            ("xlrd", "xlrd"),
            ("yaml", "pyyaml"),
        )

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        pass

    def linkPediatricAirwayAtlas(self, pediatricAirwayAtlasDirectory):
        startTime = time.time()
        logging.info("Pediatric Airway Atlas installation started")

        if self.installAndImportDependencies() and self.ensureModulePath(
            pediatricAirwayAtlasDirectory
        ):
            # No error messages have been sent to the user, so let's assure the user
            # that something useful has happened.
            slicer.util.infoDisplay("Pediatric Airway Atlas is linked", "Linked")

        stopTime = time.time()
        logging.info(
            f"Pediatric Airway Atlas installation completed in {stopTime-startTime:.2f}"
            + " seconds"
        )

    def ensureModulePath(self, directory):
        self.pediatric_airway_atlas_directory = str(pathlib.Path(directory))
        if self.pediatric_airway_atlas_directory not in sys.path:
            sys.path.insert(0, self.pediatric_airway_atlas_directory)
            importlib.invalidate_caches()
        try:
            for module_name in ("conversion_utils.generate_pixel_space_landmarks",):
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
                    f"    {pip_install_name} version: {module.__version__}"
                    if hasattr(module, "__version__")
                    else f"    {pip_install_name} version: unknown"
                    for module_name, pip_install_name, module in installed_modules
                ]
            )
            slicer.util.infoDisplay(
                f"Module{plural} installed:\n" + version_text,
                f"Module{plural} Installed",
            )

    def installAndImportDependencies(self):
        needs_installation = []
        for module_name, pip_install_name in self.python_dependencies:
            try:
                importlib.import_module(module_name)
            except ModuleNotFoundError as e1:
                needs_installation.append((module_name, pip_install_name))
        installed_modules = []
        if needs_installation:
            plural = "" if len(needs_installation) == 1 else "s"
            want_install = slicer.util.confirmYesNoDisplay(
                f"Package{plural} not found: "
                + ", ".join([module_name for module_name, _ in needs_installation])
                + f"\nInstall the package{plural}?  (This may take a while)",
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
                        [pip_install_name for _, pip_install_name in needs_installation]
                    )
                    installed_modules = [
                        (
                            module_name,
                            pip_install_name,
                            importlib.import_module(module_name),
                        )
                        for module_name, pip_install_name in needs_installation
                    ]
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

    def runPediatricAirwayAtlas(
        self, vPAWRootDirectory, vPAWModelsDirectory, patientPrefix
    ):
        """
        Run the Pediatric Airway Atlas pipeline.
        Can be used without GUI widget.

        Parameters
        ----------
        vPAWRootDirectory : str
            This is the input/output directory, e.g., "path/to/vpaw-data-root".  It must
            contain FilteredControlBlindingLogUniqueScanFiltered.xls, images/*, and
            landmarks/*.
        vPAWModelsDirectory : str
            It must contain a file with name like "116(158.10-38.AM.24.Mar).pth".
        patientPrefix : str
            Process only files with this prefix.  Blank means all files.
        """
        startTime = time.time()
        logging.info("Pediatric Airway Atlas pipeline started")

        # self.convertCTScansToNRRD(vPAWRootDirectory)
        if self.convertFCSVLandmarksToP3(
            vPAWRootDirectory, patientPrefix
        ) and self.runSegmentation(
            vPAWRootDirectory, vPAWModelsDirectory, patientPrefix
        ):
            slicer.util.infoDisplay("The pipeline has completed", "Pipeline ran")

        stopTime = time.time()
        logging.info(
            f"Pediatric Airway Atlas pipeline completed in {stopTime-startTime:.2f}"
            + " seconds"
        )

    def convertFCSVLandmarksToP3(self, vPAWRootDirectory, patientPrefix):
        cwd = os.getcwd()
        try:
            os.chdir(self.pediatric_airway_atlas_directory)

            images_dir = os.path.join(vPAWRootDirectory, "images")
            input_landmarks_dir = os.path.join(vPAWRootDirectory, "landmarks")
            output_landmarks_dir = os.path.join(
                vPAWRootDirectory, "transformed_landmarks"
            )
            num_workers = 1
            subject_prefix = patientPrefix
            if subject_prefix is not None and subject_prefix != "":
                try:
                    slicer.util._executePythonModule(
                        "conversion_utils.generate_pixel_space_landmarks",
                        [
                            f"--images_dir={images_dir}",
                            f"--input_landmarks_dir={input_landmarks_dir}",
                            f"--output_landmarks_dir={output_landmarks_dir}",
                            f"--num_workers={num_workers}",
                            f"--subject_prefix={subject_prefix}",
                        ],
                    )
                except:
                    slicer.util.errorDisplay(
                        "The run failed.  It may be that a non-blank patient prefix is"
                        + " not supported by this version of pediatric_airway_atlas"
                        + ".conversion_utils.generate_pixel_space_landmarks."
                        + "  Please update pediatric_airway_atlas and try again.",
                        "Run Error",
                    )
                    return False
            else:
                slicer.util._executePythonModule(
                    "conversion_utils.generate_pixel_space_landmarks",
                    [
                        f"--images_dir={images_dir}",
                        f"--input_landmarks_dir={input_landmarks_dir}",
                        f"--output_landmarks_dir={output_landmarks_dir}",
                        f"--num_workers={num_workers}",
                    ],
                )
        finally:
            os.chdir(cwd)
        return True

    def runSegmentation(self, vPAWRootDirectory, vPAWModelsDirectory, patientPrefix):
        cwd = os.getcwd()
        ConfigDescriptor, ConfigName = None, None
        SegmentDescriptor, SegmentName = None, None
        try:
            # Cannot import yaml at file scope because it might not yet be installed at
            # that time.
            import yaml

            # Change directory and create files
            os.chdir(self.pediatric_airway_atlas_directory)
            ConfigDescriptor, ConfigName = tempfile.mkstemp(suffix=".yaml", text=True)
            SegmentDescriptor, SegmentName = tempfile.mkstemp(suffix=".yaml", text=True)

            # Add text to the main configuration file
            b_s_f_s = "False"
            n_p = 1
            ConfigYaml = dict(
                root=vPAWRootDirectory,
                n_samples=-1,
                metadata_excel_fname="FilteredControlBlindingLogUniqueScanFiltered.xls",
                band_depth_ages=[20, 40, 60, 80, 100, 120, 140],
                n_centerline_points=200,
                n_curve_points=500,
                TARGET_LANDMARKS_ORDERED=[
                    "nasalspine",
                    "choana",
                    "epiglottistip",
                    "tvc",
                    "subglottis",
                    "carina",
                ],
                dilation_times=20,
                ALL_POSSIBLE_LANDMARKS=[
                    "carina",
                    "tracheacarina",
                    "trachea",
                    "tvc",
                    "subglottis",
                    "epiglottistip",
                    "columella",
                    "nasalspine",
                    "rightalarim",
                    "leftalarim",
                    "nosetip",
                    ["choana", "posteriorinferiorvomercorner"],
                    "pyrinaaperture",
                    ["baseoftongue", "tonguebase"],
                ],
                plane_estimation_based_mesh_area=True,
                use_planes_for_laplace_marking=True,
                balance_spacing_for_segmentation=b_s_f_s,
                num_processes=n_p,
            )
            with os.fdopen(ConfigDescriptor, "w") as ConfigFile:
                ConfigDescriptor = None  # descriptor will close when `with` exits
                yaml.dump(ConfigYaml, ConfigFile)

            # Add text to the configuration file for segmentation
            SegmentYaml = dict(
                data_root_dir=vPAWRootDirectory,
                model_save_directory=vPAWModelsDirectory,
                crop_size=[192, 192, 192],
                network_model=dict(name="TwoStepSeparatedModel", params=dict()),
                dataset=dict(
                    image_min_max_normalization=[-1024.0, 3071.0],
                    extra_keys_to_fetch=["image_spacing"],
                    train_test_split_fpath="segmentation/train_test_split_new_with_spherical.yaml",
                ),
                loss_type="ce",
                loss_params=dict(pos_weight=[2.0], loss_multiplier=10.0),
                training=dict(
                    batch_size=8,
                    num_data_loaders=24,
                    log_interval=50,
                    max_training_iteration=1000000,
                    optimizer_params=dict(lr=0.0001, weight_decay=1e-05),
                ),
                inference=dict(
                    force_spacing=None, tiles_overlap=0.75, tile_fusion_mode="gaussian"
                ),
                train_devices=[0, 1],
            )
            with os.fdopen(SegmentDescriptor, "w") as SegmentFile:
                SegmentDescriptor = None  # descriptor will close when `with` exits
                yaml.dump(SegmentYaml, SegmentFile)

            # Run the pipeline
            if patientPrefix is not None and patientPrefix != "":
                try:
                    slicer.util._executePythonModule(
                        "atlas_builder_configurable",
                        [
                            f"--config={ConfigName}",
                            f"--segmentation_config={SegmentName}",
                            f"--subject_prefix={patientPrefix}",
                        ],
                    )
                except:
                    slicer.util.errorDisplay(
                        "The run failed.  It may be that a non-blank patient prefix is"
                        + " not supported by this version of pediatric_airway_atlas"
                        + ".atlas_builder_configurable."
                        + " Please update pediatric_airway_atlas and try again.",
                        "Run Error",
                    )
                    return False
            else:
                slicer.util._executePythonModule(
                    "atlas_builder_configurable",
                    [f"--config={ConfigName}", f"--segmentation_config={SegmentName}"],
                )

        finally:
            if ConfigDescriptor is not None:
                os.close(ConfigDescriptor)
                ConfigDescriptor = None
            if ConfigName is not None and os.path.exists(ConfigName):
                os.remove(ConfigName)
                ConfigName = None
            if SegmentDescriptor is not None:
                os.close(SegmentDescriptor)
                SegmentDescriptor = None
            if SegmentName is not None and os.path.exists(SegmentName):
                os.remove(SegmentName)
                SegmentName = None
            os.chdir(cwd)
        return True


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
        """
        Do whatever is needed to reset the state - typically a scene clear will be
        enough.
        """
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
