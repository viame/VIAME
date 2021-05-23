# PyTorch External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

CreateDirectory( ${VIAME_BUILD_PREFIX}/src/pytorch-build )

set( PYTORCH_LIBS_TO_BUILD )

if( VIAME_ENABLE_PYTORCH-INTERNAL )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} pytorch )
endif()

if( VIAME_ENABLE_PYTORCH-VIS-INTERNAL )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} torchvision )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET OR VIAME_ENABLE_PYTORCH-NETHARN )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} imgaug )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} mmcv mmdetection )
endif()

if( VIAME_ENABLE_PYTORCH-PYSOT )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} pysot )
endif()

if( VIAME_ENABLE_PYTORCH-MDNET )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} roi-align )
endif()

if( VIAME_ENABLE_PYTORCH-NETHARN )
  set( PYTORCH_LIBS_TO_BUILD ${PYTORCH_LIBS_TO_BUILD} netharn bioharn )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET )
  if( VIAME_ENABLE_CUDA AND CUDA_VERSION VERSION_LESS "9.0" )
    message( FATAL_ERROR "To use mmdetection you must have at least CUDA 9.0.\n\n"
                         "Install CUDA 9.0+ or disable VIAME_ENABLE_PYTORCH-MMDET" )
  endif()
  if( NOT VIAME_ENABLE_PYTHON-INTERNAL AND Python_VERSION VERSION_LESS "3.0" )
    message( FATAL_ERROR "To use mmdetection you must have at least Python 3.0.\n\n"
                         "Use Python3 or disable VIAME_ENABLE_PYTORCH-MMDET" )
  endif()
endif()

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} ${PYTORCH_LIBS_TO_BUILD} )
set( PYTORCH_ENV_VARS )

if( VIAME_ENABLE_CUDNN )
  if( VIAME_ENABLE_PYTORCH-INTERNAL AND "${CUDNN_VERSION_MAJOR}" VERSION_LESS "7.0.0" )
    message( FATAL_ERROR "CUDNN version 7.0 or higher required for internal pytorch" )
  endif()
  list( APPEND PYTORCH_ENV_VARS "CUDNN_LIBRARY=${CUDNN_LIBRARIES}" )
  if( WIN32 )
    string( REPLACE ";" "----" PYTORCH_ENV_VARS "${PYTORCH_ENV_VARS}" )
  endif()
  if( CUDNN_ROOT_DIR )
    list( APPEND PYTORCH_ENV_VARS "CUDNN_INCLUDE_DIR=${CUDNN_ROOT_DIR}/include" )
  endif()
endif()

if( VIAME_ENABLE_PYTORCH-DISABLE-NINJA )
  list( APPEND PYTORCH_ENV_VARS "USE_NINJA=OFF" )
endif()

if( VIAME_ENABLE_PYTORCH-NETHARN )
  list( APPEND PYTORCH_ENV_VARS "BEZIER_NO_EXTENSION=1" )
endif()

if( VIAME_ENABLE_CUDA )
  if( CUDA_VERSION VERSION_LESS "9.0" AND VIAME_ENABLE_PYTORCH-NETHARN )
    message( FATAL_ERROR "VIAME_ENABLE_PYTORCH-NETHARN requires CUDA 9 or above" )
  endif()

  list( APPEND PYTORCH_ENV_VARS "USE_CUDA=1" )
  list( APPEND PYTORCH_ENV_VARS "CUDA_HOME=${CUDA_TOOLKIT_ROOT_DIR}" )
  list( APPEND PYTORCH_ENV_VARS "TORCH_CUDA_ARCH_LIST=${CUDA_ARCHITECTURES}" )
  list( APPEND PYTORCH_ENV_VARS "TORCH_NVCC_FLAGS=-Xfatbin -compress-all" )
else()
  list( APPEND PYTORCH_ENV_VARS "USE_CUDA=0" )
endif()

if( VIAME_ENABLE_PYTORCH-FORCE-CUDA )
  list( APPEND PYTORCH_ENV_VARS "FORCE_CUDA=1" )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET )
  list( APPEND PYTORCH_ENV_VARS "MMCV_WITH_OPS=1" )
endif()

if( WIN32 )
  set( EXTRA_INCLUDE_DIRS "${VIAME_INSTALL_PREFIX}/include;$ENV{INCLUDE}" )
  set( EXTRA_LIBRARY_DIRS "${VIAME_INSTALL_PREFIX}/lib;$ENV{LIB}" )

  string( REPLACE ";" "----" VIAME_PYTHON_PATH "${VIAME_PYTHON_PATH}" )
  string( REPLACE ";" "----" EXTRA_INCLUDE_DIRS "${EXTRA_INCLUDE_DIRS}" )
  string( REPLACE ";" "----" EXTRA_LIBRARY_DIRS "${EXTRA_LIBRARY_DIRS}" )

  list( APPEND PYTORCH_ENV_VARS "INCLUDE=${EXTRA_INCLUDE_DIRS}" )
  list( APPEND PYTORCH_ENV_VARS "LIB=${EXTRA_LIBRARY_DIRS}" )
else()
  list( APPEND PYTORCH_ENV_VARS "CPPFLAGS=-I${VIAME_INSTALL_PREFIX}/include" )
  list( APPEND PYTORCH_ENV_VARS "LDFLAGS=-L${VIAME_INSTALL_PREFIX}/lib" )
  list( APPEND PYTORCH_ENV_VARS "CC=${CMAKE_C_COMPILER}" )
  list( APPEND PYTORCH_ENV_VARS "CXX=${CMAKE_CXX_COMPILER}" )
  list( APPEND PYTORCH_ENV_VARS "PATH=${VIAME_EXECUTABLES_PATH}" )
endif()

list( APPEND PYTORCH_ENV_VARS "PYTHONPATH=${VIAME_PYTHON_PATH}" )
list( APPEND PYTORCH_ENV_VARS "PYTHONUSERBASE=${VIAME_INSTALL_PREFIX}" )

foreach( LIB ${PYTORCH_LIBS_TO_BUILD} )
  if( "${LIB}" STREQUAL "pytorch" )
    set( LIBRARY_LOCATION ${VIAME_PACKAGES_DIR}/pytorch )
    set( LIBRARY_LOCATION_URL file://${LIBRARY_LOCATION} )
  elseif( "${LIB}" STREQUAL "roi-align" )
    set( LIBRARY_LOCATION ${VIAME_SOURCE_DIR}/plugins/pytorch/mdnet )
    set( LIBRARY_LOCATION_URL file://${LIBRARY_LOCATION} )
  else()
    set( LIBRARY_LOCATION ${VIAME_PACKAGES_DIR}/pytorch-libs/${LIB} )
    set( LIBRARY_LOCATION_URL file://${LIBRARY_LOCATION} )
  endif()

  set( LIBRARY_PIP_CACHE_DIR ${VIAME_BUILD_PREFIX}/src/pytorch-build/${LIB}-cache )
  set( LIBRARY_PIP_BUILD_DIR ${VIAME_BUILD_PREFIX}/src/pytorch-build/${LIB}-build )
  set( LIBRARY_PIP_TMP_DIR ${VIAME_BUILD_PREFIX}/src/pytorch-build/${LIB}-tmp )

  CreateDirectory( ${LIBRARY_PIP_CACHE_DIR} )
  CreateDirectory( ${LIBRARY_PIP_BUILD_DIR} )
  CreateDirectory( ${LIBRARY_PIP_TMP_DIR} )

  set( LIBRARY_PIP_BUILD_DIR_CMD -b ${LIBRARY_PIP_BUILD_DIR} )
  set( LIBRARY_PIP_CACHE_DIR_CMD --cache-dir ${LIBRARY_PIP_CACHE_DIR} )

  if( VIAME_SYMLINK_PYTHON )
    set( LIBRARY_PIP_BUILD_CMD
      ${Python_EXECUTABLE} setup.py build )
    set( LIBRARY_PIP_INSTALL_CMD
      ${Python_EXECUTABLE} -m pip install --user -e . )
  else()
    if( "${LIB}" STREQUAL "mmcv" OR "${LIB}" STREQUAL "torchvision" )
      set( LIBRARY_PIP_BUILD_CMD
        ${Python_EXECUTABLE} setup.py
          bdist_wheel -d ${LIBRARY_PIP_BUILD_DIR} )
    else()
      set( LIBRARY_PIP_BUILD_CMD
        ${Python_EXECUTABLE} setup.py build_ext
          --include-dirs="${VIAME_INSTALL_PREFIX}/include"
          --library-dirs="${VIAME_INSTALL_PREFIX}/lib"
          --inplace bdist_wheel -d ${LIBRARY_PIP_BUILD_DIR} )
    endif()
    set( LIBRARY_PIP_INSTALL_CMD
      ${CMAKE_COMMAND}
        -DPYTHON_EXECUTABLE=${Python_EXECUTABLE}
        -DPython_EXECUTABLE=${Python_EXECUTABLE}
        -DWHEEL_DIR=${LIBRARY_PIP_BUILD_DIR}
        -P ${VIAME_CMAKE_DIR}/install_python_wheel.cmake )
  endif()

  set( LIBRARY_PYTHON_BUILD
    ${CMAKE_COMMAND} -E env "${PYTORCH_ENV_VARS}"
    "TMPDIR=${LIBRARY_PIP_TMP_DIR}"
    ${LIBRARY_PIP_BUILD_CMD} )
  set( LIBRARY_PYTHON_INSTALL
    ${CMAKE_COMMAND} -E env "${PYTORCH_ENV_VARS}"
    "TMPDIR=${LIBRARY_PIP_TMP_DIR}"
    ${LIBRARY_PIP_INSTALL_CMD} )

  if( "${LIB}" STREQUAL "bioharn" )
    set( PROJECT_DEPS netharn )
  elseif( "${LIB}" STREQUAL "netharn" )
    set( PROJECT_DEPS mmdetection )
  elseif( "${LIB}" STREQUAL "mmdetection" )
    set( PROJECT_DEPS fletch mmcv )
    if( VIAME_ENABLE_PYTORCH-VIS-INTERNAL )
      set( PROJECT_DEPS ${PROJECT_DEPS} torchvision )
    endif()
  elseif( "${LIB}" STREQUAL "pytorch" )
    set( PROJECT_DEPS fletch python-deps )
  else()
    set( PROJECT_DEPS fletch python-deps pytorch )
  endif()

  if( VIAME_ENABLE_SMQTK )
    set( PROJECT_DEPS ${PROJECT_DEPS} smqtk )
  endif()

  ExternalProject_Add( ${LIB}
    DEPENDS ${PROJECT_DEPS}
    PREFIX ${VIAME_BUILD_PREFIX}
    SOURCE_DIR ${LIBRARY_LOCATION}
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ${LIBRARY_PYTHON_BUILD}
    INSTALL_COMMAND ${LIBRARY_PYTHON_INSTALL}
    LIST_SEPARATOR "----"
    )

  if( VIAME_FORCEBUILD )
    ExternalProject_Add_Step( ${LIB} forcebuild
      COMMAND ${CMAKE_COMMAND}
        -E remove ${VIAME_BUILD_PREFIX}/src/{LIB}-stamp
      COMMENT "Removing build stamp file for build update (forcebuild)."
      DEPENDEES configure
      DEPENDERS build
      ALWAYS 1
      )
  endif()
endforeach()

set( VIAME_ARGS_pytorch
  -Dpytorch_DIR:PATH=${VIAME_BUILD_PREFIX}/src/pytorch-build
  )
