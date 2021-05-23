#ckwg +28
# Copyright 2018 by Kitware, Inc.
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

import json

from kwiver.sprokit.processes.kwiver_process import KwiverProcess
from kwiver.sprokit.pipeline import process

from kwiver.vital.types import new_descriptor, DescriptorSet

import smqtk.utils.plugin

import psycopg2


class SmqtkObjectTrackDescriptors (KwiverProcess):
    def __init__(self, conf):
        KwiverProcess.__init__(self, conf)

        # register python config file
        self.add_config_trait(
            'config_file', 'config_file', '',
            'Path to the json configuration file for the descriptor index to fetch from.'
        )
        self.declare_config_using_trait('config_file')

        self.add_config_trait(
            'video_name', 'video_name', '',
            'Video name'
        )
        self.declare_config_using_trait('video_name')

        self.add_config_trait(
            'conn_str', 'conn_str', '',
            'Connection string'
        )
        self.declare_config_using_trait('conn_str')

        # set up required flags
        optional = process.PortFlags()
        required = process.PortFlags()
        required.add(self.flag_required)

        self.declare_input_port_using_trait('object_track_set', required)
        self.declare_output_port_using_trait('object_track_set', optional)

    def _configure(self):
        self.config_file = self.config_value('config_file')
        self.video_name = self.config_value('video_name')
        self.conn_str = self.config_value('conn_str')

        # parse json file
        with open(self.config_file) as data_file:
            self.json_config = json.load(data_file)

        #: :type: smqtk.representation.DescriptorIndex
        self.smqtk_descriptor_index = smqtk.utils.plugin.from_plugin_config(
            self.json_config,
            smqtk.representation.get_descriptor_index_impls()
        )

        self.conn = psycopg2.connect(self.conn_str)
        self.current_idx = 0

        self._base_configure()

    def _step(self):
        object_tracks = self.grab_input_using_trait('object_track_set')

        for object_track in object_tracks.tracks():
            for track_state in object_track:
                if track_state.frame_id == self.current_idx:
                    cur = self.conn.cursor()
                    cur.execute("SELECT track_descriptor.uid FROM track_descriptor "
                                "INNER JOIN track_descriptor_track ON track_descriptor.uid = track_descriptor_track.uid "
                                "INNER JOIN track_descriptor_history ON track_descriptor.uid = track_descriptor_history.uid "
                                "WHERE track_descriptor.video_name = %(video_name)s AND track_descriptor_history.frame_number = %(frame_number)s AND track_descriptor_track.track_id = %(track_id)s",
                                {
                                    "video_name": self.video_name,
                                    "frame_number": track_state.frame_id,
                                    "track_id": object_track.id,
                                })
                    rows = list(cur.fetchall())
                    if len(rows) != 1:
                        raise RuntimeError("Could not get track descriptor")
                    uid = rows[0][0]

                    smqtk_descriptor = self.smqtk_descriptor_index.get_descriptor(uid)

                    vital_descriptor = new_descriptor(len(smqtk_descriptor.vector()), "d")
                    vital_descriptor[:] = smqtk_descriptor.vector()

                    track_state.detection.set_descriptor(vital_descriptor)

                    print("Finished track state: %i %i" % (object_track.id, track_state.frame_id))

        self.push_to_port_using_trait('object_track_set', object_tracks)

        self.current_idx += 1

        self._base_step()
