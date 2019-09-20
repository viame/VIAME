###
# top level build file for NOAA VIAME
#

cmake_minimum_required( VERSION 3.11.4 )
set( CMAKE_CXX_STANDARD 11 )

project( VIAME )

set( VIAME_VERSION_MAJOR 1 )
set( VIAME_VERSION_MINOR 0 )
set( VIAME_VERSION_PATCH 0 )

set( VIAME_VERSION "${VIAME_VERSION_MAJOR}.${VIAME_VERSION_MINOR}.${VIAME_VERSION_PATCH}" )

include( CMakeDependentOption )


# If VIAME_FORCEBUILD is False, we will assume we dont need to rebuild any other superbuild
# projects (except for viame). This makes development builds much quicker if just doing
# development only in viame.
option( VIAME_FORCEBUILD "Enable force-building of all subpackages" ON )
mark_as_advanced( VIAME_FORCEBUILD )

###
# Add paths used throughout CMakeLists files
##
list( INSERT CMAKE_MODULE_PATH 0    "${CMAKE_CURRENT_SOURCE_DIR}/cmake" "${KWIVER_CMAKE_DIR}" )

set( VIAME_SOURCE_DIR               "${CMAKE_SOURCE_DIR}" )
set( VIAME_CMAKE_DIR                "${CMAKE_SOURCE_DIR}/cmake" )
set( VIAME_BINARY_DIR               "${CMAKE_BINARY_DIR}/build" )
set( VIAME_BUILD_PREFIX             "${CMAKE_BINARY_DIR}/build" )
set( VIAME_BUILD_INSTALL_PREFIX     "${CMAKE_BINARY_DIR}/install"
     CACHE STRING                   "Installation directory to place all final output files" )
mark_as_advanced( VIAME_BUILD_INSTALL_PREFIX )
set( CMAKE_INSTALL_PREFIX           "${VIAME_BUILD_INSTALL_PREFIX}" )

set( VIAME_PACKAGES_DIR             "${VIAME_SOURCE_DIR}/packages" )
set( VIAME_DOWNLOAD_DIR             "${VIAME_PACKAGES_DIR}/downloads" )

###
# GPU and FFMPEG utilization flags used across projects
##
option( VIAME_ENABLE_CUDA           "Enable CUDA-Dependent Code"    ON )
option( VIAME_ENABLE_CUDNN          "Enable CUDNN-Dependent Code"   ON )
option( VIAME_ENABLE_FFMPEG         "Enable FFMPEG-Dependent Code"  ON )

###
# Add core utilities enable flags
##
option( VIAME_ENABLE_DOCS           "Enable Documentation"          OFF )
option( VIAME_ENABLE_VIVIA          "Enable Vivia GUIs"             ON )
option( VIAME_ENABLE_SEAL_TK        "Enable Seal-TK GUIs"           OFF )
option( VIAME_ENABLE_FLASK          "Enable Flask GUIs"             OFF )
option( VIAME_ENABLE_KWANT          "Enable KW Scoring Code"        ON )

mark_as_advanced( VIAME_ENABLE_SEAL_TK )
mark_as_advanced( VIAME_ENABLE_FLASK )

###
# Add default-enabled algorithmic plugin enable flags
##
option( VIAME_ENABLE_VXL            "Enable VXL plugins"            ON )
option( VIAME_ENABLE_OPENCV         "Enable OpenCV plugins"         ON )
option( VIAME_ENABLE_PYTHON         "Enable Python plugins"         ON )
option( VIAME_ENABLE_PYTORCH        "Enable PyTorch plugins"        ON )
option( VIAME_ENABLE_YOLO           "Enable YOLO (darknet) plugin"  ON )
option( VIAME_ENABLE_SMQTK          "Enable SMQTK plugins"          ON )

###
# Add secondary plugin enable flags
##
option( VIAME_ENABLE_CAFFE          "Enable Caffe plugins"          OFF )
option( VIAME_ENABLE_ITK            "Enable ITK plugins"            OFF )
option( VIAME_ENABLE_TENSORFLOW     "Enable TensorFlow plugins"     OFF )
option( VIAME_ENABLE_MATLAB         "Enable Matlab plugins"         OFF )
option( VIAME_ENABLE_SCALLOP_TK     "Enable ScallopTK plugin"       OFF )
option( VIAME_ENABLE_UW_PREDICTOR   "Enable UW predictor plugin"    OFF )
option( VIAME_ENABLE_BURNOUT        "Enable Burn-Out plugins"       OFF )
option( VIAME_ENABLE_CAMTRAWL       "Enable Camtrawl plugin"        OFF )

mark_as_advanced( VIAME_ENABLE_CAFFE )
mark_as_advanced( VIAME_ENABLE_BURNOUT )
mark_as_advanced( VIAME_ENABLE_ITK )
mark_as_advanced( VIAME_ENABLE_UW_PREDICTOR )

###
# Add assorted other enable flags
##
option( VIAME_ENABLE_GDAL           "Enable GDAL image source"      OFF )
mark_as_advanced( VIAME_ENABLE_GDAL )

###
# Flags relating to examples
##
option( VIAME_INSTALL_EXAMPLES      "Install existing VIAME examples"     ON )
option( VIAME_DOWNLOAD_MODELS       "Download example detection models"   ON )

if( VIAME_DOWNLOAD_MODELS )
  option( VIAME_DOWNLOAD_MODELS-HABCAM      "Download habcam detection models" OFF )
  option( VIAME_DOWNLOAD_MODELS-MOUSS       "Download mouss detection models"  OFF )
  option( VIAME_DOWNLOAD_MODELS-PYTORCH     "Download default pytorch models"  ON )
  option( VIAME_DOWNLOAD_MODELS-ARCTIC-SEAL "Download seal detection models"   OFF )

  mark_as_advanced( VIAME_DOWNLOAD_MODELS-HABCAM )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-MOUSS )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-PYTORCH )
  mark_as_advanced( VIAME_DOWNLOAD_MODELS-ARCTIC-SEAL )
else()
  set( VIAME_DOWNLOAD_MODELS-HABCAM      OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-MOUSS       OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-PYTORCH     OFF CACHE BOOL "Forced off" FORCE )
  set( VIAME_DOWNLOAD_MODELS-ARCTIC-SEAL OFF CACHE BOOL "Forced off" FORCE )
endif()

###
# Advanced hidden flags used for disabling core features
#
# These are meant for use by advanced users when you only want to use VIAME
# to build one of the above packages by itself, not VIAME core.
##
option( VIAME_ENABLE_KWIVER         "Enable KWIVER pipelining"      ON )
option( VIAME_ENABLE_VIAME_PLUGINS  "Enable VIAME plugins"          ON )

mark_as_advanced( VIAME_ENABLE_KWIVER )
mark_as_advanced( VIAME_ENABLE_VIAME_PLUGINS )

###
# Add external package build instructions
##
option( VIAME_BUILD_DEPENDENCIES    "Build all required dependencies in a super-build" ON )
option( VIAME_CREATE_PACKAGE        "Build a binary package at the end of build"       OFF )
mark_as_advanced( VIAME_CREATE_PACKAGE )

###
# Add extra options
##
option( VIAME_BUILD_CORE_IMAGE_LIBS "Build core image libraries such as libtiff and libjpeg" ON )
mark_as_advanced( VIAME_BUILD_CORE_IMAGE_LIBS )

option( VIAME_BUILD_TESTS "Build VIAME and all sub-packages with tests enabled" OFF )
mark_as_advanced( VIAME_BUILD_TESTS )

###
# Add logic relating to enable flags
##
if( VIAME_ENABLE_CAFFE OR VIAME_ENABLE_SCALLOP_TK OR VIAME_ENABLE_BURNOUT OR
    VIAME_ENABLE_YOLO )
  set( VIAME_ENABLE_OPENCV  ON CACHE BOOL "OpenCV required for other projects"   FORCE )
endif()

if( VIAME_ENABLE_KWANT OR VIAME_ENABLE_BURNOUT OR VIAME_ENABLE_VIVIA OR
    VIAME_ENABLE_ITK )
  set( VIAME_ENABLE_VXL     ON CACHE BOOL "VXL required for other projects"      FORCE )
endif()

if( VIAME_ENABLE_SMQTK OR VIAME_ENABLE_PYTORCH OR VIAME_ENABLE_TENSORFLOW OR
    VIAME_ENABLE_SEAL_TK )
  set( VIAME_ENABLE_PYTHON  ON CACHE BOOL "Python required for other projects"   FORCE )
endif()

if( VIAME_ENABLE_MATLAB )
  find_package( Matlab REQUIRED COMPONENTS ENG_LIBRARY MX_LIBRARY )
endif()

if( VIAME_ENABLE_DOCS )
  find_package( Doxygen REQUIRED )
endif()

if( VIAME_ENABLE_PYTHON )
  option( VIAME_DISABLE_PYTHON_CHECK   "Disable python version checking" OFF )
  mark_as_advanced( VIAME_DISABLE_PYTHON_CHECK )

  if( NOT WIN32 )
    option( VIAME_SYMLINK_PYTHON "Symlink python files instead of copying." OFF )
    mark_as_advanced( VIAME_SYMLINK_PYTHON )
  endif()
  set( KWIVER_SYMLINK_PYTHON ${VIAME_SYMLINK_PYTHON} )

  find_package( PythonInterp REQUIRED )
  find_package( PythonLibs REQUIRED )

  if( NOT ${VIAME_DISABLE_PYTHON_CHECK} AND
      NOT EXISTS ${PYTHON_INCLUDE_DIR}/pyconfig.h )
    message( FATAL_ERROR "pyconfig.h does not exist in your PYTHON_INCLUDE_DIR \
      make sure the variable is set correctly and you have python-dev installed." )
  endif()

  set( PYTHON_VERSION "${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}"
       CACHE STRING "Python version number" )
endif()

if( VIAME_ENABLE_VIVIA AND VIAME_ENABLE_SEAL_TK )
  message( FATAL_ERROR "Cannot yet enable both VIVIA and Seal-TK GUIs" )
endif()

# VXL enabled triggers yasm to be built, requiring at least some python
if( VIAME_ENABLE_VXL )
  find_package( PythonInterp QUIET )
  if( NOT PYTHONINTERP_FOUND )
    message( FATAL_ERROR "If VXL is enabled, there must be some python install located \
      on the system to build, even if VIAME_ENABLE_PYTHON is turned off for all other \
      packages. A python binary could not be found. Please install at least python." )
  endif()
endif()

if( VIAME_ENABLE_CUDA )
  find_package( CUDA QUIET REQUIRED )

  if( CUDA_VERSION_MAJOR GREATER_EQUAL 10 AND NOT CUDA_cublas_device_LIBRARY )
    set( CUDA_cublas_device_LIBRARY CACHE INTERNAL "${CUDA_cublas_LIBRARY}" )
  endif()

  if( CUDA_VERSION_MAJOR GREATER_EQUAL 10 AND VIAME_ENABLE_CAFFE )
    message( FATAL_ERROR "Caffe does not support CUDA 10 or above" )
  endif()

  option( VIAME_FORCE_CUDA_CSTD98 "Build all cuda code with C++ standard 98" FALSE )
  mark_as_advanced( VIAME_FORCE_CUDA_CSTD98 )
else()
  set(VIAME_FORCE_CUDA_CSTD98 CACHE INTERNAL FALSE)
endif()

if( VIAME_ENABLE_CUDNN AND NOT VIAME_ENABLE_CUDA )
  message( FATAL_ERROR "Cannot enable CUDNN without CUDA support" )
endif()

if( VIAME_ENABLE_CUDNN )
  set( CUDNN_ROOT_DIR "" CACHE PATH "CUDNN root folder, leave as blank to auto-detect." )

  find_library( CUDNN_LIBRARY REQUIRED
    NAMES cudnn libcudnn.so libcudnn.so.8 libcudnn.so.7 libcudnn.so.6
    HINTS ${CUDNN_ROOT_DIR}
          ${CUDA_TOOLKIT_ROOT_DIR}/targets/aarch64-linux
          ${CUDA_TOOLKIT_ROOT_DIR}
    PATH_SUFFIXES lib lib64 )

  if( NOT CUDNN_LIBRARY )
    message( FATAL_ERROR "Unable to locate CUDNN library" )
  endif()

  # Different subprojects use each variable
  set( CUDNN_LIBRARIES "${CUDNN_LIBRARY}" CACHE INTERNAL "" FORCE )

  # Check version of CUDNN
  get_filename_component( CUDNN_ROOT_DIR_TMP "${CUDNN_LIBRARY}" DIRECTORY )
  get_filename_component( CUDNN_ROOT_DIR_TMP "${CUDNN_ROOT_DIR_TMP}" DIRECTORY )

  set( CUDNN_ROOT_DIR "${CUDNN_ROOT_DIR_TMP}" CACHE INTERNAL "CUDNN root folder" FORCE )
  set( CUDNN_INCLUDE_FILE "${CUDNN_ROOT_DIR}/include/cudnn.h" CACHE INTERNAL "" FORCE )

  if( NOT EXISTS ${CUDNN_INCLUDE_FILE} AND WIN32 )
    get_filename_component( CUDNN_ROOT_DIR_TMP "${CUDNN_ROOT_DIR_TMP}" DIRECTORY )

    set( CUDNN_ROOT_DIR "${CUDNN_ROOT_DIR_TMP}" CACHE INTERNAL "CUDNN root folder" FORCE )
    set( CUDNN_INCLUDE_FILE "${CUDNN_ROOT_DIR}/include/cudnn.h" CACHE INTERNAL "" FORCE )
  endif()

  if( EXISTS "${CUDNN_INCLUDE_FILE}" )
    file( READ "${CUDNN_INCLUDE_FILE}" TMP_CUDNN_VERSION_FILE_CONTENTS )

    string( REGEX MATCH "define CUDNN_MAJOR * +([0-9]+)"
            CUDNN_VERSION_MAJOR "${TMP_CUDNN_VERSION_FILE_CONTENTS}" )
    string( REGEX REPLACE "define CUDNN_MAJOR * +([0-9]+)" "\\1"
            CUDNN_VERSION_MAJOR "${CUDNN_VERSION_MAJOR}" )
  endif()
endif()

if( WIN32 AND VIAME_ENABLE_PYTHON AND CMAKE_CONFIGURATION_TYPES EQUAL "Debug" )
  message( FATAL_ERROR "Cannot build in Debug on Windows with Python enabled, \
    build in RelWithDebInfo or Release until fixed." )
endif()

if( VIAME_ENABLE_OPENCV )
  set( VIAME_OPENCV_VERSION 3.4.0 CACHE STRING "Version of OpenCV to use" )
  set_property( CACHE VIAME_OPENCV_VERSION PROPERTY STRINGS 2.4.13 3.4.0 )

  # Version 2.4.11 no longer present fletch
  if( ${VIAME_OPENCV_VERSION} EQUAL "2.4.11" )
    set( VIAME_OPENCV_VERSION "2.4.13" CACHE STRING "Version of OpenCV to use" FORCE )
  endif()
endif()

# Set default windows configuration mode to be 'Release'
set( VIAME_FIRST_CONFIGURATION TRUE CACHE BOOL "Has this project been configured." )
mark_as_advanced( VIAME_FIRST_CONFIGURATION )

if( MSVC AND VIAME_FIRST_CONFIGURATION )
  set( CMAKE_CONFIGURATION_TYPES "Release" CACHE STRING "This specifies what \
    build types (configurations) will be available for selection within \
	Visual Studio. Options are: Release, RelWithDebInfo, Debug etc. in a \
	semi-colon seperated list." FORCE )

  set( VIAME_FIRST_CONFIGURATION FALSE CACHE BOOL "Project has been configured." FORCE )
endif()

if( MSVC AND CMAKE_CXX_COMPILER_VERSION VERSION_LESS "18.00" )
  message( FATAL_ERROR "You must use at least MSVC version 13 or greater" )
endif()
# if we have a 32 bit build, turn off Eigen alignment for more information see:
# http://eigen.tuxfamily.org/dox/group__TopicUnalignedArrayAssert.html
if( CMAKE_SIZEOF_VOID_P EQUAL 4 )
  set(CMAKE_CXX_FLAGS
    "${CMAKE_CXX_FLAGS} -DEIGEN_DONT_VECTORIZE -DEIGEN_DISABLE_UNALIGNED_ARRAY_ASSERT")
endif()

# Include internal common CMake macros used across all CMakeLists.txt
include( common_macros )

# Include checks across all prior versions of the code
include( old_version_checks )

###
# Main build loop for when we are building both VIAME and all dependencies
##
if( VIAME_BUILD_DEPENDENCIES )

  # Early error checking in case user did not run submodule init
  file( GLOB fletch_files ${VIAME_PACKAGES_DIR}/fletch/* )
  list( LENGTH fletch_files fletch_length )

  if( ${fletch_length} LESS 3 )
    message( FATAL_ERROR "Fletch directory empty, did you not run the following in your source tree: \n\
     git submodule update --init --recursive" )
  endif()

  # Include for CMake external project add command
  include( ExternalProject )

  # Specifies internal arguments passed to all projects (CXX flag passdowns, etc)
  include( common_args )

  # Hard VIAME requirements
  include( add_project_fletch )

  # Add optional projects
  if( VIAME_ENABLE_YOLO )
    include( add_project_darknet )
  endif()

  if( VIAME_ENABLE_BURNOUT )
    include( add_project_burnout )
  endif()

  if( VIAME_ENABLE_SMQTK )
    include( add_project_smqtk )
  endif()

  # Add core (required) kwiver requirement
  if( VIAME_ENABLE_KWIVER )
    include( add_project_kwiver )
  endif()

  # Add other optional libraries
  if( VIAME_ENABLE_SCALLOP_TK )
    include( add_project_scallop_tk )
  endif()

  if( VIAME_ENABLE_VIVIA )
    include( add_project_vivia )
  endif()

  if( VIAME_ENABLE_SEAL_TK )
    include( add_project_seal_tk )
  endif()

  if( VIAME_ENABLE_KWANT )
    include( add_project_kwant )
  endif()

  if( VIAME_ENABLE_PYTHON )
    include( add_project_python_deps )
  endif()

  if( VIAME_ENABLE_PYTORCH )
    include( add_project_pytorch )
  endif()

  if( WIN32 )
    include( add_project_postgres )
  endif()

  # VIAME plugins, adds this project causing the below else() block to run
  if( VIAME_ENABLE_VIAME_PLUGINS )
    include( add_project_viame )
  endif()

  # Fixup installer package
  if( VIAME_CREATE_PACKAGE )
    include( build_package )
  endif()
else()

  if( VIAME_ENABLE_FLASK )
    set(FT_DATA_ROOT "${CMAKE_BINARY_DIR}/data" CACHE STRING "Where fishtracker data is stored")
    file(COPY "plugins/flask"
         DESTINATION "plugins/flask"
         PATTERN "*.in" EXCLUDE)
    configure_file("plugins/flask/flask/fishtracker.py.in"
                   "plugins/flask/flask/fishtracker.py"
                   )
    configure_file("plugins/flask/Python/run_python_script.sh.in"
                   "plugins/flask/Python/run_python_script.sh"
                   )
  endif()

  ###
  # Look for and use Fletch to find dependencies
  ##
  find_package( kwiver REQUIRED )
  include_directories( ${KWIVER_INCLUDE_DIRS} )
  link_directories( ${KWIVER_LIBRARY_DIR} )
  list( INSERT CMAKE_MODULE_PATH  0         "${KWIVER_CMAKE_DIR}" )

  if( IS_DIRECTORY ${fletch_DIR} )
    find_package( fletch NO_MODULE )
    list( APPEND CMAKE_PREFIX_PATH  "${fletch_DIR}" )
  endif()

  if( VIAME_ENABLE_OPENCV )
    find_package( OpenCV REQUIRED )
  endif()

  include_directories( "${CMAKE_CURRENT_BINARY_DIR}" "${KWIVER_INCLUDE_DIRS}" )

  ###
  # KWIVER CMake config
  ##
  include( kwiver-cmake-future )
  include( kwiver-utils )

  ##
  # System specific compiler flags
  include( viame-flags )

  ##
  # Build system hack for visual system, will be removed
  include( windows-ksys-hack )

  ##
  # check compiler support
  include( kwiver-configcheck )

  # set the name for our package exports and plugin directories
  set( kwiver_export_name                           viame_exports )

  set( kwiver_plugin_subdir                         viame )
  set( kwiver_plugin_process_subdir                 ${kwiver_plugin_subdir}/processes )
  set( kwiver_plugin_process_instrumentation_subdir ${kwiver_plugin_subdir}/modules )
  set( kwiver_plugin_scheduler_subdir               ${kwiver_plugin_subdir}/processes )
  set( kwiver_plugin_module_subdir                  ${kwiver_plugin_subdir}/modules )
  set( kwiver_plugin_plugin_explorer_subdir         ${kwiver_plugin_subdir}/modules/plugin_explorer )
  set( kwiver_plugin_logger_subdir                  ${kwiver_plugin_subdir}/modules )

  # Setup python directories for plugin processes in same style as KWIVER
  if( VIAME_ENABLE_PYTHON )
    set( kwiver_python_subdir "python${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}" )
    set( kwiver_python_output_path "${VIAME_BUILD_PREFIX}/lib/${kwiver_python_subdir}" )

    kwiver_create_python_init( viame )
    kwiver_create_python_init( viame/processes )
  endif()

  ###
  # build submodules

  ###
  # add subdirs
  ##
  add_subdirectory( plugins )
  add_subdirectory( examples )
  add_subdirectory( configs )

  ###
  # Configure setup scripts
  ##
  include( setup_viame_paths )

  if( WIN32 )
    set( VIAME_PIPELINE_RUNNER_SCRIPT   "${VIAME_BINARY_DIR}/pipeline_runner.bat" )
    set( VIAME_PROCESSOPEDIA_SCRIPT     "${VIAME_BINARY_DIR}/processopedia.bat" )
    set( VIAME_PLUGIN_EXPLORER_SCRIPT   "${VIAME_BINARY_DIR}/plugin_explorer.bat" )
    set( VIAME_SETUP_SCRIPT             "${VIAME_BINARY_DIR}/setup_viame.bat" )

    configure_file(
      ${VIAME_CMAKE_DIR}/pipeline_runner.bat.in
      ${VIAME_PIPELINE_RUNNER_SCRIPT}
    )
    configure_file(
      ${VIAME_CMAKE_DIR}/processopedia.bat.in
      ${VIAME_PROCESSOPEDIA_SCRIPT}
    )
    configure_file(
      ${VIAME_CMAKE_DIR}/plugin_explorer.bat.in
      ${VIAME_PLUGIN_EXPLORER_SCRIPT}
    )
    configure_file(
      ${VIAME_CMAKE_DIR}/setup_viame.bat.in
      ${VIAME_SETUP_SCRIPT}
    )

    install( PROGRAMS      ${VIAME_PIPELINE_RUNNER_SCRIPT}
                           ${VIAME_PROCESSOPEDIA_SCRIPT}
                           ${VIAME_PLUGIN_EXPLORER_SCRIPT}
                           ${VIAME_SETUP_SCRIPT}
             DESTINATION   ${CMAKE_INSTALL_PREFIX} )

    if( VIAME_ENABLE_SEAL_TK )
      set( VIAME_SEAL_SCRIPT_FILE    "${VIAME_BINARY_DIR}/launch_seal_interface.bat" )

      configure_file(
        ${VIAME_CMAKE_DIR}/launch_seal_interface.bat.in
        ${VIAME_SEAL_SCRIPT_FILE}
      )

      install( PROGRAMS      ${VIAME_SEAL_SCRIPT_FILE}
               DESTINATION   ${CMAKE_INSTALL_PREFIX} )
    endif()
  else()
    set( VIAME_SETUP_SCRIPT_FILE    "${VIAME_BINARY_DIR}/setup_viame.sh" )

    configure_file(
      ${VIAME_CMAKE_DIR}/setup_viame.sh.in
      ${VIAME_SETUP_SCRIPT_FILE}
    )

    install( PROGRAMS      ${VIAME_SETUP_SCRIPT_FILE}
             DESTINATION   ${CMAKE_INSTALL_PREFIX} )

    if( VIAME_ENABLE_SEAL_TK )
      set( VIAME_SEAL_SCRIPT_FILE    "${VIAME_BINARY_DIR}/launch_seal_interface.sh" )

      configure_file(
        ${VIAME_CMAKE_DIR}/launch_seal_interface.sh.in
        ${VIAME_SEAL_SCRIPT_FILE}
      )

      install( PROGRAMS      ${VIAME_SEAL_SCRIPT_FILE}
               DESTINATION   ${CMAKE_INSTALL_PREFIX} )

    endif()
  endif()

  ###
  # Install system libs if packaging enabled
  ##
  if( VIAME_CREATE_PACKAGE )
    set( VIAME_RELEASE_NOTES_FILE "RELEASE_NOTES.md" )

    install( PROGRAMS      ${VIAME_RELEASE_NOTES_FILE}
             DESTINATION   ${CMAKE_INSTALL_PREFIX} )

    set( CMAKE_INSTALL_UCRT_LIBRARIES TRUE )
    include( InstallRequiredSystemLibraries )
    if( CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS )
      install( PROGRAMS ${CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS} DESTINATION bin COMPONENT System )
    endif()

    if( VIAME_ENABLE_CUDNN )
      install( FILES ${CUDNN_LIBRARY} DESTINATION lib )
    endif()

    if( WIN32 )
      set( PIPELINE_RUNNER_APP "pipeline_runner.exe" )
    else()
      set( PIPELINE_RUNNER_APP "pipeline_runner" )
    endif()

    if( VIAME_ENABLE_YOLO )
      if( WIN32 )
        set( DARKNET_APP "darknet.exe" )
      else()
        set( DARKNET_APP "darknet" )
      endif()
    else()
      set( DARKNET_APP )
    endif()

    if( VIAME_ENABLE_SEAL_TK )
      if( WIN32 )
        set( SEAL_TK_APP "sealtk.exe" )
      else()
        set( SEAL_TK_APP "sealtk" )
      endif()
    else()
      set( SEAL_TK_APP )
    endif()

    configure_file(
      ${VIAME_CMAKE_DIR}/viame-install-fixup.cmake.in
      ${CMAKE_BINARY_DIR}/viame-install-fixup.cmake
      @ONLY
      )
    install( SCRIPT ${CMAKE_BINARY_DIR}/viame-install-fixup.cmake )
  endif()
endif()
