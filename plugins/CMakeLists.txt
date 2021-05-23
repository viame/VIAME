
###
# add all plugin subdirectories below

set( viame_plugin_subdir           viame )
set( viame_plugin_process_subdir   ${viame_plugin_subdir}/processes )

add_subdirectory( core )
add_subdirectory( hello_world )

if( VIAME_ENABLE_PYTHON )
  kwiver_create_python_init( arrows )
  kwiver_create_python_init( processes )
endif()

if( VIAME_ENABLE_OPENCV )
  add_subdirectory( opencv )
endif()

if( VIAME_ENABLE_ITK )
  add_subdirectory( itk )
endif()

if( VIAME_ENABLE_SCALLOP_TK )
  add_subdirectory( scallop_tk )
endif()

if( VIAME_ENABLE_CAMTRAWL )
  add_subdirectory( camtrawl )
endif()

if( VIAME_ENABLE_MATLAB )
  add_subdirectory( matlab )
endif()

if( VIAME_ENABLE_SMQTK )
  add_subdirectory( smqtk )
endif()

if( VIAME_ENABLE_TENSORFLOW )
  add_subdirectory( tensorflow )
endif()

if( VIAME_ENABLE_PYTORCH )
  add_subdirectory( pytorch )
endif()

if( VIAME_ENABLE_VXL )
  add_subdirectory( vxl )
endif()
