
# Old Example Checks
if( EXISTS ${VIAME_BUILD_INSTALL_PREFIX}/examples/detector_pipelines )
  message( FATAL_ERROR "Your examples directory is too old. As of VIAME 0.9.7, "
    "the examples directory has been refactored. Delete [build-dir]/install/examples, "
    "or alternatively consider a fresh re-build." )  
endif()

# Check for old VTK versions
if( EXISTS ${VIAME_FLETCH_BUILD_DIR}/CMakeCache.txt )
  file( READ ${VIAME_FLETCH_BUILD_DIR}/CMakeCache.txt TMPTXT )
  string( FIND "${TMPTXT}" "VTK_SELECT_VERSION:STRING=6.2" matchres )
  message( STATUS ${matchres} )
  if( NOT ${matchres} EQUAL -1 )
    message( FATAL_ERROR "Your prior build was with VTK 6.2, which has been updated "
      "to version 8.0 for the latest GUIs. A full re-build is recommended, but "
      "alternatively you can delete [build]/build/src/fletch-build/CMakeCache.txt, "
      "[build]/build/src/fletch-build/build/src/VTK*, and "
      "[build]/build/src/fletch-stamp and [build]/build/src/vivia-build" )
  endif()
endif()
