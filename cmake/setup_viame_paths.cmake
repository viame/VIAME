
if( APPLE )
  set( SETUP_READLINK_CMD "this_dir=$(cd \"$(dirname \"$BASH_SOURCE[0]\")\" && pwd)" )
  set( SETUP_LIBRARY_PATH "export DYLD_FALLBACK_LIBRARY_PATH=$this_dir/lib:$this_dir/lib64:$DYLD_FALLBACK_LIBRARY_PATH" )
  set( SETUP_QT_PLUGIN_PATH "#export QT_PLUGIN_PATH=$this_dir/lib/qt4/plugins" )
else()
  set( SETUP_READLINK_CMD "this_dir=$(readlink -f $(dirname $0))" )
  set( SETUP_LIBRARY_PATH "export LD_LIBRARY_PATH=$this_dir/lib:$this_dir/lib64:$LD_LIBRARY_PATH" )
  set( SETUP_QT_PLUGIN_PATH "export QT_PLUGIN_PATH=$this_dir/lib/qt4/plugins" )
endif()

if( VIAME_ENABLE_MATLAB )
  get_filename_component( Matlab_LIBRARY_DIR "${Matlab_ENG_LIBRARY}" DIRECTORY )

  if( APPLE )
    set( SETUP_MATLAB_LIBRARY_PATH "export DYLD_FALLBACK_LIBRARY_PATH=$DYLD_FALLBACK_LIBRARY_PATH:${Matlab_LIBRARY_DIR}" )
  else()
    set( SETUP_MATLAB_LIBRARY_PATH "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64:/usr/lib:${Matlab_LIBRARY_DIR}" )
  endif()
endif()

if( VIAME_ENABLE_PYTHON )
  get_filename_component( PYTHON_LIBRARY_DIR "${PYTHON_LIBRARY}" DIRECTORY )
  get_filename_component( PYTHON_ROOT_DIR "${PYTHON_LIBRARY_DIR}" DIRECTORY )

  set( SETUP_PYTHON_LOCATION "export PYTHON_INSTALL_DIR=${PYTHON_ROOT_DIR}" )
  set( SETUP_PYTHON_LIBRARY_PATH "export PYTHON_LIBRARY=${PYTHON_LIBRARY}" )
endif()

set( SETUP_CUSTOM_TERMINAL "export PS1=\"\${PS1//\"(viame) \"/}\"\nexport PS1=\"(viame) \${PS1//\"(base) \"/}\"" )
