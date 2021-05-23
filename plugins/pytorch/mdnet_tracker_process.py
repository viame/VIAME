# ckwg +29
# Copyright 2019-2020 by Kitware, Inc.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import sys
import numpy as np

from kwiver.sprokit.processes.kwiver_process import KwiverProcess
from kwiver.sprokit.pipeline import process

from kwiver.vital.types import (
    BoundingBoxD, DetectedObject, DetectedObjectSet,
    Image, ObjectTrackState, ObjectTrackSet, Track,
)

import viame.arrows.pytorch.mdnet_tracker as mdnet

# ------------------------------------------------------------------------------
class MDNetTrackerProcess(KwiverProcess):
    def __init__(self, conf):
        KwiverProcess.__init__(self, conf)

        # Config file
        self.add_config_trait("weights_file", "weights_file",
          'models/mdnet_seed.pth',
          'MDNet initial weight file for each object track.')
        self.declare_config_using_trait("weights_file")
        self.add_config_trait("init_method", "init_method",
          'external_only',
          'Method for initializing new tracks, can be: external_only or '
          'using_detections.')
        self.declare_config_using_trait("init_method")
        self.add_config_trait("init_threshold", "init_threshold",
          '0.20',
          'If tracking multiple targets, the initialization threshold over '
          'detected object classifications for new tracks')
        self.declare_config_using_trait("init_threshold")
        self.add_config_trait("iou_threshold", "iou_threshold",
          '0.50',
          'If tracking multiple targets, the initialization threshold over '
          'box intersections in order to generate new tracks')
        self.declare_config_using_trait("iou_threshold")
        self.add_config_trait("type_string", "type_string",
          '',
          'If non-empty set the output track to be a track of this '
          'object category.')
        self.declare_config_using_trait("type_string")

        # add non-standard input and output elements
        self.add_port_trait( "initializations",
          "object_track_set", "Input external track initializations" )
        self.add_port_trait( "recommendations",
          "object_track_set", "Input external track recommendations" )
        self.add_port_trait( "evaluation_requests",
          "detected_object_set", "External detections to test if target" )
        self.add_port_trait( "evaluations",
          "detected_object_set", "Completed evaluations with scores" )

        # set up required flags
        optional = process.PortFlags()
        required = process.PortFlags()
        required.add(self.flag_required)

        # input port (port-name,flags)
        self.declare_input_port_using_trait('image', required)
        self.declare_input_port_using_trait('timestamp', required)
        self.declare_input_port_using_trait('detected_object_set', optional)
        self.declare_input_port_using_trait('initializations', required)
        self.declare_input_port_using_trait('recommendations', optional)
        self.declare_input_port_using_trait('evaluation_requests', optional)

        # output port (port-name,flags)
        self.declare_output_port_using_trait('timestamp', optional)
        self.declare_output_port_using_trait('object_track_set', optional)
        self.declare_output_port_using_trait('evaluations', optional)

    # --------------------------------------------------------------------------
    def _configure(self):
        # Configuration parameters
        self._weights_file = str(self.config_value('weights_file'))
        self._init_threshold = str(self.config_value('init_method'))
        self._init_threshold = float(self.config_value('init_threshold'))
        self._iou_threshold = float(self.config_value('iou_threshold'))
        self._type_string = str(self.config_value('type_string'))

        # Load model only once across all tracks for speed
        mdnet.opts['model_path'] = mdnet.MDNet(self._weights_file)

        # Persistent state variables
        self._trackers = dict()
        self._tracks = dict()
        self._track_init_frames = dict()
        self._last_frame_id = -1
        self._base_configure()

    # --------------------------------------------------------------------------
    def format_image(self, image):
        if not isinstance(image, np.ndarray):
            img_npy = image.image().asarray().astype('uint8')
            # Greyscale to color image if necessary
            if len(np.shape(img_npy)) > 2 and np.shape(img_npy)[2] == 1:
                img_npy = img_npy[:,:,0]
            if len(np.shape(img_npy)) == 2:
                img_npy = np.stack((img_npy,)*3, axis=-1)
            return img_npy
        return image

    # --------------------------------------------------------------------------
    def _step(self):

        # Get all inputs even ones we don't use
        in_img_c = self.grab_input_using_trait('image')
        timestamp = self.grab_input_using_trait('timestamp')

        if not timestamp.has_valid_frame():
            raise RuntimeError("Frame timestamps must contain frame IDs")

        frame_id = timestamp.get_frame()

        if self.has_input_port_edge_using_trait('detected_object_set'):
            detections = self.grab_input_using_trait('detected_object_set')
        else:
            detections = DetectedObjectSet()
        if self.has_input_port_edge_using_trait('initializations'):
            initializations = self.grab_input_using_trait('initializations')
        else:
            initializations = ObjectTrackSet()
        if self.has_input_port_edge_using_trait('recommendations'):
            recommendations = self.grab_input_using_trait('recommendations')
        else:
            recommendations = ObjectTrackSet()
        if self.has_input_port_edge_using_trait('evaluation_requests'):
            requests = self.grab_input_using_trait('evaluation_requests')
        else:
            requests = DetectedObjectSet()

        print('mdnet tracker timestamp = {!r}'.format(timestamp))

        # Handle new track external initialization
        init_track_pool = initializations.tracks()
        recc_track_pool = recommendations.tracks()
        init_track_ids = []
        img_used = False

        if len(init_track_pool) != 0 or len(self._trackers) != 0:
            img_npy = self.format_image(in_img_c)
            img_used = True

        for trk in init_track_pool:
            # Special case, initialize a track on a previous frame
            if trk[trk.last_frame].frame_id == self._last_frame_id and \
              ( not trk.id in self._track_init_frames or \
              self._track_init_frames[ trk.id ] < self._last_frame_id ):
                tid = trk.id
                cbox = trk[trk.last_frame].detection().bounding_box()
                bbox = [cbox.min_x(), cbox.min_y(), cbox.width(), cbox.height()]
                self._last_frame = self.format_image(self._last_frame)
                self._trackers[tid] = mdnet.MDNetTracker(self._last_frame, bbox)
                self._tracks[tid] = [ObjectTrackState(timestamp, cbox, 1.0)]
                self._track_init_frames[tid] = self._last_frame_id
            # This track has an initialization signal for the current frame
            elif trk[trk.last_frame].frame_id == frame_id:
                tid = trk.id
                cbox = trk[trk.last_frame].detection().bounding_box()
                bbox = [cbox.min_x(), cbox.min_y(), cbox.width(), cbox.height()]
                self._trackers[tid] = mdnet.MDNetTracker(img_npy, bbox)
                self._tracks[tid] = [ObjectTrackState(timestamp, cbox, 1.0)]
                init_track_ids.append(tid)
                self._track_init_frames[tid] = frame_id

        # Update existing tracks
        for tid in self._trackers.keys():
            if tid in init_track_ids:
                continue # Already processed (initialized) on frame
            # Check if there's a recommendation for the update
            recc_bbox = []
            for trk in recc_track_pool:
                if trk.id == tid and trk[trk.last_frame].frame_id == frame_id:
                    cbox = trk[trk.last_frame].detection().bounding_box()
                    recc_bbox = [cbox.min_x(), cbox.min_y(), cbox.width(), cbox.height()]
                    break
            bbox, score = self._trackers[tid].update(img_npy, likely_bbox=recc_bbox)
            if score > mdnet.opts['success_thr']:
                cbox = BoundingBoxD(
                  bbox[0], bbox[1], bbox[0]+bbox[2], bbox[1]+bbox[3])
                new_state = ObjectTrackState(timestamp, cbox, score)
                self._tracks[tid].append(new_state)

        # Handle track termination
        # TODO: Remove old or dead tracks

        # Classify requested evaluations
        # TODO: Evaluate input detections
        output_evaluations = DetectedObjectSet()

        # Output results
        output_tracks = ObjectTrackSet(
          [Track(tid, trk) for tid, trk in self._tracks.items()])

        self.push_to_port_using_trait('timestamp', timestamp)
        self.push_to_port_using_trait('object_track_set', output_tracks)
        self.push_to_port_using_trait('evaluations', output_evaluations)

        self._last_frame_id = timestamp.get_frame()
        if img_used:
            self._last_frame = img_npy
        else:
            self._last_frame = in_img_c
        self._base_step()

# ==============================================================================
def __sprokit_register__():
    from kwiver.sprokit.pipeline import process_factory

    module_name = 'python:viame.pytorch.MDNetTrackerProcess'

    if process_factory.is_process_module_loaded(module_name):
        return

    process_factory.add_process('mdnet_tracker',
      'Object tracking using mdnet', MDNetTrackerProcess)

    process_factory.mark_process_module_as_loaded(module_name)
