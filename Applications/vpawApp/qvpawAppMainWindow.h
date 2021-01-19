/*==============================================================================

  Copyright (c) Kitware, Inc.

  See http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Julien Finet, Kitware, Inc.
  and was partially funded by NIH grant 3P41RR013218-12S1

==============================================================================*/

#ifndef __qvpawAppMainWindow_h
#define __qvpawAppMainWindow_h

// vpaw includes
#include "qvpawAppExport.h"
class qvpawAppMainWindowPrivate;

// Slicer includes
#include "qSlicerMainWindow.h"

class Q_VPAW_APP_EXPORT qvpawAppMainWindow : public qSlicerMainWindow
{
  Q_OBJECT
public:
  typedef qSlicerMainWindow Superclass;

  qvpawAppMainWindow(QWidget *parent=0);
  virtual ~qvpawAppMainWindow();

public slots:
  void on_HelpAboutvpawAppAction_triggered();

protected:
  qvpawAppMainWindow(qvpawAppMainWindowPrivate* pimpl, QWidget* parent);

private:
  Q_DECLARE_PRIVATE(qvpawAppMainWindow);
  Q_DISABLE_COPY(qvpawAppMainWindow);
};

#endif
