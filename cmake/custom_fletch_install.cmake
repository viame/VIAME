message( "Running fletch install" )

include( ${VIAME_CMAKE_DIR}/common_macros.cmake )

if( WIN32 )

  if( MSVC AND MSVC_VERSION EQUAL 1900 )
    RenameSubstr( ${VIAME_INSTALL_PREFIX}/lib/libboost* vc120 vc140 )
  endif()
 
  if( VIAME_ENABLE_OPENCV )
    CopyFiles( ${VIAME_INSTALL_PREFIX}/x86/*/bin/*.dll ${VIAME_INSTALL_PREFIX}/bin )
    CopyFiles( ${VIAME_INSTALL_PREFIX}/x86/*/lib/*.lib ${VIAME_INSTALL_PREFIX}/lib )

    CopyFiles( ${VIAME_INSTALL_PREFIX}/x64/*/bin/*.dll ${VIAME_INSTALL_PREFIX}/bin )
    CopyFiles( ${VIAME_INSTALL_PREFIX}/x64/*/lib/*.lib ${VIAME_INSTALL_PREFIX}/lib )
  endif()

  if( VIAME_ENABLE_CAFFE )
    MoveFiles( ${VIAME_INSTALL_PREFIX}/lib/caffe*.dll ${VIAME_INSTALL_PREFIX}/bin )
  endif()
endif()

# Current caffe quick hacks
if( CMAKE_BUILD_TYPE STREQUAL "Debug" AND NOT WIN32 AND VIAME_ENABLE_CAFFE )
  CreateSymlink( ${VIAME_INSTALL_PREFIX}/lib/libcaffe-d.so
                 ${VIAME_INSTALL_PREFIX}/lib/libcaffe.so )
endif()

if( NOT WIN32 AND VIAME_ENABLE_CAFFE )
  CreateSymlink( ${VIAME_INSTALL_PREFIX}/lib/libleveldb.so
                 ${VIAME_INSTALL_PREFIX}/lib/libleveldb.so.1 )
endif()

# Move any misinstalled python files
if( PYTHON_VERSION )
  set( ROOT_PYTHON_DIR "${VIAME_INSTALL_PREFIX}/lib/python${PYTHON_VERSION}" )
  set( OUTPUT_PYTHON_DIR "${ROOT_PYTHON_DIR}/site-packages/" )

  if( EXISTS ${VIAME_INSTALL_PREFIX}/lib/site-packages )
    set( DIR_TO_MOVE "${VIAME_INSTALL_PREFIX}/lib/site-packages" )
    file( GLOB FILES_TO_MOVE "${DIR_TO_MOVE}/*" )
    file( COPY ${FILES_TO_MOVE} DESTINATION ${OUTPUT_PYTHON_DIR} )
    file( REMOVE_RECURSE  ${DIR_TO_MOVE} )
  endif()

  if( EXISTS ${VIAME_INSTALL_PREFIX}/lib/python/site-packages )
    set( DIR_TO_MOVE "${VIAME_INSTALL_PREFIX}/lib/python/site-packages" )
    file( GLOB FILES_TO_MOVE "${DIR_TO_MOVE}/*" )
    file( COPY ${FILES_TO_MOVE} DESTINATION ${OUTPUT_PYTHON_DIR} )
    file( REMOVE_RECURSE  ${DIR_TO_MOVE} )
  endif()

  if( NOT WIN32 AND VIAME_ENABLE_OPENCV )
    set( PATCH_DIR ${VIAME_CMAKE_DIR}/../packages/patches/fletch )
    file( COPY ${PATCH_DIR}/opencv_python-3.4.0.14.dist-info DESTINATION ${OUTPUT_PYTHON_DIR} )
  endif()

  if( UNIX AND VIAME_ENABLE_PYTHON-INTERNAL )
    set( LZMA_FILE "${ROOT_PYTHON_DIR}/lzma.py" )

    set( SEARCH_CODE1
"from _lzma import *" )
    set( SEARCH_CODE2
"from _lzma import _encode_filter_properties, _decode_filter_properties" )
    set( REPL_CODE
"try:\n\
    from  _lzma import *\n\
    from  _lzma import _encode_filter_properties, _decode_filter_properties\n\
except ImportError:\n\
    from  backports.lzma import *\n\
    from  backports.lzma import _encode_filter_properties, _decode_filter_properties\n" )

    if( EXISTS ${LZMA_FILE} )
      file( READ "${LZMA_FILE}" LZMA_FILE_DATA )
      string( REPLACE "${SEARCH_CODE1}" "${REPL_CODE}" ADJ_FILE_DATA "${LZMA_FILE_DATA}" )
      string( REPLACE "${SEARCH_CODE2}" "" LZMA_FILE_DATA "${ADJ_FILE_DATA}" )
      file( WRITE "${LZMA_FILE}" "${LZMA_FILE_DATA}")
    endif()
  endif()
endif()

message( "Done" )
