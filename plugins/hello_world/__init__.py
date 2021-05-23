
from viame.processes.hello_world import hello_world_detector
from viame.processes.hello_world import hello_world_filter


def __sprokit_register__():
    from kwiver.sprokit.pipeline import process_factory

    module_name = 'python:hello_world.hello_world_detector'

    if process_factory.is_process_module_loaded( module_name ):
        return

    process_factory.add_process('hello_world_detector', 'Example detector',
                                hello_world_detector.hello_world_detector )
    process_factory.add_process('hello_world_filter', 'Example filter',
                                hello_world_filter.hello_world_filter )

    process_factory.mark_process_module_as_loaded( module_name )
