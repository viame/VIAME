# SMQTK External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_BUILD_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

set( VIAME_PROJECT_LIST ${VIAME_PROJECT_LIST} smqtk )

if( VIAME_ENABLE_PYTHON )
  FormatPassdowns( "PYTHON" VIAME_PYTHON_FLAGS )
endif()

if( VIAME_ENABLE_CUDA )
  FormatPassdowns( "CUDA" VIAME_CUDA_FLAGS )
endif()

if( VIAME_SYMLINK_PYTHON )
  set( SMQTK_PIP_CMD
    pip install --user -e .[postgres] )
else()
  # This is only required for no symlink install without a -e with older
  # versions of pip, for never versions the above command works with no -e
  set( SMQTK_PIP_CMD
    pip install --user file://${VIAME_PACKAGES_DIR}/smqtk\#egg=smqtk[postgres] )
endif()
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

set( SMQTK_PYTHON_INSTALL
  ${CMAKE_COMMAND} -E env "PYTHONPATH=${CUSTOM_PYTHONPATH}"
                          "PATH=${CUSTOM_PATH}"
                          "PYTHONUSERBASE=${VIAME_BUILD_INSTALL_PREFIX}"
    ${PYTHON_EXECUTABLE} -m ${SMQTK_PIP_CMD}
  )

ExternalProject_Add( smqtk
  DEPENDS fletch
  PREFIX ${VIAME_BUILD_PREFIX}
  SOURCE_DIR ${VIAME_PACKAGES_DIR}/smqtk
  USES_TERMINAL_BUILD 1
  CMAKE_GENERATOR ${gen}
  CMAKE_CACHE_ARGS
    -DSMQTK_BUILD_EXAMPLES:BOOL=OFF
    -DSMQTK_BUILD_LIBSVM:BOOL=ON
    -DSMQTK_BUILD_FLANN:BOOL=OFF
    -DSMQTK_INSTALL_SETUP_SCRIPT:BOOL=OFF
    ${VIAME_ARGS_COMMON}
    ${VIAME_ARGS_fletch}
    ${VIAME_PYTHON_FLAGS}
    ${VIAME_CUDA_FLAGS}

  INSTALL_DIR ${VIAME_BUILD_INSTALL_PREFIX}
  LIST_SEPARATOR "----"
  )

ExternalProject_Add_Step(smqtk install_python
  WORKING_DIRECTORY ${VIAME_PACKAGES_DIR}/smqtk
  COMMAND ${SMQTK_PYTHON_INSTALL}
  COMMENT "Installing SMQTK python files."
  DEPENDEES build
  )

ExternalProject_Add_Step(smqtk install_cleanup
  WORKING_DIRECTORY ${VIAME_PACKAGES_DIR}/smqtk
  COMMAND ${CMAKE_COMMAND}
    -DVIAME_CMAKE_DIR:PATH=${VIAME_CMAKE_DIR}
    -DVIAME_BUILD_PREFIX:PATH=${VIAME_BUILD_PREFIX}
    -DVIAME_BUILD_INSTALL_PREFIX:PATH=${VIAME_BUILD_INSTALL_PREFIX}
    -DVIAME_ENABLE_SMQTK=${VIAME_ENABLE_SMQTK}
    -P ${VIAME_SOURCE_DIR}/cmake/custom_smqtk_install.cmake
  COMMENT "Performing SMQTK Cleanup."
  DEPENDEES build
  )


if ( VIAME_FORCEBUILD )
ExternalProject_Add_Step(smqtk forcebuild
  COMMAND ${CMAKE_COMMAND}
    -E remove ${VIAME_BUILD_PREFIX}/src/smqtk-stamp/smqtk-build
  COMMENT "Removing build stamp file for build update (forcebuild)."
  DEPENDEES configure
  DEPENDERS build
  ALWAYS 1
  )
endif()

set(VIAME_ARGS_smqtk
  -Dsmqtk_DIR:PATH=${VIAME_BUILD_PREFIX}/src/smqtk-build
  )
