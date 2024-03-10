VPAW by Kitware, Inc.
=====================

A Virtual Pediatric Airways Workbench (VPAW) is a patient-centered surgical planning software system targeted to pediatric patients with airway obstruction.

It aims to enable a full surgical planning pipeline for the evaluation of surgical outcomes. See [features][#Features] for more details.

This project contains the new generation of VPAW based on [3D Slicer](https://www.slicer.org/) and
it was created using the [Slicer Custom App Template](https://github.com/KitwareMedical/SlicerCustomAppTemplate).

_This project is in active development and may change from version to version without notice._

## Features

The project is being actively developed and our plan is to implement the following functionalities to enable users to express potential surgical treatment planning options for patients with airway obstruction.

A typical workflow will consist of the following steps:

* Importing computed tomography (CT) DICOM images
* Segmenting the airway (as described by _Hong et al_ [^1])
* Interactive 3D editing of airway geometries leveraging integration of 3D pointing devices such as [3D Systems Touch](https://www.3dsystems.com/haptics-devices/touch) through the OpenHaptics interface
* Creating input files for offline geometric analysis and Computational fluid dynamics (CFD) simulations

[^1]: See section 2.1 of Hong Y, Niethammer M, Andruejol J, Kimbell JS, Pitkin E, Superfine R, Davis S, Zdanski CJ, Davis B. A pediatric airway atlas and its application in subglottic stenosis. Proc IEEE Int Symp Biomed Imaging. 2013 Apr;2013:1206-1209. doi: [10.1109/ISBI.2013.6556697](https://dx.doi.org/10.1109/ISBI.2013.6556697). PMID: [26929791](https://pubmed.ncbi.nlm.nih.gov/26929791/); PMCID: [PMC4769591](http://www.ncbi.nlm.nih.gov/pmc/articles/pmc4769591/).

## Usage

This application is under development but can already be used to process and visualize CT scans if you have access to the private [pediatric_airway_atlas](https://github.com/uncbiag/pediatric_airway_atlas) research repository. [A guided tour can be found here.](doc/tour_VPAWModel_VPAWVisualize.md)

## Maintainers

* [Contributing](CONTRIBUTING.md)
* [Building](BUILD.md)

## History

The initial version of this project was developed between 2010 and 2015 in the context of supporting predictive modeling for treatment of upper airway obstruction in young children, the project as well as the team involved are respectively described and acknowledged in the [referenced](#how-to-cite) publication.

In 2022, the development of the next generation of VPAW based on [3D Slicer](https://www.slicer.org) was initiated.

## Acknowledgment

We gratefully acknowledge support from National Heart, Lung, and Blood Institute (NIH/NHLBI grant nos: 5R01HL105241 and 5R01HL154429), and National Health Institute of Dental and Craniofacial Research (NIH/NHIDC grant no: R43DE024334).

## License

This software is licensed under the terms of the [Apache License Version 2.0](LICENSE).

## How to cite ?

Quammen CW, Taylor RM 2nd, Krajcevski P, Mitran S, Enquobahrie A, Superfine R, Davis B, Davis S, Zdanski C. The Virtual Pediatric Airways Workbench. Stud Health Technol Inform. 2016;220:295-300. PMID: [27046595](https://pubmed.ncbi.nlm.nih.gov/27046595/); PMCID: [PMC5588666](http://www.ncbi.nlm.nih.gov/pmc/articles/pmc5588666/).

![vpaw by Kitware, Inc.](Applications/vpawApp/Resources/Images/LogoFull.png?raw=true)
