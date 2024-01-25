/*==============================================================================

  Copyright (c) Kitware, Inc.

  See http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Jean-Christophe Fillion-Robin, Kitware, Inc.
  and was partially funded by NIH grant 3P41RR013218-12S1

==============================================================================*/
// Qt includes
#include <QFile>

// vpaw includes
#include "qvpawAppMainWindow.h"
#include "Widgets/qAppStyle.h"

// Slicer includes
#include "qSlicerApplication.h"
#include "qSlicerApplicationHelper.h"
#include "vtkSlicerConfigure.h" // For Slicer_MAIN_PROJECT_APPLICATION_NAME
#include "vtkSlicerVersionConfigure.h" // For Slicer_MAIN_PROJECT_VERSION_FUL
#include "vtkMRMLLinearTransformNode.h"
#include "vtkMRMLModelNode.h"
#include "vtkMRMLScene.h"

// VTK Includes
#include "vtkPLYReader.h"

namespace
{

//----------------------------------------------------------------------------
int
SlicerAppMain(int argc, char * argv[])
{
  typedef qvpawAppMainWindow SlicerMainWindowType;

  qSlicerApplicationHelper::preInitializeApplication(argv[0], new qAppStyle);

  qSlicerApplication app(argc, argv);
  if (app.returnCode() != -1)
  {
    return app.returnCode();
  }

  QScopedPointer<SlicerMainWindowType> window;
  QScopedPointer<QSplashScreen>        splashScreen;

  qSlicerApplicationHelper::postInitializeApplication<SlicerMainWindowType>(app, splashScreen, window);

  if (!window.isNull())
  {
    QString windowTitle =
      QString("%1 %2").arg(Slicer_MAIN_PROJECT_APPLICATION_NAME).arg(Slicer_MAIN_PROJECT_VERSION_FULL);
    window->setWindowTitle(windowTitle);
  }

  // Load default haptic probe model from resource file.
  QFile file(":/cylinder.ply");
  if (file.open(QIODevice::ReadOnly) && app.mrmlScene())
  {
    auto bytes = file.readAll();

    vtkNew<vtkPLYReader> reader;
    reader->SetInputString(bytes.toStdString());
    reader->ReadFromInputStringOn();
    reader->Update();

    if (reader->GetErrorCode() == 0)
    {
      vtkNew<vtkMRMLModelNode> hapticProbe;
      hapticProbe->SetName("Model: Haptic Probe");
      app.mrmlScene()->AddNode(hapticProbe);
      hapticProbe->SetAndObserveMesh(reader->GetOutput());

      vtkNew<vtkMRMLLinearTransformNode> transformNode;
      transformNode->SetName("Transform: Haptic Probe");
      app.mrmlScene()->AddNode(transformNode);
      hapticProbe->SetAndObserveTransformNodeID(transformNode->GetID());
      hapticProbe->SetDisplayVisibility(true);
    }
  }

  return app.exec();
}

} // end of anonymous namespace

#include "qSlicerApplicationMainWrapper.cxx"
