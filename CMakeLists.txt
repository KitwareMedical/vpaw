cmake_minimum_required(VERSION 3.16.3)

# Enable C++14
if(NOT DEFINED CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set (EP_GIT_PROTOCOL "https")

# Slicer sources
include(FetchContent)
if(NOT DEFINED slicersources_SOURCE_DIR)
  # Download Slicer sources and set variables slicersources_SOURCE_DIR and slicersources_BINARY_DIR
  FetchContent_Populate(slicersources
    GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/Slicer/Slicer
    GIT_TAG        955326ccbd0a7855a776a4da9d458f24fc2306f3  # Oct 27, 2021
    GIT_PROGRESS   1
    )
else()
  set(slicersources_BINARY_DIR ${CMAKE_CURRENT_BINARY_DIR}/slicersources-subbuild)
endif()

# macOS initialization
set(CMAKE_MODULE_PATH ${slicersources_SOURCE_DIR}/CMake ${CMAKE_MODULE_PATH})
include(SlicerInitializeOSXVariables)

project(vpaw)

# Configure Application
set(Slicer_APPLICATIONS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/Applications)
set(Slicer_MAIN_PROJECT "vpawApp")

# Set organization
set(Slicer_ORGANIZATION_DOMAIN "kitware.com")
set(Slicer_ORGANIZATION_NAME   "Kitware, Inc.")

# Default home and favorite modules
set(Slicer_DEFAULT_HOME_MODULE "Home")
set(Slicer_DEFAULT_FAVORITE_MODULES "Data, Volumes, Models, Transforms, Markups, SegmentEditor")

# Configure SuperBuild
set(SUPERBUILD_TOPLEVEL_PROJECT Slicer)
set(EXTERNAL_PROJECT_ADDITIONAL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild")
include(ExternalProjectDependency)

# Additional Slicer dependencies looked up in EXTERNAL_PROJECT_ADDITIONAL_DIR
set(Slicer_ADDITIONAL_DEPENDENCIES
  )

#  Enable listed remote modules from ITK
set(Slicer_ITK_ADDITIONAL_MODULES
  )

if(NOT CMAKE_CONFIGURATION_TYPES)
  set(Slicer_DEFAULT_BUILD_TYPE "Release")
endif()
include(SlicerInitializeBuildType)
include(SlicerInitializeReleaseType)

# Set application bundle identifier for macOS
if(APPLE)
  set(Slicer_MACOSX_BUNDLE_GUI_IDENTIFIER "com.kitware.vpaw")
endif()

# Installation folder and admin account requirement for Windows
if(WIN32)
  # Note: To avoid escaping issue, make sure to use forward slash when setting
  #       "Slicer_CPACK_NSIS_INSTALL_ROOT". It is replaced by "\\\\" in SlicerCPack.
  set(Slicer_CPACK_NSIS_INSTALL_REQUIRES_ADMIN_ACCOUNT ON)
  if(Slicer_CPACK_NSIS_INSTALL_REQUIRES_ADMIN_ACCOUNT)
    # User has administrative privileges, therefore we can install to shared folder
    # "C:\Program Files" or "C:\Program Files (x86)".
    if(CMAKE_CL_64)
      set(Slicer_CPACK_NSIS_INSTALL_ROOT "$PROGRAMFILES64")
    else()
      set(Slicer_CPACK_NSIS_INSTALL_ROOT "$PROGRAMFILES")
    endif()
  else()
    # We do not require administrative privileges, therefore we install to user folder
    # "C:\Users\<username>\AppData\Local".
    set(Slicer_CPACK_NSIS_INSTALL_ROOT "$LOCALAPPDATA/${Slicer_ORGANIZATION_NAME}")
  endif()
endif()

# Slicer options
option(BUILD_TESTING                            "Build application test suite"                        ON)
option(Slicer_BUILD_DOCUMENTATION               "Build documentation (Doxygen, sphinx, ...)"          OFF)
if(WIN32)
  option(Slicer_BUILD_WIN32_CONSOLE_LAUNCHER    "Build ${PROJECT_NAME} launcher executable as a console app on windows (displays console at application start)" OFF)
  option(Slicer_BUILD_WIN32_CONSOLE             "Build application executable as a console app (allows capturing and piping console output)" ON)
endif()

option(Slicer_BUILD_DICOM_SUPPORT               "Build application with DICOM support"                ON)
option(Slicer_BUILD_DIFFUSION_SUPPORT           "Build application with Diffusion support"            OFF)
option(Slicer_BUILD_EXTENSIONMANAGER_SUPPORT    "Build application with ExtensionManager support"     OFF)
option(Slicer_BUILD_MULTIVOLUME_SUPPORT         "Build application with MultiVolume support"          OFF)
option(Slicer_BUILD_PARAMETERSERIALIZER_SUPPORT "Build application with parameter serializer support" OFF)
option(Slicer_USE_PYTHONQT                      "Build application with Python support"               ON)
option(Slicer_USE_QtTesting                     "Build application with QtTesting support"            OFF)
option(Slicer_USE_SimpleITK                     "Build application with SimpleITK support"            OFF)

option(Slicer_BUILD_BRAINSTOOLS                 "Build application with BRAINSTools module"           OFF)
option(Slicer_BUILD_DataStore                   "Build application with DataStore module"             OFF)
option(Slicer_BUILD_CompareVolumes              "Build application with ChangeTrackerPy module"       OFF)
option(Slicer_BUILD_LandmarkRegistration        "Build application with LandmarkRegistration module"  OFF)
option(Slicer_BUILD_SurfaceToolbox              "Build application with SurfaceToolbox module"        OFF)

# Enable Slicer built-in modules
set(Slicer_CLIMODULES_ENABLED
  ResampleDTIVolume             # Needed by ResampleScalarVectorDWIVolume
  ResampleScalarVectorDWIVolume # Depends on DiffusionApplications, needed by CropVolume
  )
set(Slicer_QTLOADABLEMODULES_ENABLED
  )
set(Slicer_QTSCRIPTEDMODULES_ENABLED
  )

# Disable Slicer built-in modules
set(Slicer_CLIMODULES_DISABLED
  )
set(Slicer_QTLOADABLEMODULES_DISABLED
  SceneViews
  SlicerWelcome
  ViewControllers
  )
set(Slicer_QTSCRIPTEDMODULES_DISABLED
  DataProbe
  DMRIInstall
  Endoscopy
  LabelStatistics
  PerformanceTests
  SampleData
  VectorToScalarVolume
  )

# Enable/Disable Slicer custom modules: To create a new module, use the SlicerExtensionWizard.
set(Slicer_EXTENSION_SOURCE_DIRS
  #${vpaw_SOURCE_DIR}/Modules/CLI/MyCLIModule
  #${vpaw_SOURCE_DIR}/Modules/Loadable/MyLoadableModule
  #${vpaw_SOURCE_DIR}/Modules/Scripted/Home
  )

# Add remote extension source directories

# SlicerOpenIGTLink
#set(extension_name "SlicerOpenIGTLink")
#set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
#FetchContent_Populate(${extension_name}
#  SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
#  GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/openigtlink/SlicerOpenIGTLink.git
#  GIT_TAG        2b92f7b1ffe02403109b671f28424e8770e902a0
#  GIT_PROGRESS   1
#  QUIET
#  )
#list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR})

#SlicerMorph modules
set(extension_name "SlicerMorph")
set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
FetchContent_Populate(${extension_name}
 SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
 GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/andinet/SlicerMorph.git
 GIT_TAG        0ab0dfabdee835ccf1a4b256b092885622388e34
 GIT_PROGRESS   1
 QUIET
 )
list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR})

#FlyThrough modules
set(extension_name "FlyThrough")
set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
FetchContent_Populate(${extension_name}
 SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
 GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/andinet/FlyThrough.git
 GIT_TAG        5761298cb1bfa602a86ba4fb6b0c29115e1b092a
 GIT_PROGRESS   1
 QUIET
 )
list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR})

#SlicerIMSTK
set(extension_name "SlicerIMSTK")
set(${extension_name}_SOURCE_DIR "${CMAKE_BINARY_DIR}/${extension_name}")
FetchContent_Populate(${extension_name}
 SOURCE_DIR     ${${extension_name}_SOURCE_DIR}
 GIT_REPOSITORY ${EP_GIT_PROTOCOL}://github.com/KitwareMedical/SlicerIMSTK.git
 GIT_TAG        bf910e42c9b98bd94678f496a3212c2f2432b785
 GIT_PROGRESS   1
 QUIET
 )
message(STATUS "Remote - ${extension_name} [OK]")
list(APPEND Slicer_EXTENSION_SOURCE_DIRS ${${extension_name}_SOURCE_DIR})

include(${SlicerIMSTK_SOURCE_DIR}/SuperBuildPrerequisites.cmake)

# Add Slicer sources
add_subdirectory(${slicersources_SOURCE_DIR} ${slicersources_BINARY_DIR})
