# Python Dependency External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

# --------------------- ADD ANY BASIC PYTHON DEPS HERE -------------------------
# Basic dependencies are installed jointly in one local pip installation call

set( PYTHON_DEP_ENV_VARS )

if( VIAME_CREATE_PACKAGE )
  set( VIAME_PYTHON_BASIC_DEPS "numpy==1.19.3" )
else()
  set( VIAME_PYTHON_BASIC_DEPS "numpy" )
endif()

list( APPEND VIAME_PYTHON_BASIC_DEPS "kiwisolver==1.2.0" "matplotlib==3.1.1" )

if( VIAME_ENABLE_TENSORFLOW )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "humanfriendly" )

  if( VIAME_ENABLE_CUDA )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "tensorflow-gpu==1.14" )
  else()
    list( APPEND VIAME_PYTHON_BASIC_DEPS "tensorflow==1.14" )
  endif()
endif()

if( VIAME_ENABLE_PYTORCH-INTERNAL )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "dataclasses" )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "yapf" )
endif()

if( VIAME_ENABLE_CAMTRAWL OR VIAME_ENABLE_OPENCV )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "tqdm" "scipy" )
endif()

if( ( WIN32 OR NOT VIAME_ENABLE_OPENCV ) AND
      ( VIAME_ENABLE_CAMTRAWL OR VIAME_ENABLE_OPENCV OR
        VIAME_ENABLE_PYTORCH-MMDET OR VIAME_ENABLE_PYTORCH-NETHARN ) )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "opencv-python" )
endif()

if( VIAME_ENABLE_ITK_EXTRAS )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "msgpack" )
endif()

if( VIAME_ENABLE_PYTORCH )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "scikit-image==0.16.2" )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET OR VIAME_ENABLE_PYTORCH-NETHARN )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "scikit-build" )
endif()

if( VIAME_ENABLE_PYTORCH-NETHARN AND VIAME_ENABLE_GDAL )
  if( WIN32 )
    list( APPEND VIAME_PYTHON_BASIC_DEPS "gdal==2.2.3" )
  else()
    list( APPEND VIAME_PYTHON_BASIC_DEPS "gdal" )
  endif()
endif()

if( VIAME_ENABLE_CAMTRAWL OR VIAME_ENABLE_PYTORCH-NETHARN )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "ubelt" "pygments" "bezier==2020.1.14" )
endif()

if( VIAME_ENABLE_PYTORCH AND VIAME_ENABLE_PYTORCH-INTERNAL )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "pyyaml" )
endif()

if( VIAME_ENABLE_PYTORCH AND VIAME_ENABLE_PYTORCH-MMDET AND NOT WIN32 )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "pycocotools" )
endif()

if( VIAME_ENABLE_PYTHON-INTERNAL AND UNIX )
  list( APPEND VIAME_PYTHON_BASIC_DEPS "backports.lzma" "backports.weakref" )
endif()

# ---------------------- ADD ANY ADV PYTHON DEPS HERE --------------------------
# Advanced python dependencies are installed individually due to special reqs

set( VIAME_PYTHON_ADV_DEPS python-deps )
set( VIAME_PYTHON_ADV_DEP_CMDS "custom-install" )

if( VIAME_ENABLE_ITK_EXTRAS )
  set( WX_VERSION "4.0.7" )

  list( APPEND VIAME_PYTHON_ADV_DEPS wxPython )

  if( UNIX )
    if( EXISTS "/etc/os-release" )
      ParseLinuxOSField( "ID" OS_ID )
    endif()

    execute_process( COMMAND lsb_release -cs
      OUTPUT_VARIABLE RELEASE_CODENAME
      OUTPUT_STRIP_TRAILING_WHITESPACE )

    if( "${OS_ID}" MATCHES "centos" )
      set( WXP_ARCHIVE https://extras.wxpython.org/wxPython4/extras/linux/gtk3/centos-7 )
      list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "-U -f ${WXP_ARCHIVE} wxPython==${WX_VERSION}" )
    elseif( "${RELEASE_CODENAME}" MATCHES "xenial" )
      set( WXP_ARCHIVE https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-16.04 )
      list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "-U -f ${WXP_ARCHIVE} wxPython==${WX_VERSION}" )
    else()
      list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "wxPython==${WX_VERSION}" )
    endif()
  else()
    list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "wxPython==${WX_VERSION}" )
  endif()
endif()

if( VIAME_ENABLE_PYTORCH AND NOT VIAME_ENABLE_PYTORCH-INTERNAL )
  list( APPEND VIAME_PYTHON_ADV_DEPS pytorch )

  set( ARGS_TORCH )

  set( PYTORCH_ARCHIVE https://download.pytorch.org/whl/torch_stable.html )
  set( PYTORCH_VERSION ${VIAME_PYTORCH_VERSION} )

  set( CUDA_VER_STR "" )
  set( TORCHVISION_STR "" )

  if( CUDA_VERSION VERSION_EQUAL "11.0" )
    set( CUDA_VER_STR "+cu110" )
  elseif( CUDA_VERSION VERSION_EQUAL "10.2" )
    set( CUDA_VER_STR "+cu102" )
  elseif( CUDA_VERSION VERSION_EQUAL "10.1" )
    set( CUDA_VER_STR "+cu101" )
  elseif( CUDA_VERSION VERSION_EQUAL "10.0" )
    set( CUDA_VER_STR "+cu100" )
  elseif( CUDA_VERSION VERSION_EQUAL "9.2" )
    set( CUDA_VER_STR "+cu92" )
  elseif( NOT VIAME_ENABLE_CUDA )
    set( CUDA_VER_STR "+cpu" )
  endif()

  if( NOT VIAME_ENABLE_PYTORCH-VIS-INTERNAL )
    if( PYTORCH_VERSION VERSION_EQUAL "1.7.1" )
      set( TORCHVISION_STR "torchvision==0.8.2${CUDA_VER_STR}" )
    elseif( PYTORCH_VERSION VERSION_EQUAL "1.6.0" )
      set( TORCHVISION_STR "torchvision==0.7.0${CUDA_VER_STR}" )
    elseif( PYTORCH_VERSION VERSION_EQUAL "1.4.0" )
      set( TORCHVISION_STR "torchvision==0.5.0${CUDA_VER_STR}" )
    endif()
  endif()

  # Default case
  set( ARGS_TORCH "==${PYTORCH_VERSION}${CUDA_VER_STR} ${TORCHVISION_STR} -f ${PYTORCH_ARCHIVE}" )

  # Special cases
  if( WIN32 AND VIAME_ENABLE_CUDA )
    if( CUDA_VERSION VERSION_EQUAL "10.1" )
      if( Python_VERSION VERSION_EQUAL 3.6 AND PYTORCH_VERSION VERSION_EQUAL "1.4.0" )
        set( ARGS_TORCH "https://download.pytorch.org/whl/cu101/torch-1.4.0-cp36-cp36m-win_amd64.whl" )
      else()
        set( ARGS_TORCH "===${PYTORCH_VERSION}${CUDA_VER_STR} ${TORCHVISION_STR} -f ${PYTORCH_ARCHIVE}" )
      endif()
    elseif( CUDA_VERSION VERSION_EQUAL "10.2" AND PYTORCH_VERSION VERSION_EQUAL "1.7.1" )
      set( ARGS_TORCH "==${PYTORCH_VERSION} ${TORCHVISION_STR} -f ${PYTORCH_ARCHIVE}" )
    elseif( NOT ( CUDA_VERSION VERSION_EQUAL "11.0" OR CUDA_VERSION VERSION_EQUAL "10.2" OR
                  CUDA_VERSION VERSION_EQUAL "10.1" OR CUDA_VERSION VERSION_EQUAL "9.2" ) )
      message( FATAL_ERROR "With your current build settings you must either:\n"
        " (a) Turn on VIAME_ENABLE_PYTORCH-INTERNAL\n"
        " (b) Use a CUDA version with premade torch (e.g. 9.2, 10.0, 10.1, 11.0)\n"
        " (c) Disable VIAME_ENABLE_PYTORCH\n" )
    endif()
  elseif( VIAME_ENABLE_CUDA )
    if( PYTORCH_VERSION VERSION_GREATER "1.6.0" AND CUDA_VERSION VERSION_EQUAL "11.0" )
      set( ARGS_TORCH "===${PYTORCH_VERSION}${CUDA_VER_STR} ${TORCHVISION_STR} -f ${PYTORCH_ARCHIVE}" )
    elseif( PYTORCH_VERSION VERSION_GREATER "1.5.0" AND CUDA_VERSION VERSION_EQUAL "10.2" )
      set( ARGS_TORCH "===${PYTORCH_VERSION} ${TORCHVISION_STR} -f ${PYTORCH_ARCHIVE}" )
    elseif( PYTORCH_VERSION VERSION_EQUAL "1.4.0" AND CUDA_VERSION VERSION_EQUAL "10.1" )
      set( ARGS_TORCH "===${PYTORCH_VERSION} ${TORCHVISION_STR} -f ${PYTORCH_ARCHIVE}" )
    elseif( PYTORCH_VERSION VERSION_GREATER "1.4.0" AND CUDA_VERSION VERSION_EQUAL "10.1" )
      set( ARGS_TORCH "===${PYTORCH_VERSION}${CUDA_VER_STR} ${TORCHVISION_STR} -f ${PYTORCH_ARCHIVE}" )
    elseif( NOT ( CUDA_VERSION VERSION_EQUAL "11.0" OR CUDA_VERSION VERSION_EQUAL "10.2" OR
                  CUDA_VERSION VERSION_EQUAL "10.1" OR CUDA_VERSION VERSION_EQUAL "9.2" ) )
      message( FATAL_ERROR "With your current build settings you must either:\n"
        " (a) Turn on VIAME_ENABLE_PYTORCH-INTERNAL\n"
        " (b) Use a CUDA version with premade torch (e.g. 9.2, 10.0, 10.1, 11.0)\n"
        " (c) Disable VIAME_ENABLE_PYTORCH\n" )
    endif()
  endif()

  string( FIND "${ARGS_TORCH}" "https://" TMP_VAR )
  if( "${TMP_VAR}" EQUAL 0 )
    list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "${ARGS_TORCH}" )
  else()
    list( APPEND VIAME_PYTHON_ADV_DEP_CMDS "torch${ARGS_TORCH}" )
  endif()
endif()

# ---------------------------- INSTALL ROUTINES --------------------------------

if( WIN32 )
  set( EXTRA_INCLUDE_DIRS "${VIAME_INSTALL_PREFIX}/include;$ENV{INCLUDE}" )
  set( EXTRA_LIBRARY_DIRS "${VIAME_INSTALL_PREFIX}/lib;$ENV{LIB}" )

  if( VIAME_ENABLE_PYTHON-INTERNAL )
    set( ENV{PYTHONPATH} "${VIAME_PYTHON_PATH};$ENV{PYTHONPATH}" )
  endif()

  string( REPLACE ";" "----" VIAME_PYTHON_PATH "${VIAME_PYTHON_PATH}" )
  string( REPLACE ";" "----" VIAME_EXECUTABLES_PATH "${VIAME_EXECUTABLES_PATH}" )
  string( REPLACE ";" "----" EXTRA_INCLUDE_DIRS "${EXTRA_INCLUDE_DIRS}" )
  string( REPLACE ";" "----" EXTRA_LIBRARY_DIRS "${EXTRA_LIBRARY_DIRS}" )

  list( APPEND PYTHON_DEP_ENV_VARS "INCLUDE=${EXTRA_INCLUDE_DIRS}" )
  list( APPEND PYTHON_DEP_ENV_VARS "LIB=${EXTRA_LIBRARY_DIRS}" )
else()
  list( APPEND PYTHON_DEP_ENV_VARS "PATH=${VIAME_EXECUTABLES_PATH}" )
  list( APPEND PYTHON_DEP_ENV_VARS "CPPFLAGS=-I${VIAME_INSTALL_PREFIX}/include" )
  list( APPEND PYTHON_DEP_ENV_VARS "LDFLAGS=-L${VIAME_INSTALL_PREFIX}/lib" )
  list( APPEND PYTHON_DEP_ENV_VARS "CC=${CMAKE_C_COMPILER}" )
  list( APPEND PYTHON_DEP_ENV_VARS "CXX=${CMAKE_CXX_COMPILER}" )
endif()

list( APPEND PYTHON_DEP_ENV_VARS "PYTHONPATH=${VIAME_PYTHON_PATH}" )
list( APPEND PYTHON_DEP_ENV_VARS "PYTHONUSERBASE=${VIAME_INSTALL_PREFIX}" )

set( VIAME_PYTHON_DEPS_DEPS fletch )

list( LENGTH VIAME_PYTHON_ADV_DEPS DEP_COUNT )
math( EXPR DEP_COUNT "${DEP_COUNT} - 1" )

foreach( ID RANGE ${DEP_COUNT} )

  list( GET VIAME_PYTHON_ADV_DEPS ${ID} DEP )

  set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} ${DEP} )

  if( "${DEP}" STREQUAL "python-deps" )
    set( PYTHON_LIB_DEPS ${VIAME_PYTHON_DEPS_DEPS} )
    set( CMD ${VIAME_PYTHON_BASIC_DEPS} )
  else()
    set( PYTHON_LIB_DEPS ${VIAME_PYTHON_DEPS_DEPS} python-deps )
    list( GET VIAME_PYTHON_ADV_DEP_CMDS ${ID} CMD )
  endif()

  set( PYTHON_DEP_PIP_CMD pip install --user ${CMD} )
  string( REPLACE " " ";" PYTHON_DEP_PIP_CMD "${PYTHON_DEP_PIP_CMD}" )

  set( PYTHON_DEP_BUILD
    ${CMAKE_COMMAND} -E env "${PYTHON_DEP_ENV_VARS}"
      ${Python_EXECUTABLE} -m ${PYTHON_DEP_PIP_CMD}
    )

  if( "${DEP}" STREQUAL "pytorch" )
    set( PYTHON_DEP_INSTALL ${CMAKE_COMMAND}
      -DVIAME_PYTHON_BASE:PATH=${VIAME_PYTHON_INSTALL}
      -DVIAME_PATCH_DIR:PATH=${VIAME_SOURCE_DIR}/packages/patches
      -DVIAME_PYTORCH_VERSION:STRING=${VIAME_PYTORCH_VERSION}
      -P ${VIAME_SOURCE_DIR}/cmake/custom_pytorch_install.cmake )
  else()
    set( PYTHON_DEP_INSTALL "" )
  endif()

  ExternalProject_Add( ${DEP}
    DEPENDS ${PYTHON_LIB_DEPS}
    PREFIX ${VIAME_BUILD_PREFIX}
    SOURCE_DIR ${VIAME_CMAKE_DIR}
    USES_TERMINAL_BUILD 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ${PYTHON_DEP_BUILD}
    INSTALL_COMMAND "${PYTHON_DEP_INSTALL}"
    INSTALL_DIR ${VIAME_INSTALL_PREFIX}
    LIST_SEPARATOR "----"
    )
endforeach()
