
###
# Sub folder options
##
if( VIAME_ENABLE_UW_PREDICTOR )
  add_subdirectory( uw_predictor )
endif()

###
# Loadable algorithms
##

find_package( OpenCV REQUIRED )

include_directories( "${OpenCV_INCLUDE_DIRS}" )
link_directories( "${OpenCV_LIBRARY_DIR}" )

set( plugin_headers
  ocv_image_enhancement.h
  ocv_debayer_filter.h
  ocv_random_hue_shift.h
  ocv_stereo_depth_map.h
  )

set( plugin_sources
  ocv_image_enhancement.cxx
  ocv_debayer_filter.cxx
  ocv_random_hue_shift.cxx
  ocv_stereo_depth_map.cxx
  )

kwiver_install_headers(
  SUBDIR     viame
  ${plugin_headers}
  )

kwiver_install_headers(
  ${CMAKE_CURRENT_BINARY_DIR}/viame_opencv_export.h
  NOPATH   SUBDIR     viame
  )

kwiver_add_library( viame_opencv
  ${plugin_headers}
  ${plugin_sources}
  )

get_target_property( results viame_opencv COMPILE_DEFINITIONS )

if( "${OpenCV_VERSION}" VERSION_LESS "3.0.0" )
  target_compile_definitions( viame_opencv PRIVATE -DVIAME_OPENCV_VER_2 )
endif()

get_target_property( results viame_opencv COMPILE_DEFINITIONS )

target_link_libraries( viame_opencv
  PUBLIC               kwiver::vital
                       kwiver::vital_algo
                       kwiver::vital_config
                       kwiver::vital_exceptions
                       kwiver::vital_logger
                       kwiver::vital_util
                       kwiver::kwiversys
                       kwiver::kwiver_algo_ocv
                       ${OpenCV_LIBRARIES}
  )

set_target_properties( viame_opencv PROPERTIES
  SOVERSION            ${VIAME_VERSION_MAJOR}
  )

algorithms_create_plugin( viame_opencv
  register_algorithms.cxx
  )

target_link_libraries( viame_opencv_plugin
  PUBLIC               kwiver::vital_vpm
  )

if( VIAME_ENABLE_PYTHON )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
    processes/opencv
    __init__ )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/ocv_multimodal_registration.py
    processes/opencv
    ocv_multimodal_registration )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/ocv_fft_filter_based_on_ref.py
    processes/opencv
    ocv_fft_filter_based_on_ref )

endif()
