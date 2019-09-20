# fletch External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_BUILD_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} fletch )

set( VIAME_FLETCH_BUILD_DIR "${VIAME_BUILD_PREFIX}/src/fletch-build"
     CACHE STRING "Alternative FLETCH build dir" )
mark_as_advanced( VIAME_FLETCH_BUILD_DIR )

if( VIAME_ENABLE_PYTHON )
  FormatPassdowns( "PYTHON" VIAME_PYTHON_FLAGS )
endif()

if( VIAME_ENABLE_CUDA )
  FormatPassdowns( "CUDA" VIAME_CUDA_FLAGS )
endif()

if( VIAME_ENABLE_CUDNN )
  FormatPassdowns( "CUDNN" VIAME_CUDNN_FLAGS )
endif()

if( VIAME_ENABLE_VXL OR VIAME_ENABLE_OPENCV OR VIAME_ENABLE_SEAL_TK )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_ZLib:BOOL=ON
    -Dfletch_ENABLE_libjpeg-turbo:BOOL=${VIAME_BUILD_CORE_IMAGE_LIBS}
    -Dfletch_ENABLE_libtiff:BOOL=${VIAME_BUILD_CORE_IMAGE_LIBS}
    -Dfletch_ENABLE_PNG:BOOL=${VIAME_BUILD_CORE_IMAGE_LIBS}
  )
  if( VIAME_ENABLE_VXL )
    set( fletch_DEP_FLAGS
      ${fletch_DEP_FLAGS}
      -Dfletch_ENABLE_libgeotiff:BOOL=${VIAME_BUILD_CORE_IMAGE_LIBS}
    )
  endif()
endif()

if( VIAME_ENABLE_GDAL )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_libgeotiff:BOOL=ON
  )
elseif( NOT VIAME_ENABLE_GDAL AND NOT VIAME_ENABLE_VXL )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_libgeotiff:BOOL=OFF
  )
endif()

if( VIAME_ENABLE_VIVIA OR VIAME_ENABLE_BURNOUT OR VIAME_ENABLE_SEAL_TK )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_TinyXML1:BOOL=ON
    -Dfletch_ENABLE_libjson:BOOL=ON
    -Dfletch_ENABLE_GeographicLib:BOOL=ON
  )
else()
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_TinyXML1:BOOL=OFF
    -Dfletch_ENABLE_libjson:BOOL=OFF
    -Dfletch_ENABLE_GeographicLib:BOOL=OFF
  )
endif()

if( VIAME_ENABLE_VIVIA )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_shapelib:BOOL=OFF
    -Dfletch_ENABLE_VTK:BOOL=ON
    -Dfletch_ENABLE_qtExtensions:BOOL=ON
    -DVTK_SELECT_VERSION:STRING=8.0
    -DQt_SELECT_VERSION:STRING=4.8.6
    -Dfletch_ENABLE_PROJ4:BOOL=ON
    -Dfletch_ENABLE_libkml:BOOL=ON
    -Dfletch_ENABLE_PNG:BOOL=ON
  )
  if( NOT WIN32 )
    set( fletch_DEP_FLAGS
      ${fletch_DEP_FLAGS}
      -Dfletch_ENABLE_libxml2:BOOL=ON
    )
  endif()
elseif( VIAME_ENABLE_SEAL_TK)
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_qtExtensions:BOOL=ON
    -Dfletch_ENABLE_VTK:BOOL=OFF
    -Dfletch_ENABLE_ZLib:BOOL=ON
    -DQt_SELECT_VERSION:STRING=5.11.2
  )
else()
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_VTK:BOOL=OFF
  )
endif()

if( VIAME_ENABLE_KWANT )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_TinyXML1:BOOL=ON
    -Dfletch_ENABLE_libjson:BOOL=ON
    -Dfletch_ENABLE_YAMLcpp:BOOL=ON
  )
endif()

if( VIAME_ENABLE_CUDA )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_BUILD_WITH_CUDA:BOOL=ON
  )
  if( VIAME_ENABLE_CUDNN )
    set( fletch_DEP_FLAGS
      ${fletch_DEP_FLAGS}
      -Dfletch_BUILD_WITH_CUDNN:BOOL=ON
    )
  else()
    set( fletch_DEP_FLAGS
      ${fletch_DEP_FLAGS}
      -Dfletch_BUILD_WITH_CUDNN:BOOL=OFF
    )
  endif()
else()
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_BUILD_WITH_CUDA:BOOL=OFF
  )
endif()

if( VIAME_ENABLE_FFMPEG )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_FFmpeg:BOOL=ON
  )
else()
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_FFmpeg:BOOL=OFF
  )
endif()

if( VIAME_ENABLE_CAFFE OR VIAME_BUILD_TESTS )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_GTest:BOOL=ON
  )
else()
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_GTest:BOOL=OFF
  )
endif()

if( WIN32 AND VIAME_ENABLE_ITK )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_HDF5:BOOL=ON
  )
endif()

if( EXTERNAL_Qt )
  if( WIN32 )
    set( fletch_DEP_FLAGS
      ${fletch_DEP_FLAGS}
      -Dfletch_ENABLE_Qt:BOOL=OFF
      -DQt5_DIR:PATH=${EXTERNAL_Qt}/lib/cmake/Qt5
      -DQT_QMAKE_EXECUTABLE:PATH=${EXTERNAL_Qt}/bin/qmake.exe
    )
  else()
    set( fletch_DEP_FLAGS
      ${fletch_DEP_FLAGS}
      -Dfletch_ENABLE_Qt:BOOL=OFF
      -DQt5_DIR:PATH=${EXTERNAL_Qt}/lib/cmake/Qt5
      -DQT_QMAKE_EXECUTABLE:PATH=${EXTERNAL_Qt}/bin/qmake
    )
  endif()
elseif( VIAME_ENABLE_VIVIA OR VIAME_ENABLE_BURNOUT OR VIAME_ENABLE_SEAL_TK )
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_Qt:BOOL=ON
  )
else()
  set( fletch_DEP_FLAGS
    ${fletch_DEP_FLAGS}
    -Dfletch_ENABLE_Qt:BOOL=OFF
  )
endif()

if( EXTERNAL_OpenCV )
  set( FLETCH_BUILD_OPENCV OFF )
else()
  set( FLETCH_BUILD_OPENCV ${VIAME_ENABLE_OPENCV} )
endif()

if( EXTERNAL_ITK )
  set( FLETCH_BUILD_ITK OFF )
else()
  set( FLETCH_BUILD_ITK ${VIAME_ENABLE_ITK} )
endif()

ExternalProject_Add(fletch
  PREFIX ${VIAME_BUILD_PREFIX}
  SOURCE_DIR ${VIAME_PACKAGES_DIR}/fletch
  BINARY_DIR ${VIAME_FLETCH_BUILD_DIR}
  USES_TERMINAL_BUILD 1
  CMAKE_GENERATOR ${gen}
  CMAKE_CACHE_ARGS
    ${VIAME_ARGS_COMMON}
    ${VIAME_PYTHON_FLAGS}
    ${VIAME_CUDA_FLAGS}
    ${VIAME_CUDNN_FLAGS}

    -DBUILD_SHARED_LIBS:BOOL=ON

    # KWIVER Dependencies, Always On
    -Dfletch_ENABLE_Boost:BOOL=TRUE
    -Dfletch_ENABLE_Eigen:BOOL=TRUE

    # Optional Dependencies
    ${fletch_DEP_FLAGS}

    -Dfletch_ENABLE_VXL:BOOL=${VIAME_ENABLE_VXL}
    -Dfletch_ENABLE_ITK:BOOL=${FLETCH_BUILD_ITK}
    -Dfletch_ENABLE_OpenCV:BOOL=${FLETCH_BUILD_OPENCV}
    -Dfletch_ENABLE_OpenCV_contrib:BOOL=${FLETCH_BUILD_OPENCV}
    -DOpenCV_SELECT_VERSION:STRING=${VIAME_OPENCV_VERSION}

    -Dfletch_ENABLE_Caffe:BOOL=${VIAME_ENABLE_CAFFE}
    -DAUTO_ENABLE_CAFFE_DEPENDENCY:BOOL=${VIAME_ENABLE_CAFFE}

    -Dfletch_BUILD_WITH_PYTHON:BOOL=${VIAME_ENABLE_PYTHON}
    -Dfletch_PYTHON_MAJOR_VERSION:STRING=${PYTHON_VERSION_MAJOR}
    -Dfletch_FORCE_CUDA_CSTD98:BOOL=${VIAME_FORCE_CUDA_CSTD98}

    -Dfletch_ENABLE_PostgreSQL:BOOL=${VIAME_ENABLE_SMQTK}
    -Dfletch_ENABLE_CppDB:BOOL=${VIAME_ENABLE_SMQTK}

    -Dfletch_ENABLE_pybind11:BOOL=${VIAME_ENABLE_PYTHON}
    -Dfletch_ENABLE_PyBind11:BOOL=${VIAME_ENABLE_PYTHON}

    -Dfletch_ENABLE_GDAL:BOOL=${VIAME_ENABLE_GDAL}
    -Dfletch_ENABLE_openjpeg:BOOL=${VIAME_ENABLE_GDAL}

    # Set fletch install path to be viame install path
    -Dfletch_BUILD_INSTALL_PREFIX:PATH=${VIAME_BUILD_INSTALL_PREFIX}

    # Disable optional OpenCV build flags, these oft don't build
    -Dfletch_ENABLE_OpenCV_CUDA:BOOL=FALSE
    -Dfletch_ENABLE_OpenCV_FFmpeg:BOOL=FALSE
    -Dfletch_ENABLE_OpenCV_TIFF:BOOL=${VIAME_BUILD_CORE_IMAGE_LIBS}

  INSTALL_DIR ${VIAME_BUILD_INSTALL_PREFIX}
  INSTALL_COMMAND ${CMAKE_COMMAND}
    -DVIAME_CMAKE_DIR:PATH=${VIAME_CMAKE_DIR}
    -DVIAME_ENABLE_OPENCV:BOOL=${VIAME_ENABLE_OPENCV}
    -DVIAME_BUILD_PREFIX:PATH=${VIAME_BUILD_PREFIX}
    -DVIAME_BUILD_INSTALL_PREFIX:PATH=${VIAME_BUILD_INSTALL_PREFIX}
    -DMSVC=${MSVC}
    -DMSVC_VERSION=${MSVC_VERSION}
    -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
    -DVIAME_ENABLE_CAFFE=${VIAME_ENABLE_CAFFE}
    -DVIAME_ENABLE_SMQTK=${VIAME_ENABLE_SMQTK}
    -P ${VIAME_SOURCE_DIR}/cmake/custom_fletch_install.cmake
  )

if( VIAME_FORCEBUILD )
  ExternalProject_Add_Step(fletch forcebuild
    COMMAND ${CMAKE_COMMAND}
      -E remove ${VIAME_BUILD_PREFIX}/src/fletch-stamp/fletch-build
    COMMENT "Removing build stamp file for build update (forcebuild)."
    DEPENDEES configure
    DEPENDERS build
    ALWAYS 1
    )
endif()

if( WIN32 )
  set( VIAME_ARGS_fletch
    -Dfletch_DIR:PATH=${VIAME_FLETCH_BUILD_DIR}
    )
else()
  set( VIAME_ARGS_fletch
    -Dfletch_DIR:PATH=${VIAME_BUILD_INSTALL_PREFIX}/share/cmake
    )
endif()

set( VIAME_ARGS_Boost
  -DBoost_INCLUDE_DIR:PATH=${VIAME_BUILD_INSTALL_PREFIX}/include
  )

if( VIAME_ENABLE_OPENCV )
  if( NOT EXTERNAL_OpenCV )
    set(VIAME_ARGS_fletch
      ${VIAME_ARGS_fletch}
      -DOpenCV_DIR:PATH=${VIAME_FLETCH_BUILD_DIR}/build/src/OpenCV-build
      )
  else()
    set( VIAME_ARGS_fletch
      ${VIAME_ARGS_fletch}
      -DOpenCV_DIR:PATH=${EXTERNAL_OpenCV}
      )
  endif()
endif()

if( VIAME_ENABLE_CAFFE )
  set( VIAME_ARGS_fletch
     ${VIAME_ARGS_fletch}
    -DCaffe_DIR:PATH=${VIAME_FLETCH_BUILD_DIR}/build/src/Caffe-build
    )
endif()

if( VIAME_ENABLE_VIVIA )
  set( VIAME_ARGS_libkml
     ${VIAME_ARGS_libkml}
    -DKML_DIR:PATH=${VIAME_FLETCH_BUILD_DIR}/build/src/libkml-build
    )
  set( VIAME_ARGS_VTK
     ${VIAME_ARGS_VTK}
    -DVTK_DIR:PATH=${VIAME_FLETCH_BUILD_DIR}/build/src/VTK-build
    )
  set( VIAME_ARGS_PROJ4
     ${VIAME_ARGS_PROJ4}
    -DPROJ4_INCLUDE_DIR:PATH=${VIAME_BUILD_INSTALL_PREFIX}/include
    )
  if( WIN32 )
    set( VIAME_ARGS_PROJ4
       ${VIAME_ARGS_PROJ4}
      -DPROJ4_LIBRARY:PATH=${VIAME_BUILD_INSTALL_PREFIX}/lib/proj_4_9.lib
      )
  endif()
endif()

if( EXTERNAL_Qt )
  if( WIN32 )
    set(VIAME_ARGS_Qt
       ${VIAME_ARGS_Qt}
       -DQt5_DIR:PATH=${EXTERNAL_Qt}/lib/cmake/Qt5
       -DQT_QMAKE_EXECUTABLE:PATH=${EXTERNAL_Qt}/bin/qmake.exe
    )
  else()
    set(VIAME_ARGS_Qt
       ${VIAME_ARGS_Qt}
       -DQt5_DIR:PATH=${EXTERNAL_Qt}/lib/cmake/Qt5
       -DQT_QMAKE_EXECUTABLE:PATH=${EXTERNAL_Qt}/bin/qmake
    )
  endif()
elseif( VIAME_ENABLE_VIVIA OR VIAME_ENABLE_SEAL_TK )
  if( WIN32 )
    set( VIAME_ARGS_Qt
       ${VIAME_ARGS_Qt}
       -DQT_QMAKE_EXECUTABLE:PATH=${VIAME_BUILD_INSTALL_PREFIX}/bin/qmake.exe
    )
  else()
    set( VIAME_ARGS_Qt
       ${VIAME_ARGS_Qt}
       -DQT_QMAKE_EXECUTABLE:PATH=${VIAME_BUILD_INSTALL_PREFIX}/bin/qmake
    )
  endif()
endif()

if( VIAME_ENABLE_VXL )
  set( VIAME_ARGS_VXL
    ${VIAME_ARGS_VXL}
    -DVXL_DIR:PATH=${VIAME_FLETCH_BUILD_DIR}/build/src/VXL-build
    )
  set( VIAME_ARGS_VXL_INSTALL
    ${VIAME_ARGS_VXL_INSTALL}
    -DVXL_DIR:PATH=${VIAME_BUILD_INSTALL_PREFIX}/share/vxl/cmake
    )
endif()

if( EXTERNAL_ITK )
  set( VIAME_ARGS_ITK
    ${VIAME_ARGS_ITK}
    -DITK_DIR:PATH=${EXTERNAL_ITK}
    )
elseif( VIAME_ENABLE_ITK )
  set( VIAME_ARGS_ITK
    ${VIAME_ARGS_ITK}
    -DITK_DIR:PATH=${VIAME_FLETCH_BUILD_DIR}/build/src/ITK-build
    )
endif()
