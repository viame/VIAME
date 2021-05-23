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

import numpy as np  # NOQA
import ubelt as ub


class NetharnClassifier(ImageObjectDetector):
    """
    Full-Frame Classifier

    Note: there is no kwiver base class for classifiers, so we abuse the
    detector interface.

    CommandLine:
        xdoctest -m ~/code/VIAME/plugins/pytorch/netharn_classifier.py NetharnClassifier --show

    Example:
        >>> self = NetharnClassifier()
        >>> image_data = self.demo_image()
        >>> deployed_fpath = self.demo_deployed()
        >>> cfg_in = dict(
        >>>     deployed=deployed_fpath,
        >>>     xpu='0',
        >>> )
        >>> self.set_configuration(cfg_in)
        >>> detected_objects = self.classify(image_data)
        >>> object_type = detected_objects[0].type()
        >>> class_names = object_type.all_class_names()
        >>> cname_to_prob = {cname: object_type.score(cname) for cname in class_names}
        >>> print('cname_to_prob = {}'.format(ub.repr2(cname_to_prob, nl=1, precision=4)))
    """

    def __init__(self):
        ImageObjectDetector.__init__(self)

        # kwiver configuration variables
        self._kwiver_config = {
            'deployed': "",
            'xpu': "0",
            'batch_size': "auto"
        }

        # netharn variables
        self._thresh = None
        self.predictor = None

    def demo_deployed(self):
        """
        Returns a path to a netharn deployed model

        Returns:
            str: file path to a scallop classifier
        """
        from bioharn import clf_fit
        harn = clf_fit.setup_harn(cmdline=False, dataset='special:shapes128',
                                  max_epoch=1, timeout=60)
        harn.initialize()
        if not harn.prev_snapshots():
            # generate a model if needed
            deployed_fpath = harn.run()
        else:
            deployed_fpath = harn.prev_snapshots()[-1]
        # TODO: point to a pretrained model on data.kitware
        # import ubelt as ub
        # url = 'https://data.kitware.com/api/v1/file/<some-itemid>/download'
        # deployed_fpath = ub.grabdata(
        #     url, fname='some-filename.zip',
        #     appname='viame', hash_prefix='some-hash',
        #     hasher='sha512')
        return deployed_fpath

    def demo_image(self):
        """
        Returns an image which can be run through the classifier

        Returns:
            ImageContainer: an image of a scallop
        """
        from PIL import Image as PILImage
        from kwiver.vital.util import VitalPIL
        from kwiver.vital.types import ImageContainer
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
        import torch
        from bioharn import clf_predict
        cfg = self.get_configuration()

        # HACK: merge config doesn't support dictionary input
        _vital_config_update(cfg, cfg_in)

        for key in self._kwiver_config.keys():
            self._kwiver_config[key] = str(cfg.get_value(key))

        if self._kwiver_config['batch_size'] == "auto":
            self._kwiver_config['batch_size'] = 2
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

        pred_config = clf_predict.ClfPredictConfig()
        pred_config['batch_size'] = self._kwiver_config['batch_size']
        pred_config['deployed'] = self._kwiver_config['deployed']
        pred_config['xpu'] = self._kwiver_config['xpu']
        pred_config['input_dims'] = 'native'
        # (256, 256)
        self.predictor = clf_predict.ClfPredictor(pred_config)

        self.predictor._ensure_model()
        return True

    def check_configuration(self, cfg):
        if not cfg.has_value("deployed"):
            print("A network deploy file must be specified!")
            return False
        return True

    def detect(self, image_data):
        full_rgb = image_data.asarray().astype('uint8')
        path_or_image = full_rgb
        predictor = self.predictor

        classification = list(predictor.predict([path_or_image]))[0]
        # Hack: use the image size to coerce a classification as a detection
        h, w = full_rgb.shape[0:2]
        output = _classification_to_kwiver_detections(classification, w, h)
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


def _classification_to_kwiver_detections(classification, w, h):
    """
    Convert kwarray classifications to kwiver deteted object sets

    Args:
        classification (bioharn.clf_predict.Classification)
        w (int): width of image
        h (int): height of image

    Returns:
        kwiver.vital.types.DetectedObjectSet
    """
    detected_objects = DetectedObjectSet()

    if classification.data.get('prob', None) is not None:
        # If we have a probability for each class, uses that
        class_names = list(classification.classes)
        class_prob = classification.prob
        detected_object_type = DetectedObjectType(class_names, class_prob)
    else:
        # Otherwise we only have the score for the predicted calss
        class_name = classification.classes[classification.cidx]
        class_score = classification.conf
        detected_object_type = DetectedObjectType(class_name, class_score)

    bounding_box = BoundingBoxD(0, 0, w, h)
    detected_object = DetectedObject(
        bounding_box, classification.conf, detected_object_type)
    detected_objects.add(detected_object)
    return detected_objects


def __vital_algorithm_register__():
    """
    Note:

        We may be able to refactor somethign like this

        # In vital.py

        def _register_algorithm(cls, name=None, desc=''):
            if name is None:
                name = cls.__name__
            from kwiver.vital.algo import algorithm_factory
            if not algorithm_factory.has_algorithm_impl_name(cls.static_type_name(), name):
                algorithm_factory.add_algorithm(name, desc, cls)
                algorithm_factory.mark_algorithm_as_loaded(name)

        def register_algorithm(name=None, desc=''):
            '''
            POC refactor of __vital_algorithm_register__ into a decorator
            '''
            def _wrapper(cls):
                _register_algorithm(cls, name, desc)
                return cls
            return _wrapper

        def lazy_register(cls, name=None, desc=''):
            ''' Alternate Proof-of-Concept '''
            def __vital_algorithm_register__():
                return _register_algorithm(cls, name, desc)
            return __vital_algorithm_register__

        # Then in your class
        import vital
        @vial.register_algorithm(desc="PyTorch Netharn classification routine")
        class MyAlgorithm(BaseAlgo):
            ...

        # OR if the currenty lazy structure is important
        import vital
        class MyAlgorithm(BaseAlgo):
            ...

        __vital_algorithm_register__ = vital.lazy_register(MyAlgorithm, desc="PyTorch Netharn classification routine")

        # We could also play with adding class member variables for the lazy
        # initialization. There is lots of room to make this better / easier.
    """
    from kwiver.vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "netharn_classifier"

    if not algorithm_factory.has_algorithm_impl_name(
            NetharnClassifier.static_type_name(), implementation_name):
        algorithm_factory.add_algorithm(
            implementation_name, "PyTorch Netharn classification routine",
            NetharnClassifier)

        algorithm_factory.mark_algorithm_as_loaded(implementation_name)
