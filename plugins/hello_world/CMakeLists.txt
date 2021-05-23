###
# Loadable algorithms

set( plugin_headers
  hello_world_detector.h
  hello_world_filter.h
  )

set( plugin_sources
  hello_world_detector.cxx
  hello_world_filter.cxx
  )

kwiver_install_headers(
  SUBDIR     viame
  ${plugin_headers}
  )

kwiver_install_headers(
  ${CMAKE_CURRENT_BINARY_DIR}/viame_hello_world_export.h
  NOPATH   SUBDIR     viame
  )

kwiver_add_library( viame_hello_world
  ${plugin_headers}
  ${plugin_sources}
  )

target_link_libraries( viame_hello_world
  PUBLIC               kwiver::vital
                       kwiver::vital_algo
                       kwiver::vital_config
                       kwiver::vital_exceptions
                       kwiver::vital_logger
                       kwiver::vital_util
                       ${OpenCV_LIBRARIES}
  )

set_target_properties( viame_hello_world PROPERTIES
  SOVERSION            ${VIAME_VERSION_MAJOR}
  )

algorithms_create_plugin( viame_hello_world
  register_algorithms.cxx
  )
  
target_link_libraries( viame_hello_world_plugin
  PUBLIC               kwiver::vital_vpm
  )

if( VIAME_ENABLE_PYTHON )
  kwiver_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
    processes/hello_world
    __init__)

  kwiver_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/hello_world_detector.py
    processes/hello_world
    hello_world_detector)

  kwiver_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/hello_world_filter.py
    processes/hello_world
    hello_world_filter)
endif()
