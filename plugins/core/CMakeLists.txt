# Build / Install Plugin containing core algorithm implementations

set( plugin_headers
  add_timestamp_from_filename.h
  auto_detect_transform.h
  convert_head_tail_points.h
  empty_detector.h
  filename_to_timestamp.h
  notes_to_attributes.h
  read_detected_object_set_fishnet.h
  read_detected_object_set_habcam.h
  read_detected_object_set_oceaneyes.h
  read_detected_object_set_viame_csv.h
  read_object_track_set_viame_csv.h
  write_detected_object_set_viame_csv.h
  write_object_track_set_viame_csv.h
  )

set( plugin_sources
  add_timestamp_from_filename.cxx
  auto_detect_transform.cxx
  convert_head_tail_points.cxx
  empty_detector.cxx
  filename_to_timestamp.cxx
  notes_to_attributes.cxx
  read_detected_object_set_fishnet.cxx
  read_detected_object_set_habcam.cxx
  read_detected_object_set_oceaneyes.cxx
  read_detected_object_set_viame_csv.cxx
  read_object_track_set_viame_csv.cxx
  write_detected_object_set_viame_csv.cxx
  write_object_track_set_viame_csv.cxx
  )

kwiver_install_headers(
  SUBDIR     viame
  ${plugin_headers}
  )

kwiver_install_headers(
  ${CMAKE_CURRENT_BINARY_DIR}/viame_core_export.h
  NOPATH   SUBDIR     viame
  )

kwiver_add_library( viame_core
  ${plugin_headers}
  ${plugin_sources}
  )

set( CORE_LINK_LIBRARIES
  kwiver::vital
  kwiver::vital_algo
  kwiver::vital_config
  kwiver::vital_exceptions
  kwiver::vital_logger
  kwiver::vital_util
  kwiver::kwiversys )

# VXL is used in some parsers for aux functionality if enabled
if( VIAME_ENABLE_VXL )
  find_package( VXL REQUIRED )
  include( ${VXL_CMAKE_DIR}/UseVXL.cmake )
  include_directories( SYSTEM ${VXL_CORE_INCLUDE_DIR} )
  include_directories( SYSTEM ${VXL_VGL_INCLUDE_DIR} )
  link_directories( ${VXL_LIBRARY_DIR} )
  add_definitions( -DVIAME_ENABLE_VXL )
  set( AUX_LINK_LIBRARIES vgl ${AUX_LINK_LIBRARIES} )
endif()

# OpenCV is used in some parsers for aux functionality if enabled
if( VIAME_ENABLE_OPENCV )
  find_package( OpenCV REQUIRED )
  include_directories( "${OpenCV_INCLUDE_DIRS}" )
  link_directories( "${OpenCV_LIBRARY_DIR}" )
  add_definitions( -DVIAME_ENABLE_OPENCV )
  set( AUX_LINK_LIBRARIES
       ${OpenCV_LIBRARIES}
       kwiver::kwiver_algo_ocv
       ${AUX_LINK_LIBRARIES} )
endif()

target_link_libraries( viame_core
  PUBLIC               ${CORE_LINK_LIBRARIES}
                       ${AUX_LINK_LIBRARIES}
  )

set_target_properties( viame_core PROPERTIES
  SOVERSION            ${VIAME_VERSION_MAJOR}
  )

algorithms_create_plugin( viame_core
  register_algorithms.cxx
  )

target_link_libraries( viame_core_plugin
  PUBLIC               kwiver::vital_vpm
  )

find_package( Boost ${KWIVER_BOOST_VERSION} REQUIRED
    COMPONENTS
      chrono
      filesystem
      system)

include_directories( SYSTEM ${Boost_INCLUDE_DIRS} )
link_directories( ${Boost_LIBRARY_DIRS} )

# Add process library
set( process_headers
  align_multimodal_imagery_process.h
  extract_desc_ids_for_training_process.h
  filter_frame_process.h
  filter_object_tracks_process.h
  full_frame_tracker_process.h
  track_conductor_process.h
  write_homography_list_process.h
)

set( process_sources
  register_processes.cxx
  align_multimodal_imagery_process.cxx
  extract_desc_ids_for_training_process.cxx
  filter_frame_process.cxx
  filter_object_tracks_process.cxx
  full_frame_tracker_process.cxx
  track_conductor_process.cxx
  write_homography_list_process.cxx
)

kwiver_add_plugin( viame_processes_core
  SUBDIR           ${viame_plugin_process_subdir}
  SOURCES          ${process_sources}
                   ${private_headers}
  PRIVATE          ${CORE_LINK_LIBRARIES}
                   kwiver::sprokit_pipeline
                   kwiver::kwiver_algo_core
                   kwiver::kwiver_adapter
                   kwiver::vital_vpm
                   ${Boost_SYSTEM_LIBRARY}
                   ${Boost_FILESYSTEM_LIBRARY}
 )

if( VIAME_ENABLE_PYTHON )

  kwiver_create_python_init( arrows/core )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/npy_image_normalization.py
    arrows/core
    npy_image_normalization )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
    processes/core
    __init__ )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/utility_processes.py
    processes/core
    utility_processes )

endif()
