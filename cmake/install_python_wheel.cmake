file( GLOB _wheels LIST_DIRECTORIES FALSE ${WHEEL_DIR}/* )
execute_process(
  COMMAND ${Python_EXECUTABLE} -m pip install --user ${_wheels}
  RESULT_VARIABLE _result
  WORKING_DIRECTORY ${WHEEL_DIR}
  )

if( NOT _result EQUAL 0 )
  message( FATAL_ERROR "pip install exited with non-zero status: ${_result}" )
endif()
