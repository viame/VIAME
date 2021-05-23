
kwiver_create_python_init( arrows/tensorflow )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/tf_detector.py
  arrows/tensorflow
  tf_detector )
