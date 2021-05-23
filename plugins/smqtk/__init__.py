#ckwg +28
# Copyright 2017 by Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  * Neither name of Kitware, Inc. nor the names of any contributors may be used
#    to endorse or promote products derived from this software without specific
#    prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from viame.processes.smqtk import smqtk_ingest_descriptors
from viame.processes.smqtk import smqtk_process_query
from viame.processes.smqtk import smqtk_object_track_descriptors

def __sprokit_register__():
    from kwiver.sprokit.pipeline import process_factory

    module_name = 'python:smqtk.smqtk_processes'

    if process_factory.is_process_module_loaded(module_name):
        return

    process_factory.add_process(
        'smqtk_ingest_descriptors',
        'Add descriptors and parallel UUIDs to a SMQTK descriptor index',
        smqtk_ingest_descriptors.SmqtkIngestDescriptors
    )

    process_factory.add_process(
        'smqtk_process_query',
        'Perform queries against some arbitrary descriptor index',
        smqtk_process_query.SmqtkProcessQuery
    )

    process_factory.add_process(
        'smqtk_object_track_descriptors',
        'Add descriptors to object tracks',
        smqtk_object_track_descriptors.SmqtkObjectTrackDescriptors
    )

    process_factory.mark_process_module_as_loaded(module_name)
