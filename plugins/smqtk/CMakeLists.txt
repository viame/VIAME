if( VIAME_ENABLE_PYTHON AND VIAME_ENABLE_SMQTK )

  # Processes
  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
    processes/smqtk
    __init__ )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/smqtk_ingest_descriptors.py
    processes/smqtk
    smqtk_ingest_descriptors )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/smqtk_process_query.py
    processes/smqtk
    smqtk_process_query )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/smqtk_object_track_descriptors.py
    processes/smqtk
    smqtk_object_track_descriptors )

  # Functions and other utilities
  kwiver_create_python_init( arrows/smqtk )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/smqtk_train_svm_models.py
    arrows/smqtk
    smqtk_train_svm_models )

  kwiver_add_python_module(
    ${CMAKE_CURRENT_SOURCE_DIR}/smqtk_trainer.py
    arrows/smqtk
    smqtk_trainer )

endif()
