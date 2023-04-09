import logging
import numpy as np
import os
from pathlib import Path
import pickle as pk
import slicer
import slicer.ScriptedLoadableModule
import slicer.util
import vtk
import qt


def summary_repr(contents):
    """
    Like Python `repr`, returns a string representing the contents.  However, numpy
    arrays are summarized as their shape and unknown types are summarized by their type.

    Parameters
    ----------
    contents : Python object

    Returns
    -------
    A string representation of a summary of the object
    """

    if isinstance(contents, list):
        return "[" + ", ".join([summary_repr(elem) for elem in contents]) + "]"
    elif isinstance(contents, tuple):
        if len(contents) == 1:
            return "(" + summary_repr(contents[0]) + ",)"
        else:
            return "(" + ", ".join([summary_repr(elem) for elem in contents]) + ")"
    elif isinstance(contents, dict):
        return (
            "{"
            + ", ".join(
                [
                    summary_repr(key) + ": " + summary_repr(value)
                    for (key, value) in contents.items()
                ]
            )
            + "}"
        )
    elif isinstance(contents, set):
        return "{" + ", ".join([summary_repr(elem) for elem in contents]) + "}"
    elif isinstance(contents, (int, float, np.float32, np.float64, bool, str)):
        return repr(contents)
    elif isinstance(contents, np.ndarray):
        return repr(type(contents)) + ".shape=" + summary_repr(contents.shape)
    else:
        return repr(type(contents))


#
# VPAWVisualize
#


class VPAWVisualize(slicer.ScriptedLoadableModule.ScriptedLoadableModule):
    """
    Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        slicer.ScriptedLoadableModule.ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "VPAW Visualize"
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
This is the scripted loadable module named VPAW Visualize.  See more information in
<a href="https://github.com/KitwareMedical/vpaw#VPAWVisualize">module documentation</a>.
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
# VPAWVisualizeWidget
#


class VPAWVisualizeWidget(
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
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/VPAWVisualize.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level
        # qMRMLWidget's "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each
        # MRML widget's.  "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible
        # to run in batch mode, without a graphical user interface.
        self.logic = VPAWVisualizeLogic()

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
        self.ui.DataDirectory.connect(
            "currentPathChanged(const QString&)", self.updateParameterNodeFromGUI
        )
        self.ui.PatientPrefix.connect(
            "textChanged(const QString&)", self.updateParameterNodeFromGUI
        )

        # Buttons
        self.ui.HomeButton.connect("clicked(bool)", self.onHomeButton)
        self.ui.VPAWModelButton.connect("clicked(bool)", self.onVPAWModelButton)
        self.ui.showButton.connect("clicked(bool)", self.onShowButton)
        self.ui.computeIsosurfacesButton.connect("clicked(bool)", self.onComputeIsosurfacesButton)
        self.updateComputeIsosurfacesButtonEnabledness()

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

        self.ui.subjectHierarchyTree.setMRMLScene(slicer.mrmlScene)
        shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        self.addObserver(shNode, shNode.SubjectHierarchyItemModifiedEvent, self.shItemModifiedEvent)

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
        if self._parameterNode is not None:
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
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause
        # infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.DataDirectory.currentPath = self._parameterNode.GetParameter(
            "DataDirectory"
        )
        self.ui.PatientPrefix.text = self._parameterNode.GetParameter("PatientPrefix")

        # Update buttons states and tooltips
        if os.path.isdir(self.ui.DataDirectory.currentPath):
            # Enable show button
            self.ui.showButton.toolTip = (
                f"Show files from {repr(self.ui.DataDirectory.currentPath)}"
                + (
                    f" with prefix {repr(self.ui.PatientPrefix.text)}"
                    if self.ui.PatientPrefix.text != ""
                    else ""
                )
            )
            self.ui.showButton.enabled = True
        else:
            # Disable show button
            self.ui.showButton.toolTip = (
                "Show is disabled; first select a valid data directory"
            )
            self.ui.showButton.enabled = False

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
            "DataDirectory", self.ui.DataDirectory.currentPath
        )
        self._parameterNode.SetParameter("PatientPrefix", self.ui.PatientPrefix.text)

        self._parameterNode.EndModify(wasModified)

    @vtk.calldata_type(vtk.VTK_LONG)
    def shItemModifiedEvent(self, caller, eventId, callData):
        """Callback for when a subject hierarchy item is modified."""
        qt.QTimer.singleShot(2000, self.updateComputeIsosurfacesButtonEnabledness)

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

    def onShowButton(self):
        """
        When the user clicks the Show button, find the requested files and load them in
        to 3D Slicer's subject hierarchy.
        """

        with slicer.util.tryWithErrorDisplay(
            "Failed to show patient data.", waitCursor=True
        ):
            if self.ui.PatientPrefix.text == "":
                raise ValueError("Provide a patient prefix for which to show data.")
            list_of_files = self.logic.find_and_sort_files_with_prefix(
                self.ui.DataDirectory.currentPath, self.ui.PatientPrefix.text
            )
            if len(list_of_files) == 0:
                raise FileNotFoundError("No patient found with the given prefix.")
            self.logic.clearSubject()
            self.logic.loadNodesToSubjectHierarchy(list_of_files, self.ui.PatientPrefix.text)
            self.logic.arrangeView()
            self.updateComputeIsosurfacesButtonEnabledness()


    def onComputeIsosurfacesButton(self):
        """
        Compute isosurfaces of the laplace sol'n image
        """

        with slicer.util.tryWithErrorDisplay(
            "Unable to compute isosurfaces; see exception message below.", waitCursor=True
        ):
            try:
                self.ui.computeIsosurfacesStackedWidget.setCurrentIndex(1) # show progress bar
                def progress_callback(progress_percentage):
                    self.ui.computeIsosurfacesProgressBar.setValue(progress_percentage)
                progress_callback(0)
                slicer.app.processEvents() # I found this was needed to get the widget to visually repaint before the progress increases in the computation. -E
                self.logic.compute_isosurfaces(progress_callback)
            finally:
                self.ui.computeIsosurfacesStackedWidget.setCurrentIndex(0) # revert to showing button
                self.updateComputeIsosurfacesButtonEnabledness()

    def updateComputeIsosurfacesButtonEnabledness(self):
        """Enable or disable the compute isosurfaces button based on state of the VPAWVisualizeLogic"""
        if not self.logic.subjectIsCurrentlyLoaded():
            self.ui.computeIsosurfacesButton.setEnabled(False)
            self.ui.computeIsosurfacesButton.setToolTip("Load a subject to enable this")
            return
        if self.logic.isosurface_exists():
            self.ui.computeIsosurfacesButton.setEnabled(False)
            self.ui.computeIsosurfacesButton.setToolTip("Isosurfaces model already exists")
            return
        self.ui.computeIsosurfacesButton.setEnabled(True)
        self.ui.computeIsosurfacesButton.setToolTip("Compute isosurfaces model from the laplace solution")





#
# VPAWVisualizeLogic
#


class VPAWVisualizeLogic(slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic):
    """This class should implement all the actual computation done by your module.  The
    interface should be such that other python code can import this class and make use
    of the functionality without requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member
        variables.
        """

        slicer.ScriptedLoadableModule.ScriptedLoadableModuleLogic.__init__(self)
        self.clearSubject()

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """

        if not parameterNode.GetParameter("Threshold"):
            parameterNode.SetParameter("Threshold", "100.0")
        if not parameterNode.GetParameter("Invert"):
            parameterNode.SetParameter("Invert", "false")

    def find_files_with_prefix(self, path, prefix, include_subjectless=False):
        """
        Find all file names within `path` recursively that start with `prefix`

        Parameters
        ----------
        path : str
            Initially, the top-level directory to be scanned for files.  For recursive
            calls, it will be a directory or file within the top-level directory's
            hierarchy.
        prefix: str
            A value such as "1000_" will find all proper files that have basenames that
            start with that string.  If prefix=="" then all files regardless of name
            will be reported.
        include_subjectless: bool
            If set to True then files not associated with any patient will also be
            included.

        Returns
        -------
        When `path` is a file, returns the one-tuple list `[(path, mtime)]` if the
            `path` basename begins with `prefix`; otherwise returns an empty list.
            "mtime" is the modification time returned by os.path.getmtime(path).
        When `path` is a directory, returns the concatenation of the lists generated by
            a recursive call to find_files_with_prefix for each entry in the directory.
        """

        if os.path.isdir(path):
            # This `path` is a directory.  Recurse to all files and directories within
            # `path` and flatten the responses into a single list.
            response = [
                record
                for sub in os.listdir(path)
                for record in self.find_files_with_prefix(
                    os.path.join(path, sub), prefix, include_subjectless
                )
            ]
        else:
            # This path is not a directory.  Return a list containting the path if the
            # path basename begins with `prefix`, otherwise return an empty list.
            response = [
                (p, os.path.getmtime(p))
                for p in (path,)
                if os.path.basename(p).startswith(prefix)
                or (
                    include_subjectless
                    and (
                        "mean_landmarks" in p
                        or "FilteredControlBlindingLogUniqueScanFiltered" in p
                        or "weighted_perc" in p
                    )
                )
            ]
        return response

    def find_and_sort_files_with_prefix(self, dataDirectory, patientPrefix):
        """
        Find all file names within `path` recursively that start with `prefix`, and sort
        them by their modification times

        Parameters
        ----------
        dataDirectory : str
            The top-level directory to be scanned for files.
        patientPrefix: str
            A value such as "1000_" will find all proper files that have basenames that
            start with that string.  If prefix=="" then all files regardless of name
            will be reported.

        Returns
        -------
        When `path` is a directory, returns a list of the requested files, sorted
        chronologically by their modification times in
        """

        if not (isinstance(dataDirectory, str) and os.path.isdir(dataDirectory)):
            raise ValueError(
                f"Data directory (value={repr(dataDirectory)}) is not valid"
            )
        if not (patientPrefix is None or isinstance(patientPrefix, str)):
            raise ValueError(
                f"Patient prefix (value={repr(patientPrefix)}) is not valid"
            )
        if patientPrefix is None:
            patientPrefix = ""

        import time

        startTime = time.time()
        logging.info("Processing started")

        list_of_records = self.find_files_with_prefix(
            dataDirectory, patientPrefix, include_subjectless=False
        )
        # Sort by modification time
        list_of_records.sort(key=lambda record: record[1])
        # Remove modification times
        list_of_files = [record[0] for record in list_of_records]

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")

        return list_of_files

    def loadFromP3File(self, filename, properties):
        """
        Load a node based upon a P3 file, in lieu of a 3D Slicer "slicer.util.load*"
        function.

        Parameters
        ----------
        filename : str
            The file from which to read the data that will define the created node
        properties : dict
            A dictionary of properties that otherwise would be passed to most
            slicer.util.load* functions, but in this case is parsed for anything useful

        Returns
        -------
        A 3D Slicer node object representing the data
        """

        with open(filename, "rb") as f:
            contents = pk.load(f)

        if Path(filename).parent.stem == "centerline":
            return self.loadCenterlineFromP3FileContents(contents)

        print(f"File type for {filename} is not currently supported")
        print(f"{filename} contains {summary_repr(contents)}")  # !!!
        # !!! Create node from contents

        return None

    def loadCenterlineFromP3FileContents(self, contents):
        """
        Load a centerline using the data object written into a P3 file named "####_CENTERLINE.p3"

        Parameters
        ----------
        contents : a pair of arrays (centerline_points, centerline_normals). Currently we only use
            centerline_points, piecing them together into a curve node.

        Returns
        -------
        A vtkMRMLMarkupsCurveNode
        """
        centerline_points, centerline_normals = contents
        centerline_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode")
        centerline_node.SetName("Centerline")
        slicer.util.updateMarkupsControlPointsFromArray(centerline_node, centerline_points)
        centerline_node.GetDisplayNode().SetGlyphTypeFromString("Vertex2D")
        centerline_node.SetCurveTypeToLinear()
        centerline_node.LockedOn() # don't allow mouse interaction to move control points
        return centerline_node

    def loadOneNode(self, filename, basename_repr, props):
        """
        Create a 3D Slicer node object for the data in a file

        Parameters
        ----------
        filename : str
            The file from which to read the data that will define the created node
        basename_repr: str
            A string representing the file, which is used for warning/error output
        props : dict
            A dictionary of properties that is passed to most slicer.util.load*
            functions

        Returns
        -------
        A 3D Slicer node object representing the data
        """

        # Determine the node type from the filename extension, using its
        # immediate-ancestor directory's name if necessary.  Note: check for ".seg.nrrd"
        # before checking for ".nrrd".
        if filename.endswith(".seg.nrrd"):
            node = slicer.util.loadSegmentation(filename, properties=props)
            node.CreateClosedSurfaceRepresentation()
        elif filename.endswith(".nrrd"):
            directory = os.path.basename(os.path.dirname(filename))
            if directory == "images":
                node = slicer.util.loadVolume(filename, properties=props)
                self.show_nodes.append(node)
            elif directory == "segmentations_computed":
                node = slicer.util.loadSegmentation(filename, properties=props)
                node.CreateClosedSurfaceRepresentation()
            else:
                # Guess
                node = slicer.util.loadVolume(filename, properties=props)
        elif filename.endswith(".fcsv"):
            node = slicer.util.loadMarkups(filename)
            assert(node.IsTypeOf('vtkMRMLMarkupsNode'))
            node.LockedOn() # don't allow mouse interaction to move control points
        elif filename.endswith(".mha"):
            node = slicer.util.loadVolume(filename, properties=props)
        elif filename.endswith(".png"):
            node = slicer.util.loadVolume(filename, properties=props)
        elif filename.endswith(".p3"):
            node = self.loadFromP3File(filename, properties=props)
        elif filename.endswith(".xls"):
            print(f"File type for {basename_repr} is not currently supported")
            node = None
        else:
            print(f"File type for {basename_repr} is not recognized")
            node = None
        return node

    def clearSubject(self):
        """ Set VPAWVisualizeLogic to initial state before any subject was loaded,
        and clear the subject hierarchy. """
        self.subject_id = None
        self.subject_item_id = None # subject hierarchy item id for the currently loaded subject
        self.input_image_node = None
        self.centerline_node = None
        self.segmentation_node = None
        self.laplace_sol_node = None
        self.laplace_sol_masked_node = None
        self.laplace_isosurface_node = None
        self.clearSubjectHierarchy()

    def clearSubjectHierarchy(self):
        """
        Remove all nodes from the 3D Slicer subject hierarchy
        """

        slicer.mrmlScene.GetSubjectHierarchyNode().RemoveAllItems(True)
        self.show_nodes = list()

    def subjectIsCurrentlyLoaded(self) -> bool:
        """Whether a subject has been loaded."""
        return self.subject_id is not None

    def put_node_under_subject(self, node):
        """Move the given node in the subject hierarchy such that it becomes a child of the
        subject item for the currently loaded subject. """
        shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
        node_item = shNode.GetItemByDataNode(node)
        shNode.SetItemParent(node_item, self.subject_item_id)

    def loadOneNodeToSubjectHierarchy(self, shNode, subject_item, filename):
        """
        Load data from a single file into a node and put the node in the 3D Slicer
        subject hierarchy

        Parameters
        ----------
        shNode: subject hierarchy node
            The 3D subject hierarchy node
        subject_item: int
            Parent for the node we are creating
        filename: str
            The data source for the file
        """

        # The node types supported by 3D Slicer generally can be found with fgrep
        # 'loadNodeFromFile(filename' from
        # https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/util.py.
        # Currently they are AnnotationFile, ColorTableFile, FiberBundleFile,
        # MarkupsFile, ModelFile, ScalarOverlayFile, SegmentationFile,
        # ShaderPropertyFile, TableFile, TextFile, TransformFile, and VolumeFile.

        basename = os.path.basename(filename)
        basename_repr = repr(basename)
        props = {"name": basename, "singleFile": True, "show": False}

        node = self.loadOneNode(filename, basename_repr, props)
        if node is None:
            return

        dirname = Path(filename).parent.stem
        if dirname == "sols":
            self.laplace_sol_node = node
        elif dirname == 'images':
            self.input_image_node = node
        elif dirname == 'centerline':
            self.centerline_node = node
        elif dirname == 'segmentations_computed':
            self.segmentation_node = node

        self.put_node_under_subject(node)

    def loadNodesToSubjectHierarchy(self, list_of_files, subject_name):
        """
        Load data from files into nodes and put the nodes in the 3D Slicer subject
        hierarchy

        Parameters
        ----------
        list_of_files : List[str]
            Files to be loaded
        subject_name : str
            Name for folder in subject hierarchy to contain the nodes
        """

        self.subject_id = subject_name

        # The subject hierarchy node can contain subject (patient), study (optionally),
        # and node items.  slicer.mrmlScene knows how to find the subject hierarchy
        # node.
        shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
        # A subject item is created with the subject hierarchy node as its parent.
        self.subject_item_id = shNode.CreateSubjectItem(shNode.GetSceneItemID(), subject_name)

        # slicer knows how to find the subject hierarchy tree view.
        shTV = slicer.qMRMLSubjectHierarchyTreeView()
        # Tell the subject hierarchy tree view about its enclosing scene.
        shTV.setMRMLScene(slicer.mrmlScene)
        # Tell the subject hierarchy tree view that its root item is the subject item.
        shTV.setRootItem(self.subject_item_id)

        for filename in list_of_files:
            self.loadOneNodeToSubjectHierarchy(shNode, self.subject_item_id, filename)

        self.fix_image_origins_and_spacings()
        self.restrict_laplace_sol_to_segmentation()

        # Recursively set visibility and expanded properties of each item
        def recurseVisibility(item, visibility, expanded):
            # Useful functions for traversing items
            # shNode.GetSceneItemID()
            # shNode.GetNumberOfItems()
            # shNode.GetNumberOfItemChildren(parentItem)
            # shNode.GetItemByPositionUnderParent(parentItem, childIndex)
            # shNode.SetItemExpanded(shNode.GetSceneItemID(), True)
            shNode.SetItemDisplayVisibility(item, visibility)
            shNode.SetItemExpanded(item, expanded)
            for child_index in range(shNode.GetNumberOfItemChildren(item)):
                recurseVisibility(
                    shNode.GetItemByPositionUnderParent(item, child_index),
                    visibility,
                    expanded,
                )

        recurseVisibility(self.subject_item_id, True, True)

        # Resize columns of the SubjectHierarchyTreeView
        shTV.header().resizeSections(shTV.header().ResizeToContents)
        # Force re-displaying of the SubjectHierarchyTreeView
        slicer.mrmlScene.StartState(slicer.vtkMRMLScene.ImportState)
        slicer.mrmlScene.EndState(slicer.vtkMRMLScene.ImportState)

    def fix_image_origins_and_spacings(self):
        """Some nodes rely on others for origin and spacing info, because it wasn't properly saved
        in the files from which we generate those nodes. This functions goes through and transfers
        origin and spacing info whereever it is needed. """

        if self.laplace_sol_node is not None and self.input_image_node is not None:
            self.laplace_sol_node.SetOrigin(self.input_image_node.GetOrigin())
            self.laplace_sol_node.SetSpacing(self.input_image_node.GetSpacing())

    def restrict_laplace_sol_to_segmentation(self):
        """If the laplace solution and the segmentation node both exist, mask the laplace solution
        volume by the segmentation node. If either of them doesn't exists, raise an exception."""

        if self.segmentation_node is None:
            raise RuntimeError("Could not find segmentation node.")
        if self.laplace_sol_node is None:
            raise RuntimeError("Could not find laplace solution node.")

        sol_array = slicer.util.arrayFromVolume(self.laplace_sol_node)

        seg_ids = self.segmentation_node.GetSegmentation().GetSegmentIDs()
        if len(seg_ids) != 1:
            raise RuntimeError(f"Expected node {self.segmentation_node.GetName()} to have exactly one segmentation.")
        seg_array = slicer.util.arrayFromSegmentBinaryLabelmap(self.segmentation_node, seg_ids[0], self.laplace_sol_node)

        sol_masked_array = np.copy(sol_array)
        sol_masked_array[seg_array==0] = np.nan

        sol_masked_node = slicer.modules.volumes.logic().CloneVolume(self.laplace_sol_node, self.laplace_sol_node.GetName()+"_restrictedToSegmentation")
        slicer.util.updateVolumeFromArray(sol_masked_node, sol_masked_array)
        self.put_node_under_subject(sol_masked_node)
        self.laplace_sol_masked_node = sol_masked_node


    def arrangeView(self):
        """
        Make the 3D Slicer viewing panels default to something reasonable
        """

        # Make sure at least one input image (if any) is being viewed
        if self.show_nodes:
            slicer.util.setSliceViewerLayers(foreground=self.show_nodes[0], fit=True)
        self.show_nodes = list()

        # Center the 3D view
        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()


    def compute_isosurfaces(self, progress_callback=None):
        """ Compute isosurfaces of the laplace solution image, if one exists.
        Raises exception if none exists.

        Args:
            progress_callback: Optionally, a function that takes a progress_percentage float value.
                If this is provided then progress_callback(progress_percentage) will be called by compute_isosurfaces
                while the computation is being done.
        """
        if self.laplace_sol_node is None:
            raise RuntimeError("No Laplace solution seems to have been loaded.")
        if self.laplace_sol_masked_node is None:
            raise RuntimeError("No masked Laplace solution was found; there should be a volume node consisting of the Laplace solution restricted to the airway segmentation.")

        if progress_callback is None:
            progress_callback = lambda progress_percentage : None
            # defining a function that does nothing is cleaner than checking for None repeatedly below

        sol_node_name = self.laplace_sol_node.GetName()

        isosurface_values = np.linspace(0,1,11)

        # marching cubes does not work great at actual min or max value
        # so we leave a bit of room
        isosurface_values[0] += 0.02
        isosurface_values[-1] -= 0.02

        output_models = []
        for i,value in enumerate(isosurface_values):
            output_model_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
            output_models.append(output_model_node)
            output_model_node.SetName(f"{sol_node_name}_{value:0.2f}")
            parameters = {
            'InputVolume' : self.laplace_sol_masked_node,
            'OutputGeometry' : output_model_node,
            'Threshold' : value,
            'Smooth' : 0,
            'Decimate' : 0.25,
            'SplitNormals' : True,
            'PointNormals' : True,
            }
            cli_node = slicer.cli.runSync(slicer.modules.grayscalemodelmaker, None, parameters)
            if cli_node.GetStatus() & cli_node.ErrorsMask:
                errorText = cli_node.GetErrorText()
                slicer.mrmlScene.RemoveNode(cli_node)
                raise ValueError("Grayscale Model Maker execution failed: " + errorText)
            slicer.mrmlScene.RemoveNode(cli_node)
            progress_callback(80 * (i+1)/len(isosurface_values))

        # now output_models should be merged
        merge_polydata_filter = vtk.vtkAppendPolyData()
        for model_node in output_models:
            merge_polydata_filter.AddInputConnection(model_node.GetPolyDataConnection())
        merge_polydata_filter.Update()
        progress_callback(90)
        merged_model_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
        merged_model_node.SetName(f"{sol_node_name}_isosurfaces")
        merged_model_node.SetAndObservePolyData(merge_polydata_filter.GetOutput())
        for model_node in output_models:
            slicer.mrmlScene.RemoveNode(model_node)
        progress_callback(100)
        merged_model_node.CreateDefaultDisplayNodes()
        merged_model_node.GetDisplayNode().SetVisibility(True)
        self.put_node_under_subject(merged_model_node)
        self.laplace_isosurface_node = merged_model_node

    def isosurface_exists(self) -> bool:
        """Whether isosurface has already been computed"""
        return (
            self.laplace_isosurface_node is not None
            and slicer.mrmlScene.GetNodeByID(self.laplace_isosurface_node.GetID()) is not None
        )

#
# VPAWVisualizeTest
#


class VPAWVisualizeTest(slicer.ScriptedLoadableModule.ScriptedLoadableModuleTest):
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
        self.test_VPAWVisualize1()

    def test_VPAWVisualize1(self):
        """
        Ideally you should have several levels of tests.  At the lowest level tests
        should exercise the functionality of the logic with different inputs (both valid
        and invalid).  At higher levels your tests should emulate the way the user would
        interact with your code and confirm that it still works the way you intended.

        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on, your
        test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        self.delayDisplay("Test skipped")
