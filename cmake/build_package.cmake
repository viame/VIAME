###
# top level build file for NOAA VIAME Package Util
##

set( CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/CMake ${CMAKE_MODULE_PATH} )

include( installation_blacklist )

if( NOT DEFINED VIAME_INSTALL_DIR )
  set( VIAME_INSTALL_DIR "${VIAME_BUILD_INSTALL_PREFIX}")
endif()

set( FIXUP_LIBS )
set( FIXUP_DIRS )

macro( add_to_fixup_libs dir_path )
  if( WIN32 )
    file( GLOB FILES_TO_ADD "${dir_path}/*.dll" )
    set( FIXUP_LIBS ${FIXUP_LIBS} ${FILES_TO_ADD} )
  else()
    file( GLOB FILES_TO_ADD "${dir_path}/*.so" )
    set( FIXUP_LIBS ${FIXUP_LIBS} ${FILES_TO_ADD} )
  endif()
endmacro()

file( GLOB VIAME_BIN_FILES "${VIAME_INSTALL_DIR}/bin/*"  )
list( APPEND FIXUP_DIRS ${VIAME_INSTALL_DIR}/bin )

file( GLOB VIAME_LIB_FILES "${VIAME_INSTALL_DIR}/lib/*"  )
list( APPEND FIXUP_DIRS ${VIAME_INSTALL_DIR}/lib )

file( APPEND VIAME_LIB_FILES "${VIAME_INSTALL_DIR}/lib64/*"  )
list( APPEND FIXUP_DIRS ${VIAME_INSTALL_DIR}/lib64 )

file( GLOB VIAME_INCLUDE_FILES "${VIAME_INSTALL_DIR}/include/*"  )
list( APPEND FIXUP_DIRS ${VIAME_INSTALL_DIR}/include )

file( GLOB VIAME_GUI_PLUGINS_FILES "${VIAME_INSTALL_DIR}/plugins/*"  )
list( APPEND FIXUP_DIRS ${VIAME_INSTALL_DIR}/plugins )

file( GLOB VIAME_SPRKIT_PLUGINS_FILES "${VIAME_INSTALL_DIR}/lib/sprokit/*" )
list( APPEND FIXUP_DIRS ${VIAME_INSTALL_DIR}/lib/sprokit )

file( GLOB VIAME_VIAME_PLUGINS_FILES "${VIAME_INSTALL_DIR}/lib/modules/*" )
list( APPEND FIXUP_DIRS ${VIAME_INSTALL_DIR}/lib/modules )
add_to_fixup_libs( ${VIAME_INSTALL_DIR}/lib/modules )

file( GLOB VIAME_PLUGIN_PLUGINS_FILES "${VIAME_INSTALL_DIR}/lib/modules/plugin_explorer/*" )
list( APPEND FIXUP_DIRS ${VIAME_INSTALL_DIR}/lib/modules/plugin_explorer )

if( VIAME_ENABLE_MATLAB )
  get_filename_component( MATLAB_LIB_PATH ${Matlab_MEX_LIBRARY} DIRECTORY )
  set( MATLAB_DLL_PATH ${Matlab_ROOT_DIR}/bin/win64 )
  list( APPEND FIXUP_DIRS ${MATLAB_LIB_PATH} )
  list( APPEND FIXUP_DIRS ${MATLAB_DLL_PATH} )
endif()

if( VIAME_ENABLE_CUDNN )
  get_filename_component( CUDNN_LIB_PATH ${CUDNN_LIBRARY} DIRECTORY )
  list( APPEND FIXUP_DIRS ${CUDNN_LIB_PATH} )
endif()

set( CPACK_PACKAGE_DESCRIPTION_SUMMARY "VIAME" )
set( CPACK_PACKAGE_VENDOR              "Kitware, NOAA, and Friends" )
set( CPACK_PACKAGE_DESCRIPTION_FILE    "${CMAKE_CURRENT_SOURCE_DIR}/README.md" )
set( CPACK_RESOURCE_FILE_LICENSE       "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE.txt" )
set( CPACK_PACKAGE_VERSION_MAJOR       "${VIAME_VERSION_MAJOR}" )
set( CPACK_PACKAGE_VERSION_MINOR       "${VIAME_VERSION_MINOR}" )
set( CPACK_PACKAGE_VERSION_PATCH       "${VIAME_VERSION_PATCH}" )
set( CPACK_PACKAGE_INSTALL_DIRECTORY   "VIAME-${CMake_VERSION_MAJOR}.${CMake_VERSION_MINOR}" )

include( InstallRequiredSystemLibraries )

#foreach( path_id ${FIXUP_DIRS} )
#  if( WIN32 )
#    file( GLOB FILES_TO_ADD "${path_id}/*.dll" )
#    set( FIXUP_LIBS ${FIXUP_LIBS} ${FILES_TO_ADD} )
#  else()
#    file( GLOB FILES_TO_ADD "${path_id}/*.so" )
#    set( FIXUP_LIBS ${FIXUP_LIBS} ${FILES_TO_ADD} )
#  endif()
#endforeach()

if( CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS )
  set( CMAKE_INSTALL_UCRT_LIBRARIES TRUE )
  install( PROGRAMS ${CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS} DESTINATION bin COMPONENT System )
endif()

install( DIRECTORY ${VIAME_INSTALL_DIR}/ DESTINATION . )

if( WIN32 )
  install( FILES ${VIAME_CMAKE_DIR}/setup_viame.bat.install
    DESTINATION .
    RENAME setup_viame.bat
    )
else()
  install( FILES ${VIAME_CMAKE_DIR}/setup_viame.sh.install
    DESTINATION .
    RENAME setup_viame.sh
    )
endif()

#    if( WIN32 AND NOT UNIX )
#      set( CPACK_PACKAGE_ICON "${CMake_SOURCE_DIR}/Utilities/Release\\\\InstallIcon.bmp")
#      set( CPACK_NSIS_INSTALLED_ICON_NAME "bin\\\\MyExecutable.exe")
#      set( CPACK_NSIS_DISPLAY_NAME "${CPACK_PACKAGE_INSTALL_DIRECTORY} My Famous Project")
#      set( CPACK_NSIS_HELP_LINK "http:\\\\\\\\www.my-project-home-page.org")
#      set( CPACK_NSIS_URL_INFO_ABOUT "http:\\\\\\\\www.my-personal-home-page.com")
#      set( CPACK_NSIS_CONTACT "me@my-personal-home-page.com")
#      set( CPACK_NSIS_MODIFY_PATH ON)
#   else( WIN32 AND NOT UNIX )
#      set( CPACK_STRIP_FILES "bin/MyExecutable" )
#      set( CPACK_SOURCE_STRIP_FILES "" )
#   endif()

#SET( CPACK_PACKAGE_EXECUTABLES "MyExecutable" "My Executable" )
include( CPack )
