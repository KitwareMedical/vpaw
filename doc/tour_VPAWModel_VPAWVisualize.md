The Virtual Pediatric Airways Workbench (VPAW) is an application, based upon 3D
Slicer, for creating and visualizing anatomically accurate, three-dimensional
airway models for geometric and computational fluid dynamics analyses. Here we
describe two of its modules, VPAW Model and VPAW Visualize.

The **VPAW Model** module provides a graphical user interface so that the user
can easily install, configure, and run the pipelines from the
`pediatric_airway_atlas` repository. The pipeline starts with one CT image and
one set of landmarks per patient and produces a variety of additional images,
landmarks, segmentations, areas, centerlines, and Laplace transforms. These
outputs can be used in comparisons to atlas data.

The **VPAW Visualize** module facilitates the visualization of results produced
by the `pediatric_airway_atlas` pipelines. This module allows researchers to
visualize and overlay intermediate and final outputs for a patient.

# The VPAW Model module

When you start VPAW you start on the Home screen. To run the Pediatric Airway
Atlas pipeline, first click on the "Go to VPAW Model module" button.

<img src="./media/image8.png" style="width:6.5in;height:3.94444in" />

You need to specify the directory containing the source code for the Pediatric
Airway Atlas model. Click on the "**...**" button that is to the right of
"Pediatric Airway Atlas source directory."

<img src="./media/image29.png" style="width:6.5in;height:3.94444in" />

Use the dialog box to select the directory that contains your source code. This
is the top-level directory of the `uncbiag/pediatric_airway_atlas` git
repository on your local computer. Click the "Choose" button.

<img src="./media/image18.png" style="width:6.5in;height:4.48611in" />

You are returned to the VPAW Model screen. Click on the "Link to Pediatric
Airway Atlass codebase and install dependencies" button to tell VPAW that you
want to use the selected source code and install any required Python packages.
Note that these packages need to be installed only once and they are installed
to a Python environment that is internal to VPAW; they are not installed to
Python environments that you use outside of VPAW.

<img src="./media/image23.png" style="width:6.5in;height:3.94444in" />

If there are missing Python dependencies, you see a dialog box like the
following. Click the "Yes" button.

<img src="./media/image21.png"
style="width:5.22917in;height:1.65625in" />

Upon completion of the installation of the Python dependencies, you are alerted
to the version numbers of the successfully installed Python packages. Click the
"OK" button.

<img src="./media/image7.png"
style="width:2.92708in;height:4.65625in" />

Whether or not there were dependencies that needed to be installed, you are
notified that VPAW is now connected to the Pediatric Airway Atlas source code
that you supplied. Click the "OK" button.

<img src="./media/image6.png"
style="width:2.52083in;height:1.20833in" />

Next you need to specify the directory that contains your inputs to be processed
by the pipeline. This directory has a Microsoft Excel file called
FilteredControlBlindingLogUniqueScanFiltered.xls and two subdirectories, images
and landmarks. The images subdirectory has one `PPPP\_INPUT.nrrd` file per
patient, where `PPPP` is a four-digit patient number. The landmarks subdirectory
has one `PPPP\_LANDMARKS.fcsv` file for each of the same patient numbers.

The FilteredControlBlindingLogUniqueScanFiltered.xls file of clinical data by
patient and the image files must be supplied. The landmarks files must be
pre-computed prior to running these pipelines. The directory we are using in
this example has inputs for two patients, 1127 and 1129.

<img src="./media/image1.png" style="width:6.5in;height:3.52778in" />

Click on the "..." button that is to the right of "Input/Output Root Directory."

<img src="./media/image23.png" style="width:6.5in;height:3.94444in" />

Use the dialog box to select the directory that contains your inputs. Click the
"Choose" button.

<img src="./media/image26.png" style="width:6.5in;height:4.48611in" />

You are returned to the VPAW Model screen. Next you need to specify the
directory that contains the model parameters that the pipeline should use when
processing the input data. The directory should contain a single file with a
name like "116(158.10-38.AM.24.Mar).pth".

<img src="./media/image27.png" style="width:6.5in;height:1.91667in" />

Click on the "..." button that is to the right of "Models Directory."

<img src="./media/image9.png" style="width:6.5in;height:3.94444in" />

Use the dialog box to select the directory that contains your model file. Click
the "Choose" button.

<img src="./media/image4.png" style="width:6.5in;height:4.48611in" />

You are returned to the VPAW Model screen.

<img src="./media/image13.png" style="width:6.5in;height:3.94444in" />

Optionally specify a patient number. If you leave this blank, all patients are
processed. In this example, we specify patient 1127. Whether or not you specify
a patient number, click on the "Run Pediatric Airway Atlas" button.

<img src="./media/image22.png" style="width:6.5in;height:3.94444in" />

After the Pediatric Airway Atlas pipeline has completed, you see a dialog box
indicating that. Click on the "OK" button.

<img src="./media/image2.png"
style="width:2.35417in;height:1.20833in" />

You are returned to the VPAW Model screen. An examination of the input/output
directory now shows both the inputs and the newly generated outputs.

<img src="./media/image5.png" style="width:6.5in;height:9.11111in" />

# The VPAW Visualize module

To look at the inputs and outputs, we use the VPAW Visualize screen. Click on
the "Go to VPAW Visualize module" button near the upper left corner.

<img src="./media/image22.png" style="width:6.5in;height:3.94444in" />

You are taken to the VPAW Visualize screen. To visualize the data just analyzed
by the pipeline or any previous dataset, we enter the location of the dataset.
Click on the "..." button that is to the right of "Data directory."

<img src="./media/image28.png" style="width:6.5in;height:3.94444in" />

Use the dialog box to select the directory that contains your data to be
visualized. Click the "Choose" button.

<img src="./media/image3.png" style="width:6.5in;height:4.48611in" />

You are returned to the VPAW Visualize screen.

<img src="./media/image12.png" style="width:6.5in;height:3.94444in" />

Specify the patient number for the data you wish to visualize. In this example,
we specify patient 1127. Click on the "Show" button.

<img src="./media/image11.png" style="width:6.5in;height:3.94444in" />

The VPAW Visualize page now lists a number of data features that can be
visualized. Click on the "Compute Isosurfaces" button to generate a model node
consisting of isosurfaces of the Laplace solution image.

<img src="./media/image20.png" style="width:6.5in;height:3.94444in" />

Notice the letters "S" (red), "A" (green), and "L" (yellow) to the right of the
corresponding sliders in the main viewing panels, which indicate superior,
anterior, and left. You adjust the red, green, and yellow sliders to specify
which axial plane (inferior to superior), coronal plane (posterior to anterior),
and sagittal plane (right to left) of the data are displayed. Toggle the
visibility of each element in the scene by toggling the eye icon in the second
column of the list of inputs and outputs.

<img src="./media/image19.png" style="width:6.5in;height:3.94444in" />

Let’s tour through the elements one at a time. Looking at just the landmarks
"`1127_LANDMARKS`" shows this information.

<img src="./media/image16.png" style="width:6.5in;height:3.94444in" />

Looking at just the input CT scan "`1127_INPUT`" shows this information.

<img src="./media/image24.png" style="width:6.5in;height:3.94444in" />

Looking at just the airway segmentation "`Segment_1`" shows this information.

<img src="./media/image30.png" style="width:6.5in;height:3.94444in" />

Looking at just "`1127_MARKED`" shows this information.

<img src="./media/image14.png" style="width:6.5in;height:3.94444in" />

Looking at just "`1127_UNITIZED_SEGMENTATIONS`" shows this information.

<img src="./media/image15.png" style="width:6.5in;height:3.94444in" />

Looking at just the Laplace solution "`1127_SOL`" shows this information.

<img src="./media/image17.png" style="width:6.5in;height:3.94444in" />

Looking at just the restricted Laplace solution
"`1127_SOLrestrictedToSegmentation`" shows this information.

<img src="./media/image25.png" style="width:6.5in;height:3.94444in" />

Looking at just the airway centerline "`Centerline`" shows this information.

<img src="./media/image10.png" style="width:6.5in;height:3.94444in" />

The combination of several visualizations produces rich images.

<img src="./media/image19.png" style="width:6.5in;height:3.94444in" />
