set( EXAMPLE_INSTALL_FILES
     README.rst )


if( VIAME_ENABLE_PYTORCH )
  if( WIN32 )
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         train_st_tracker_viame_csv.bat )
  else()
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         train_st_tracker_viame_csv.sh )
  endif()
endif()

###
# Install pipelines to example directory
##
install( FILES       ${EXAMPLE_INSTALL_FILES}
         DESTINATION examples/object_tracker_training )
