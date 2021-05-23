# If we make a non-standalone module use this
#kwiver_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
#  processes/camtrawl
#  __init__)

# Just install module as a standalone file to the pythonpath

set(_rel_modnames
  algos
  demo
  expt
  imutils
  processes
  __init__
  __main__
  )

#kwiver_add_python_module(${CMAKE_CURRENT_SOURCE_DIR}/camtrawl/processes.py
foreach (rel_modname IN ITEMS ${_rel_modnames})
  string(REPLACE "." "/" rel_modpath_noext ${rel_modname})
  kwiver_add_python_module("${CMAKE_CURRENT_SOURCE_DIR}/processes/camtrawl/${rel_modpath_noext}.py"
    "processes/camtrawl" "${rel_modname}")
endforeach()
