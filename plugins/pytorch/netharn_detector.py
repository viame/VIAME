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

"""
Notes:
    pip install ~/remote/videonas/fouo/projects/diva/kwiver-wheels/kwiver-1.4.0-cp37-cp37m-linux_x86_64.whl
    pip install ~/remote/videonas/fouo/projects/diva/kwiver-wheels/external_arrow-0.0.1-cp37-cp37m-linux_x86_64.whl


    pip install ~/remote/videonas/fouo/projects/diva/kwiver-wheels/kwiver-1.4.0-cp35-cp35m-linux_x86_64.whl

    pip install netharn kwimage kwarray ndsampler


    git submodule add -b release git@gitlab.kitware.com:computer-vision/kwimage.git packages/kwimage
"""

from kwiver.vital.algo import ImageObjectDetector

from kwiver.vital.types import BoundingBoxD
from kwiver.vital.types import DetectedObjectSet
from kwiver.vital.types import DetectedObject
from kwiver.vital.types import DetectedObjectType

import numpy as np


class NetharnDetector(ImageObjectDetector):
    """
    Implementation of ImageObjectDetector class

    CommandLine:
        xdoctest -m ~/code/VIAME/plugins/pytorch/netharn_detector.py NetharnDetector --show

    Example:
        >>> self = NetharnDetector()
        >>> image_data = self.demo_image()
        >>> deployed_fpath = self.demo_deployed()
        >>> cfg_in = dict(
        >>>     deployed=deployed_fpath,
        >>>     xpu='0',
        >>> )
        >>> self.set_configuration(cfg_in)
        >>> detected_objects = self.detect(image_data)
        >>> # xdoctest: +REQUIRES(--show)
        >>> import kwplot
        >>> kwplot.autompl()
        >>> full_rgb = image_data.asarray().astype('uint8')
        >>> dets = _kwiver_to_kwimage_detections(detected_objects)
        >>> canvas = dets.draw_on(full_rgb)
        >>> kwplot.imshow(canvas)
        >>> kwplot.show_if_requested()
    """

    def __init__(self):
        ImageObjectDetector.__init__(self)

        # kwiver configuration variables
        self._kwiver_config = {
            'deployed': "",
            'thresh': 0.01,
            'xpu': "0",
            'batch_size': "auto",
            'input_string': ""
        }

        # netharn variables
        self._thresh = None
        self.predictor = None

    def demo_deployed(self):
        """
        Returns a path to a netharn deployed model

        Returns:
            str: file path to a scallop detector
        """
        import ubelt as ub
        url = 'https://data.kitware.com/api/v1/file/5dd3eb8eaf2e2eed3508d604/download'
        deployed_fpath = ub.grabdata(
            url, fname='deploy_MM_CascadeRCNN_myovdqvi_035_MVKVVR_fix3.zip',
            appname='viame', hash_prefix='22a1eeb18c9e5706f6578e66abda1e97',
            hasher='sha512')
        return deployed_fpath

    def demo_image(self):
        """
        Returns an image which can be run through the detector

        Returns:
            ImageContainer: an image of a scallop
        """
        from PIL import Image as PILImage
        from kwiver.vital.util import VitalPIL
        from kwiver.vital.types import ImageContainer
        import ubelt as ub
        url = 'https://data.kitware.com/api/v1/file/5dcf0d1faf2e2eed35fad5d1/download'
        image_fpath = ub.grabdata(
            url, fname='scallop.jpg', appname='viame',
            hash_prefix='3bd290526c76453bec7', hasher='sha512')
        pil_img = PILImage.open(image_fpath)
        image_data = ImageContainer(VitalPIL.from_pil(pil_img))
        return image_data

    def get_configuration(self):
        # Inherit from the base class
        cfg = super(ImageObjectDetector, self).get_configuration()
        for key, value in self._kwiver_config.items():
            cfg.set_value(key, str(value))
        return cfg

    def set_configuration(self, cfg_in):
        cfg = self.get_configuration()

        # HACK: merge config doesn't support dictionary input
        _vital_config_update(cfg, cfg_in)

        for key in self._kwiver_config.keys():
            self._kwiver_config[key] = str(cfg.get_value(key))
        self._kwiver_config['thresh'] = float(self._kwiver_config['thresh'])

        self._thresh = float(self._kwiver_config['thresh'])

        if self._kwiver_config['batch_size'] == "auto":
            self._kwiver_config['batch_size'] = 2
            import torch
            if torch.cuda.is_available():
                gpu_mem = 0
                if len(self._kwiver_config['xpu']) == 1 and \
                  self._kwiver_config['xpu'] != 0:
                    gpu_id = int(self._kwiver_config['xpu'])
                    gpu_mem = torch.cuda.get_device_properties(gpu_id).total_memory
                else:
                    self._gpu_count = torch.cuda.device_count()
                    for i in range( self._gpu_count ):
                        single_gpu_mem = torch.cuda.get_device_properties(i).total_memory
                    if gpu_mem == 0:
                        gpu_mem = single_gpu_mem
                    else:
                        gpu_mem = min(gpu_mem, single_gpu_mem)
                if gpu_mem > 9e9:
                    self._kwiver_config['batch_size'] = 4
                elif gpu_mem >= 7e9:
                    self._kwiver_config['batch_size'] = 3

        import os
        if os.name == 'nt':
            os.environ["KWIMAGE_DISABLE_TORCHVISION_NMS"] = "1"

        from bioharn import detect_predict
        pred_config = detect_predict.DetectPredictConfig()
        pred_config['batch_size'] = self._kwiver_config['batch_size']
        pred_config['deployed'] = self._kwiver_config['deployed']
        pred_config['xpu'] = self._kwiver_config['xpu']
        self.predictor = detect_predict.DetectPredictor(pred_config)

        self.predictor._ensure_model()
        return True

    def check_configuration(self, cfg):
        if not cfg.has_value("deployed"):
            print("A network deploy file must be specified!")
            return False
        return True

    def detect(self, image_data):
        full_rgb = image_data.asarray().astype('uint8')

        if len(self._kwiver_config['input_string']) > 0:
            dict_or_image = {self._kwiver_config['input_string']:full_rgb}
        else:
            dict_or_image = full_rgb

        predictor = self.predictor
        detections = predictor.predict(dict_or_image)

        # apply threshold
        flags = detections.scores >= self._thresh
        detections = detections.compress(flags)

        # convert to kwiver format
        output = _kwimage_to_kwiver_detections(detections)
        return output


def _vital_config_update(cfg, cfg_in):
    """
    Treat a vital Config object like a python dictionary

    Args:
        cfg (kwiver.vital.config.config.Config): config to update
        cfg_in (dict | kwiver.vital.config.config.Config): new values
    """
    # vital cfg.merge_config doesnt support dictionary input
    if isinstance(cfg_in, dict):
        for key, value in cfg_in.items():
            if cfg.has_value(key):
                cfg.set_value(key, str(value))
            else:
                raise KeyError('cfg has no key={}'.format(key))
    else:
        cfg.merge_config(cfg_in)
    return cfg


def _kwiver_to_kwimage_detections(detected_objects):
    """
    Convert vital detected object sets to kwimage.Detections

    Args:
        detected_objects (kwiver.vital.types.DetectedObjectSet)

    Returns:
        kwimage.Detections
    """
    import ubelt as ub
    import kwimage
    boxes = []
    scores = []
    class_idxs = []

    classes = []
    if len(detected_objects) > 0:
        obj = ub.peek(detected_objects)
        classes = obj.type.all_class_names()

    for obj in detected_objects:
        box = obj.bounding_box
        tlbr = [box.min_x(), box.min_y(), box.max_x(), box.max_y()]
        score = obj.confidence
        cname = obj.type.get_most_likely_class()
        cidx = classes.index(cname)
        boxes.append(tlbr)
        scores.append(score)
        class_idxs.append(cidx)

    dets = kwimage.Detections(
        boxes=kwimage.Boxes(np.array(boxes), 'tlbr'),
        scores=np.array(scores),
        class_idxs=np.array(class_idxs),
        classes=classes,
    )
    return dets


def _kwimage_to_kwiver_detections(detections):
    """
    Convert kwimage detections to kwiver deteted object sets

    Args:
        detected_objects (kwimage.Detections)

    Returns:
        kwiver.vital.types.DetectedObjectSet
    """

    # convert segmentation masks
    if 'segmentations' in detections.data:
        print( "Warning: segmentations not implemented" )

    boxes = detections.boxes.to_tlbr()
    scores = detections.scores
    class_idxs = detections.class_idxs

    # convert to kwiver format, apply threshold
    detected_objects = DetectedObjectSet()

    for tlbr, score, cidx in zip(boxes.data, scores, class_idxs):
        class_name = detections.classes[cidx]

        bbox_int = np.round(tlbr).astype(np.int32)
        bounding_box = BoundingBoxD(
            bbox_int[0], bbox_int[1], bbox_int[2], bbox_int[3])

        detected_object_type = DetectedObjectType(class_name, score)
        detected_object = DetectedObject(
            bounding_box, score, detected_object_type)
        detected_objects.add(detected_object)
    return detected_objects


def __vital_algorithm_register__():
    from kwiver.vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "netharn"

    if algorithm_factory.has_algorithm_impl_name(
            NetharnDetector.static_type_name(), implementation_name):
        return

    algorithm_factory.add_algorithm(
        implementation_name, "PyTorch Netharn detection routine",
        NetharnDetector)

    algorithm_factory.mark_algorithm_as_loaded(implementation_name)
