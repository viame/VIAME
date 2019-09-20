# scallop_tk External Project
#
# Required symbols are:
#   VIAME_BUILD_PREFIX - where packages are built
#   VIAME_BUILD_INSTALL_PREFIX - directory install target
#   VIAME_PACKAGES_DIR - location of git submodule packages
#   VIAME_ARGS_COMMON -
##

# Configure faster-rcnn repository in packages to point to internal caffe
if( NOT WIN32 )
  ExternalProject_Add( py-faster-rcnn
    DEPENDS fletch
    PREFIX ${VIAME_BUILD_PREFIX}
    SOURCE_DIR ${VIAME_PACKAGES_DIR}/py-faster-rcnn/lib
    CONFIGURE_COMMAND ${CMAKE_COMMAND} -E create_symlink
      ${VIAME_FLETCH_BUILD_DIR}/build/src/Caffe-build
      ${VIAME_PACKAGES_DIR}/py-faster-rcnn/caffe-fast-rcnn
    BUILD_COMMAND cd ${VIAME_PACKAGES_DIR}/py-faster-rcnn/lib && make
    INSTALL_COMMAND ${CMAKE_COMMAND}
      -DVIAME_CMAKE_DIR:PATH=${VIAME_CMAKE_DIR}
      -P ${VIAME_SOURCE_DIR}/cmake/custom_faster_rcnn_install.cmake
    )
endif()
