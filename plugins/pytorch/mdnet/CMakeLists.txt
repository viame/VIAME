
kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/bbreg.py
  arrows/pytorch/mdnet
  bbreg )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/data_prov.py
  arrows/pytorch/mdnet
  data_prov )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/img_cropper.py
  arrows/pytorch/mdnet
  img_cropper )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
  arrows/pytorch/mdnet
  __init__ )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/model.py
  arrows/pytorch/mdnet
  model )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/options.py
  arrows/pytorch/mdnet
  options )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/prepro_data.py
  arrows/pytorch/mdnet
  prepro_data )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/pretrain_options.py
  arrows/pytorch/mdnet
  pretrain_options )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/sample_generator.py
  arrows/pytorch/mdnet
  sample_generator )

kwiver_add_python_module(
  ${CMAKE_CURRENT_SOURCE_DIR}/utils.py
  arrows/pytorch/mdnet
  utils )

