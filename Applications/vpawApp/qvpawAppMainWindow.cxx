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

// vpaw includes
#include "qvpawAppMainWindow.h"
#include "qvpawAppMainWindow_p.h"

// Qt includes
#include <QDesktopWidget>
#include <QLabel>

// Slicer includes
#include "qSlicerApplication.h"
#include "qSlicerAboutDialog.h"
#include "qSlicerMainWindow_p.h"
#include "qSlicerModuleSelectorToolBar.h"

//-----------------------------------------------------------------------------
// qvpawAppMainWindowPrivate methods

qvpawAppMainWindowPrivate::qvpawAppMainWindowPrivate(qvpawAppMainWindow & object)
  : Superclass(object)
{}

//-----------------------------------------------------------------------------
qvpawAppMainWindowPrivate::~qvpawAppMainWindowPrivate() {}

//-----------------------------------------------------------------------------
void
qvpawAppMainWindowPrivate::init()
{
#if (QT_VERSION >= QT_VERSION_CHECK(5, 7, 0))
  QApplication::setAttribute(Qt::AA_UseHighDpiPixmaps);
#endif
  Q_Q(qvpawAppMainWindow);
  this->Superclass::init();
}

//-----------------------------------------------------------------------------
void
qvpawAppMainWindowPrivate::setupUi(QMainWindow * mainWindow)
{
  qSlicerApplication * app = qSlicerApplication::application();

  //----------------------------------------------------------------------------
  // Add actions
  //----------------------------------------------------------------------------
  QAction * helpAboutSlicerAppAction = new QAction(mainWindow);
  helpAboutSlicerAppAction->setObjectName("HelpAboutvpawAppAction");
  helpAboutSlicerAppAction->setText("About " + app->applicationName());

  //----------------------------------------------------------------------------
  // Calling "setupUi()" after adding the actions above allows the call
  // to "QMetaObject::connectSlotsByName()" done in "setupUi()" to
  // successfully connect each slot with its corresponding action.
  this->Superclass::setupUi(mainWindow);

  // Add Help Menu Action
  this->HelpMenu->addAction(helpAboutSlicerAppAction);

  //----------------------------------------------------------------------------
  // Configure
  //----------------------------------------------------------------------------
  mainWindow->setWindowIcon(QIcon(":/Icons/Medium/DesktopIcon.png"));

  QLabel * logoLabel = new QLabel();
  logoLabel->setObjectName("LogoLabel");
  logoLabel->setPixmap(qMRMLWidget::pixmapFromIcon(QIcon(":/LogoFull.png")));
  this->PanelDockWidget->setTitleBarWidget(logoLabel);

  // Hide the toolbars
  this->MainToolBar->setVisible(false);
  // this->ModuleSelectorToolBar->setVisible(false);
  this->ModuleToolBar->setVisible(false);
  this->ViewToolBar->setVisible(false);
  this->MouseModeToolBar->setVisible(false);
  this->CaptureToolBar->setVisible(false);
  this->ViewersToolBar->setVisible(false);
  this->DialogToolBar->setVisible(false);

  // Hide the menus
  // this->menubar->setVisible(false);
  // this->FileMenu->setVisible(false);
  // this->EditMenu->setVisible(false);
  // this->ViewMenu->setVisible(false);
  // this->LayoutMenu->setVisible(false);
  // this->HelpMenu->setVisible(false);

  // Hide the modules panel
  // this->PanelDockWidget->setVisible(false);
  this->DataProbeCollapsibleWidget->setCollapsed(true);
  this->DataProbeCollapsibleWidget->setVisible(false);
  this->StatusBar->setVisible(false);
}

//-----------------------------------------------------------------------------
// qvpawAppMainWindow methods

//-----------------------------------------------------------------------------
qvpawAppMainWindow::qvpawAppMainWindow(QWidget * windowParent)
  : Superclass(new qvpawAppMainWindowPrivate(*this), windowParent)
{
  Q_D(qvpawAppMainWindow);
  d->init();
}

//-----------------------------------------------------------------------------
qvpawAppMainWindow::qvpawAppMainWindow(qvpawAppMainWindowPrivate * pimpl, QWidget * windowParent)
  : Superclass(pimpl, windowParent)
{
  // init() is called by derived class.
}

//-----------------------------------------------------------------------------
qvpawAppMainWindow::~qvpawAppMainWindow() {}

//-----------------------------------------------------------------------------
void
qvpawAppMainWindow::on_HelpAboutvpawAppAction_triggered()
{
  qSlicerAboutDialog about(this);
  about.setLogo(QPixmap(":/Logo.png"));
  about.exec();
}
