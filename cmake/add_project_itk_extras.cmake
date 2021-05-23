# ITK External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} itk_module_tps )

# -------------------------------------- C/C++ -------------------------------------------

ExternalProject_Add( itk_module_tps
  DEPENDS fletch
  PREFIX ${VIAME_BUILD_PREFIX}
  SOURCE_DIR ${VIAME_PACKAGES_DIR}/itk-modules/trimmed-point-set
  CMAKE_GENERATOR ${gen}
  CMAKE_ARGS
    ${VIAME_ARGS_COMMON}
    ${VIAME_ARGS_fletch}
    ${VIAME_ARGS_VXL}
    ${VIAME_ARGS_ITK}
    -DBUILD_TESTING:BOOL=OFF
  INSTALL_DIR ${VIAME_INSTALL_PREFIX}
)

if( VIAME_FORCEBUILD )
  ExternalProject_Add_Step( itk_module_tps forcebuild
    COMMAND ${CMAKE_COMMAND}
      -E remove ${VIAME_BUILD_PREFIX}/src/itk_module_tps-stamp/itk_module_tps-build
    COMMENT "Removing build stamp file for build update (forcebuild)."
    DEPENDEES configure
    DEPENDERS build
    ALWAYS 1
  )
endif()

# -------------------------------------- Python ------------------------------------------

if( VIAME_ENABLE_PYTHON )

  if( WIN32 )
    string( REPLACE ";" "----" VIAME_PYTHON_PATH "${VIAME_PYTHON_PATH}" )
    string( REPLACE ";" "----" VIAME_EXECUTABLES_PATH "${VIAME_EXECUTABLES_PATH}" )
  endif()

  if( VIAME_SYMLINK_PYTHON )
    set( KEYPOINTGUI_PIP_CMD
      pip install --user -e . )
  else()
    # This is only required for no symlink install without a -e with older
    # versions of pip, for never versions the above command works with no -e
    set( KEYPOINTGUI_PIP_CMD
      pip install --user file://${VIAME_PACKAGES_DIR}/itk-modules/keypointgui )
  endif()

  set( KEYPOINTGUI_INSTALL
    ${CMAKE_COMMAND} -E env "PYTHONPATH=${VIAME_PYTHON_PATH}"
                            "PATH=${VIAME_EXECUTABLES_PATH}"
                            "PYTHONUSERBASE=${VIAME_INSTALL_PREFIX}"
      ${Python_EXECUTABLE} -m ${KEYPOINTGUI_PIP_CMD}
    )

  ExternalProject_Add( keypointgui
    DEPENDS fletch python-deps wxPython
    PREFIX ${VIAME_BUILD_PREFIX}
    SOURCE_DIR  ${VIAME_PACKAGES_DIR}/itk-modules/keypointgui
    BUILD_IN_SOURCE 1
    USES_TERMINAL_BUILD 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ${KEYPOINTGUI_INSTALL}
    INSTALL_COMMAND ""
    INSTALL_DIR ${VIAME_INSTALL_PREFIX}
    LIST_SEPARATOR "----"
    )
endif()
  
