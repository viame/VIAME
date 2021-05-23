
set( Python_FOUND TRUE CACHE INTERNAL "Forced" FORCE )

set( Python_VERSION_MAJOR "3" CACHE INTERNAL "Forced" FORCE )
set( Python_VERSION_MINOR "6" CACHE INTERNAL "Forced" FORCE )
set( Python_VERSION_PATCH "5" CACHE INTERNAL "Forced" FORCE )

set( Python_INCLUDE_DIR ${VIAME_INSTALL_PREFIX}/include CACHE PATH "Forced" FORCE )

if( WIN32 )
  set( Python_EXECUTABLE ${VIAME_INSTALL_PREFIX}/bin/python.exe CACHE PATH "Forced" FORCE )
  set( Python_LIBRARY ${VIAME_INSTALL_PREFIX}/lib/python3.lib CACHE PATH "Forced" FORCE )
else()
  set( Python_EXECUTABLE ${VIAME_INSTALL_PREFIX}/bin/python CACHE PATH "Forced" FORCE )
  set( Python_LIBRARY ${VIAME_INSTALL_PREFIX}/lib/libpython3.so CACHE PATH "Forced" FORCE )
endif()
