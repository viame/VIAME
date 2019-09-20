# Python Dependency External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_BUILD_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

# --------------------- ADD ANY EXTRA PYTHON DEPS HERE -------------------------

set( VIAME_PYTHON_DEPS numpy matplotlib )

if( VIAME_ENABLE_OPENCV )
  set( VIAME_PYTHON_DEPS opencv-python ${VIAME_PYTHON_DEPS} )
endif()

if( VIAME_ENABLE_CAMTRAWL )
  set( VIAME_PYTHON_DEPS ubelt ${VIAME_PYTHON_DEPS} )
endif()

if( VIAME_ENABLE_TENSORFLOW )
  if( VIAME_ENABLE_CUDA )
    set( VIAME_PYTHON_DEPS tensorflow-gpu ${VIAME_PYTHON_DEPS} )
  else()
    set( VIAME_PYTHON_DEPS tensorflow ${VIAME_PYTHON_DEPS} )
  endif()
endif()

if( VIAME_ENABLE_PYTOCH AND NOT VIAME_ENABLE_PYTORCH-CORE )
  set( torch torchvision ${VIAME_PYTHON_DEPS} )
endif()

# ------------------------------------------------------------------------------

set( PYTHON_BASEPATH
  ${VIAME_BUILD_INSTALL_PREFIX}/lib/python${PYTHON_VERSION} )

if( WIN32 )
  set( CUSTOM_PYTHONPATH
    ${PYTHON_BASEPATH}/site-packages;${PYTHON_BASEPATH}/dist-packages )
  set( CUSTOM_PATH
    ${VIAME_BUILD_INSTALL_PREFIX}/bin;$ENV{PATH} )
  string( REPLACE ";" "----" CUSTOM_PYTHONPATH "${CUSTOM_PYTHONPATH}" )
  string( REPLACE ";" "----" CUSTOM_PATH "${CUSTOM_PATH}" )
else()
  set( CUSTOM_PYTHONPATH
    ${PYTHON_BASEPATH}/site-packages:${PYTHON_BASEPATH}/dist-packages )
  set( CUSTOM_PATH
    ${VIAME_BUILD_INSTALL_PREFIX}/bin:$ENV{PATH} )
endif()

set( VIAME_PYTHON_DEPS_DEPS fletch )

if( VIAME_ENABLE_SMQTK )
  set( VIAME_PYTHON_DEPS_DEPS smqtk ${VIAME_PYTHON_DEPS_DEPS} )
endif()

foreach( DEP ${VIAME_PYTHON_DEPS} )

  set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} ${DEP} )

  set( PYTHON_DEP_PIP_CMD
      pip install --user ${DEP} )

  set( PYTHON_DEP_INSTALL
    ${CMAKE_COMMAND} -E env "PYTHONPATH=${CUSTOM_PYTHONPATH}"
                            "PATH=${CUSTOM_PATH}"
                            "PYTHONUSERBASE=${VIAME_BUILD_INSTALL_PREFIX}"
      ${PYTHON_EXECUTABLE} -m ${PYTHON_DEP_PIP_CMD}
    )

  ExternalProject_Add( ${DEP}
    DEPENDS ${VIAME_PYTHON_DEPS_DEPS}
    PREFIX ${VIAME_BUILD_PREFIX}
    SOURCE_DIR ${VIAME_CMAKE_DIR}
    USES_TERMINAL_BUILD 1
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ${PYTHON_DEP_INSTALL}
    INSTALL_COMMAND ""
    INSTALL_DIR ${VIAME_BUILD_INSTALL_PREFIX}
    LIST_SEPARATOR "----"
    )
endforeach()
