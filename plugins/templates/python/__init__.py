
from viame.processes.@template_dir@ import @template@_detector

def __sprokit_register__():
    from kwiver.sprokit.pipeline import process_factory

    module_name = 'python:@template_dir@.@template@_detector'

    if process_factory.is_process_module_loaded( module_name ):
        return

    process_factory.add_process( '@template@_detector', 'Example detector', \
      @template@_detector.@template@_detector )

    process_factory.mark_process_module_as_loaded( module_name )
