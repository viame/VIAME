# PyTorch External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_BUILD_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

CreateDirectory( ${VIAME_BUILD_PREFIX}/src/pytorch-build )

option( VIAME_ENABLE_PYTORCH-CORE     "Enable internal PyTorch build"   ON )
option( VIAME_ENABLE_PYTORCH-VISION   "Enable torchvision PyTorch code" ON )
option( VIAME_ENABLE_PYTORCH-MMDET    "Enable mmdet PyTorch code"       ON )
option( VIAME_ENABLE_PYTORCH-PYSOT    "Enable pysot PyTorch code"       OFF )
option( VIAME_ENABLE_PYTORCH-NETHARN  "Enable netharn PyTorch code"     OFF )

mark_as_advanced( VIAME_ENABLE_PYTORCH-CORE )
mark_as_advanced( VIAME_ENABLE_PYTORCH-VISION )
mark_as_advanced( VIAME_ENABLE_PYTORCH-MMDET )
mark_as_advanced( VIAME_ENABLE_PYTORCH-PYSOT )
mark_as_advanced( VIAME_ENABLE_PYTORCH-NETHARN )

set( VIAME_PYTORCH_BUILD_CORE   ${VIAME_ENABLE_PYTORCH-CORE}   CACHE INTERNAL "" )
set( VIAME_PYTORCH_BUILD_VISION ${VIAME_ENABLE_PYTORCH-VISION} CACHE INTERNAL "" )

if( WIN32 AND VIAME_ENABLE_PYTORCH-CORE )
  if( VIAME_ENABLE_CUDA AND CUDA_VERSION_MAJOR EQUAL 10 )
    set( VIAME_PYTORCH_BUILD_CORE OFF )
    set( VIAME_PYTORCH_BUILD_VISION OFF )
    DownloadAndExtract(
      https://data.kitware.com/api/v1/item/5d522e3867a3767939173f83/download
      193222893140fed4898fb67da1067a13
      ${VIAME_DOWNLOAD_DIR}/torch-1.0.1-cu10-windows-x64-binaries.zip
      ${VIAME_BUILD_INSTALL_PREFIX} )
  elseif( NOT VIAME_ENABLE_CUDA )
    set( VIAME_PYTORCH_BUILD_CORE OFF )
    set( VIAME_PYTORCH_BUILD_VISION OFF )
    DownloadAndExtract(
      https://data.kitware.com/api/v1/item/5d54df4185f25b11ff2ded7a/download
      db5543b42f697c05329d288357835f8a
      ${VIAME_DOWNLOAD_DIR}/torch-1.0.1-cpu-windows-x64-binaries.zip
      ${VIAME_BUILD_INSTALL_PREFIX} )
  endif()
endif()

set( PYTORCH_LIBRARIES )

if( VIAME_PYTORCH_BUILD_CORE )
  set( PYTORCH_LIBRARIES ${PYTORCH_LIBRARIES} pytorch )

  set( COMMON_PYTORCH_PROJECT_DEP fletch pytorch )
else()
  set( COMMON_PYTORCH_PROJECT_DEP fletch )
endif()

if( VIAME_PYTORCH_BUILD_VISION )
  set( PYTORCH_LIBRARIES ${PYTORCH_LIBRARIES} torchvision )
endif()

if( VIAME_ENABLE_PYTORCH-MMDET )
  set( PYTORCH_LIBRARIES ${PYTORCH_LIBRARIES} mmcv mmdetection )
endif()

if( VIAME_ENABLE_PYTORCH-PYSOT )
  set( PYTORCH_LIBRARIES ${PYTORCH_LIBRARIES} pysot )
endif()

if( VIAME_ENABLE_PYTORCH-NETHARN )
  set( PYTORCH_LIBRARIES ${PYTORCH_LIBRARIES} netharn )
endif()

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} ${PYTORCH_LIBRARIES} )

if( VIAME_ENABLE_CUDNN )
  if( VIAME_ENABLE_PYTORCH-CORE AND "${CUDNN_VERSION_MAJOR}" VERSION_LESS "7.0.0" )
    message( FATAL_ERROR "CUDNN version 7.0 or higher required for internal pytorch" )
  endif()

  set( CUDNN_ENV "CUDNN_LIBRARY=${CUDNN_LIBRARIES}" )
  if( CUDNN_ROOT_DIR )
    list( APPEND CUDNN_ENV "CUDNN_INCLUDE_DIR=${CUDNN_ROOT_DIR}/include" )
  endif()
  if( WIN32 )
    string( REPLACE ";" "----" CUDNN_ENV "${CUDNN_ENV}" )
  endif()
else()
  unset( CUDNN_ENV )
endif()

set( PYTHON_BASEPATH
  ${VIAME_BUILD_INSTALL_PREFIX}/lib/python${PYTHON_VERSION} )

if( VIAME_ENABLE_CUDA )
  set( TORCH_CUDA_ARCHITECTURES "3.0 3.5 5.0 5.2 6.0 6.1+PTX" )
  set( TORCH_NVCC_FLAGS "-Xfatbin -compress-all" )
else()
  set( TORCH_CUDA_ARCHITECTURES )
  set( TORCH_NVCC_FLAGS )
endif()

if( WIN32 )
  set( CUSTOM_PYTHONPATH
    ${PYTHON_BASEPATH}/site-packages;${PYTHON_BASEPATH}/dist-packages )
  if( VIAME_ENABLE_CUDA )
    set( CUSTOM_PATH
      ${VIAME_BUILD_INSTALL_PREFIX}/bin;${CUDA_TOOLKIT_ROOT_DIR}/bin;$ENV{PATH} )
  else()
    set( CUSTOM_PATH
      ${VIAME_BUILD_INSTALL_PREFIX}/bin )
  endif()
  string( REPLACE ";" "----" CUSTOM_PYTHONPATH "${CUSTOM_PYTHONPATH}" )
  string( REPLACE ";" "----" CUSTOM_PATH "${CUSTOM_PATH}" )
else()
  set( CUSTOM_PYTHONPATH
    ${PYTHON_BASEPATH}/site-packages:${PYTHON_BASEPATH}/dist-packages )
  if( VIAME_ENABLE_CUDA )
    set( CUSTOM_PATH
      ${VIAME_BUILD_INSTALL_PREFIX}/bin:${CUDA_TOOLKIT_ROOT_DIR}/bin:$ENV{PATH} )
  else()
    set( CUSTOM_PATH
      ${VIAME_BUILD_INSTALL_PREFIX}/bin:$ENV{PATH} )
  endif()
endif()

foreach( LIB ${PYTORCH_LIBRARIES} )

  if( "${LIB}" STREQUAL "pytorch" )
    set( LIBRARY_LOCATION ${VIAME_PACKAGES_DIR}/pytorch )
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

  set( LIBRARY_PIP_SETTINGS ${LIBRARY_PIP_BUILD_DIR_CMD} ${LIBRARY_PIP_CACHE_DIR_CMD} )

  if( VIAME_SYMLINK_PYTHON )
    set( LIBRARY_PIP_BUILD_CMD
      ${PYTHON_EXECUTABLE} setup.py build )
    set( LIBRARY_PIP_INSTALL_CMD
      ${PYTHON_EXECUTABLE} -m pip install --user -e . )
  else()
    set( LIBRARY_PIP_BUILD_CMD
      ${PYTHON_EXECUTABLE} setup.py bdist_wheel -d ${LIBRARY_PIP_BUILD_DIR} )
    set( LIBRARY_PIP_INSTALL_CMD
      ${CMAKE_COMMAND}
        -DPYTHON_EXECUTABLE=${PYTHON_EXECUTABLE}
        -DWHEEL_DIR=${LIBRARY_PIP_BUILD_DIR}
        -P ${VIAME_CMAKE_DIR}/install_python_wheel.cmake )
  endif()

  set( LIBRARY_PYTHON_BUILD
    ${CMAKE_COMMAND} -E env "PYTHONPATH=${CUSTOM_PYTHONPATH}"
                            "TMPDIR=${LIBRARY_PIP_TMP_DIR}"
                            "PATH=${CUSTOM_PATH}"
                            "PYTHONUSERBASE=${VIAME_BUILD_INSTALL_PREFIX}"
                            "CUDA_HOME=${CUDA_TOOLKIT_ROOT_DIR}"
                            "TORCH_CUDA_ARCH_LIST=${TORCH_CUDA_ARCHITECTURES}"
                            "TORCH_NVCC_FLAGS=${TORCH_NVCC_FLAGS}"
                            "${CUDNN_ENV}"
      ${LIBRARY_PIP_BUILD_CMD} )
  set( LIBRARY_PYTHON_INSTALL
    ${CMAKE_COMMAND} -E env "PYTHONPATH=${CUSTOM_PYTHONPATH}"
                            "TMPDIR=${LIBRARY_PIP_TMP_DIR}"
                            "PATH=${CUSTOM_PATH}"
                            "PYTHONUSERBASE=${VIAME_BUILD_INSTALL_PREFIX}"
                            "CUDA_HOME=${CUDA_TOOLKIT_ROOT_DIR}"
                            "TORCH_CUDA_ARCH_LIST=${TORCH_CUDA_ARCHITECTURES}"
                            "TORCH_NVCC_FLAGS=${TORCH_NVCC_FLAGS}"
                            "${CUDNN_ENV}"
      ${LIBRARY_PIP_INSTALL_CMD} )

  if( "${LIB}" STREQUAL "mmdetection" )
    set( MMDET_SUBDEPS roi_align roi_pool nms dcn )

    foreach( DEP ${MMDET_SUBDEPS} )
      set( DEP_PYTHON_BUILD
        ${CMAKE_COMMAND} -E env "PYTHONPATH=${CUSTOM_PYTHONPATH}"
                                "TMPDIR=${LIBRARY_PIP_TMP_DIR}"
                                "PATH=${CUSTOM_PATH}"
                                "PYTHONUSERBASE=${VIAME_BUILD_INSTALL_PREFIX}"
                                "CUDA_HOME=${CUDA_TOOLKIT_ROOT_DIR}"
                                "TORCH_CUDA_ARCH_LIST=${TORCH_CUDA_ARCHITECTURES}"
                                "TORCH_NVCC_FLAGS=${TORCH_NVCC_FLAGS}"
                                "${CUDNN_ENV}"
          ${PYTHON_EXECUTABLE} setup.py build_ext --inplace )
      set( DEP_DEPS ${COMMON_PYTORCH_PROJECT_DEP} mmcv )
      ExternalProject_Add( mmdet_${DEP}
        DEPENDS ${DEP_DEPS}
        PREFIX ${VIAME_BUILD_PREFIX}
        SOURCE_DIR ${VIAME_PACKAGES_DIR}/pytorch-libs/${LIB}/mmdet/ops/${DEP}
        STAMP_DIR ${VIAME_BUILD_PREFIX}/src/pytorch-build/${DEP}-stamp
        BUILD_IN_SOURCE 1
        CONFIGURE_COMMAND ""
        BUILD_COMMAND ${DEP_PYTHON_BUILD}
        INSTALL_COMMAND ""
        LIST_SEPARATOR "----"
        )
    endforeach()

    set( PROJECT_DEPS ${COMMON_PYTORCH_PROJECT_DEP} mmcv
         mmdet_roi_align mmdet_roi_pool mmdet_dcn mmdet_nms )
  elseif( "${LIB}" STREQUAL "pytorch" )
    set( PROJECT_DEPS fletch )
  else()
    set( PROJECT_DEPS ${COMMON_PYTORCH_PROJECT_DEP} )
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
