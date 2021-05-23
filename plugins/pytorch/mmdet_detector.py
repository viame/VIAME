# ckwg +29
# Copyright 2019 by Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#  this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
#  * Neither name of Kitware, Inc. nor the names of any contributors may be used
#  to endorse or promote products derived from this software without specific
#  prior written permission.
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

from kwiver.vital.algo import ImageObjectDetector

from kwiver.vital.types import (
    BoundingBoxD, DetectedObject, DetectedObjectSet, DetectedObjectType
)

from distutils.util import strtobool

import numpy as np
import sys

import mmcv


class MMDetDetector( ImageObjectDetector ):
    """
    Implementation of ImageObjectDetector class
    """
    def __init__( self ):
        ImageObjectDetector.__init__(self)
        self._net_config = ""
        self._weight_file = ""
        self._class_names = ""
        self._thresh = 0.01
        self._gpu_index = "0"
        self._display_detections = False
        self._template = ""

    def get_configuration(self):
        # Inherit from the base class
        cfg = super(ImageObjectDetector, self).get_configuration()
        cfg.set_value( "net_config", self._net_config )
        cfg.set_value( "weight_file", self._weight_file )
        cfg.set_value( "class_names", self._class_names )
        cfg.set_value( "thresh", str( self._thresh ) )
        cfg.set_value( "gpu_index", self._gpu_index )
        cfg.set_value( "display_detections", str( self._display_detections ) )
        cfg.set_value( "template", str( self._template ) )
        return cfg

    def set_configuration( self, cfg_in ):
        cfg = self.get_configuration()
        cfg.merge_config( cfg_in )

        self._net_config = str( cfg.get_value( "net_config" ) )
        self._weight_file = str( cfg.get_value( "weight_file" ) )
        self._class_names = str( cfg.get_value( "class_names" ) )
        self._thresh = float( cfg.get_value( "thresh" ) )
        self._gpu_index = str( cfg.get_value( "gpu_index" ) )
        self._display_detections = strtobool( cfg.get_value( "display_detections" ) )
        self._template = str( cfg.get_value( "template" ) )

        from viame.arrows.pytorch.mmdet_compatibility import check_config_compatibility
        check_config_compatibility( self._net_config, self._weight_file, self._template )

        import matplotlib
        matplotlib.use( 'PS' ) # bypass multiple Qt load issues
        from mmdet.apis import init_detector

        gpu_string = 'cuda:' + str( self._gpu_index )
        self._model = init_detector( self._net_config, self._weight_file, device=gpu_string )
        with open( self._class_names, "r" ) as in_file:
            self._labels = in_file.read().splitlines()

    def check_configuration( self, cfg ):
        if not cfg.has_value( "net_config" ):
            print( "A network config file must be specified!" )
            return False
        if not cfg.has_value( "class_names" ):
            print( "A class file must be specified!" )
            return False
        if not cfg.has_value( "weight_file" ):
            print( "No weight file specified" )
            return False
        return True

    def detect( self, image_data ):
        input_image = image_data.asarray().astype( 'uint8' )

        from mmdet.apis import inference_detector
        detections = inference_detector( self._model, input_image )

        if isinstance( detections, tuple ):
            bbox_result, segm_result = detections
        else:
            bbox_result, segm_result = detections, None

        if np.size( bbox_result ) > 0:
            bboxes = np.vstack( bbox_result )
        else:
            bboxes = []

        # convert segmentation masks
        masks = []
        if segm_result is not None:
            segms = mmcv.concat_list( segm_result )
            inds = np.where( bboxes[:, -1] > score_thr )[0]
            for i in inds:
                masks.append( maskUtils.decode( segms[i] ).astype( np.bool ) )

        # collect labels
        labels = [
            np.full( bbox.shape[0], i, dtype=np.int32 )
            for i, bbox in enumerate( bbox_result )
        ]

        if np.size( labels ) > 0:
            labels = np.concatenate( labels )
        else:
            labels = []

        # convert to kwiver format, apply threshold
        output = DetectedObjectSet()

        for bbox, label in zip( bboxes, labels ):
            class_confidence = float( bbox[-1] )
            if class_confidence < self._thresh:
                continue

            bbox_int = bbox.astype( np.int32 )
            bounding_box = BoundingBoxD( bbox_int[0], bbox_int[1],
                                         bbox_int[2], bbox_int[3] )

            class_name = self._labels[ label ]
            detected_object_type = DetectedObjectType( class_name, class_confidence )

            detected_object = DetectedObject( bounding_box,
                                              np.max( class_confidence ),
                                              detected_object_type )
            output.add( detected_object )

        if np.size( labels ) > 0 and self._display_detections:
            mmcv.imshow_det_bboxes(
                input_image,
                bboxes,
                labels,
                class_names=self._labels,
                score_thr=self._thresh,
                show=True )

        return output

def __vital_algorithm_register__():
    from kwiver.vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "mmdet"

    if algorithm_factory.has_algorithm_impl_name(
      MMDetDetector.static_type_name(), implementation_name ):
        return

    algorithm_factory.add_algorithm( implementation_name,
      "PyTorch MMDetection inference routine", MMDetDetector )

    algorithm_factory.mark_algorithm_as_loaded( implementation_name )
