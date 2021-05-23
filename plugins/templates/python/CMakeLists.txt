###
# Loadable algorithms

if( VIAME_ENABLE_PYTHON )
  kwiver_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
    processes/@template_dir@
    __init__)

  kwiver_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/@template@_detector.py
    processes/@template_dir@
    @template@_detector)
endif()
