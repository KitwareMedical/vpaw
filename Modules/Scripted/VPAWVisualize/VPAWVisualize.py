import logging
import os
import slicer
import slicer.ScriptedLoadableModule
import slicer.util
import vtk


#
# VPAWVisualize
#


class VPAWVisualize(slicer.ScriptedLoadableModule.ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
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
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)

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
        self.ui.DataDirectory.currentPath = str(
            self._parameterNode.GetParameter("DataDirectory")
        )
        self.ui.PatientPrefix.text = str(
            self._parameterNode.GetParameter("PatientPrefix")
        )

        # Update buttons states and tooltips
        # !!! Gray out button ....enabled = False and change ....toolTip based upon
        # !!! whether DataDirectory is sensible

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
            "DataDirectory", str(self.ui.DataDirectory.currentPath)
        )
        self._parameterNode.SetParameter(
            "PatientPrefix", str(self.ui.PatientPrefix.text)
        )

        self._parameterNode.EndModify(wasModified)

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        with slicer.util.tryWithErrorDisplay(
            "Failed to compute results.", waitCursor=True
        ):

            # Compute output
            self.logic.process(
                self.ui.DataDirectory.currentPath, self.ui.PatientPrefix.text
            )


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

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("Threshold"):
            parameterNode.SetParameter("Threshold", "100.0")
        if not parameterNode.GetParameter("Invert"):
            parameterNode.SetParameter("Invert", "false")

    def process(self, dataDirectory, patientPrefix):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param dataDirectory: root directory containing data
        :param patientPrefix: prefix string for selecting which files are relevant
        """

        if not dataDirectory or not patientPrefix:
            raise ValueError("Data directory or patient prefix is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # !!! Call find_files_with_prefix, instantiate collapsed widgets (via
        # !!! VPAWVisualizeWidget somehow -- callback?), and make contents for them.

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")

    def find_files_with_prefix(self, path, prefix):
        """Find all file names within `path` recursively that start with `prefix`

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

        Returns
        -------
        When `path` is a file, returns the one-element list `[path]` if the `path`
            basename begins with `prefix`; otherwise returns an empty list.
        When `path` is a directory, returns the concatenation of the lists generated by
            a recursive call to find_files_with_prefix for each entry in the directory.

        """
        if os.path.isdir(path):
            # This `path` is a directory.  Recurse to all files and directories within
            # `path` and flatten the responses into a single list.
            response = [
                item
                for sub in os.listdir(path)
                for item in self.find_files_with_prefix(os.path.join(path, sub), prefix)
            ]
        else:
            # This path is not a directory.  Return a list containting the path if the
            # path basename begins with `prefix`, otherwise return an empty list.
            response = [p for p in (path,) if os.path.basename(p).startswith(prefix)]
        return response


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
        """Do whatever is needed to reset the state - typically a scene clear will be
        enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_VPAWVisualize1()

    def test_VPAWVisualize1(self):
        """Ideally you should have several levels of tests.  At the lowest level
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

        self.delayDisplay("Test skipped")
