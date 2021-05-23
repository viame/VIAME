# -*- coding: utf-8 -*-
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
"""
Ignore:
    workon_py2
    source ~/code/VIAME/build/install/setup_viame.sh
    cd ~/code/VIAME/plugins/camtrawl

    feat1 = vital.types.Feature(loc=(10, 1))
    feat2 = vital.types.Feature(loc=(2, 3))

    np.sum((feat1.location - feat2.location) ** 2)

CommandLine:
    # OPENCV 3.X VERSION
    cd ~/code/VIAME/plugins/camtrawl/python
    export PYTHONPATH=$(pwd):$PYTHONPATH

    workon_py2
    cd ~/code/VIAME/build-cv3-py2

    export KWIVER_PLUGIN_PATH=""
    export SPROKIT_MODULE_PATH=""
    source install/setup_viame.sh

    export KWIVER_DEFAULT_LOG_LEVEL=debug
    export KWIVER_DEFAULT_LOG_LEVEL=info
    export KWIVER_PYTHON_DEFAULT_LOG_LEVEL=info
    export SPROKIT_PYTHON_MODULES=kwiver.processes:viame.processes

    python ~/code/VIAME/plugins/camtrawl/python/run_camtrawl.py
    python run_camtrawl.py

    ~/code/VIAME/build/install/bin/kwiver runner ~/.cache/sprokit/temp_pipelines/temp_pipeline_file.pipe
    ~/code/VIAME/build/install/bin/kwiver runner camtrawl.pipe -S pythread_per_process

CommandLine:
    # OPENCV 2.4 VERSION
    cd ~/code/VIAME/plugins/camtrawl/python
    export PYTHONPATH=$(pwd):$PYTHONPATH

    workon_py2
    cd ~/code/VIAME/build

    export KWIVER_PLUGIN_PATH=""
    export SPROKIT_MODULE_PATH=""
    source ~/code/VIAME/build/install/setup_viame.sh
    export KWIVER_DEFAULT_LOG_LEVEL=debug
    export KWIVER_DEFAULT_LOG_LEVEL=info
    export KWIVER_PYTHON_DEFAULT_LOG_LEVEL=info
    export SPROKIT_PYTHON_MODULES=kwiver.processes:viame.processes

    # export KWIVER_PYTHON_COLOREDLOGS=1

    python ~/code/VIAME/plugins/camtrawl/python/run_camtrawl.py
    python run_camtrawl.py

    ~/code/VIAME/build/install/bin/kwiver runner ~/.cache/sprokit/temp_pipelines/temp_pipeline_file.pipe  -S pythread_per_process
    ~/code/VIAME/build/install/bin/kwiver runner camtrawl.pipe -S pythread_per_process

SeeAlso
    ~/code/VIAME/packages/kwiver/vital/bindings/python/vital/types
"""
from __future__ import absolute_import, print_function, division

import numpy as np
import vital.types

from kwiver.sprokit.processes.kwiver_process import KwiverProcess
from kwiver.sprokit.pipeline import process
from kwiver.sprokit.pipeline import datum  # NOQA

import ubelt as ub
import os
import itertools as it

from . import algos as ctalgo

from sprokit import sprokit_logging
# import logging
logger = sprokit_logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
print = logger.info


# TODO: add something similar in sprokit proper
TMP_SPROKIT_PROCESS_REGISTRY = []


def tmp_sprokit_register_process(name=None, doc=''):
    def _wrp(cls):
        name_ = name
        if name is None:
            name_ = cls.__name__
        TMP_SPROKIT_PROCESS_REGISTRY.append((name_, doc, cls))
        return cls
    return _wrp


def camtrawl_setup_config(self, default_params):
    if isinstance(default_params, dict):
        default_params = list(it.chain(*default_params.values()))
    for pi in default_params:
        self.add_config_trait(pi.name, pi.name, str(pi.default), pi.doc)
        self.declare_config_using_trait(pi.name)


def tmp_smart_cast_config(self):
    # import ubelt as ub
    # import utool as ut
    config = {}
    keys = [k for k in list(self.available_config())
            if not k.startswith('_')]
    for key in keys:
        strval = self.config_value(key)
        # print('strval = {!r}'.format(strval))
        try:
            val = eval(strval, {}, {})
        except Exception:
            val = strval
        config[key] = val
    return config


@tmp_sprokit_register_process(name='camtrawl_detect_fish',
                              doc='preliminatry fish detection')
class CamtrawlDetectFishProcess(KwiverProcess):
    """
    This process gets an image and detection_set as input, extracts each chip,
    does postprocessing and then sends the extracted chip to the output port.

    """
    # ----------------------------------------------
    def __init__(self, conf):
        print('conf = {!r}'.format(conf))
        logger.debug(' ----- init ' + self.__class__.__name__)
        KwiverProcess.__init__(self, conf)

        camtrawl_setup_config(self, ctalgo.GMMForegroundObjectDetector.default_params())

        # set up required flags
        optional = process.PortFlags()
        required = process.PortFlags()
        required.add(self.flag_required)

        #  declare our input port ( port-name,flags)
        self.declare_input_port_using_trait('image', required)

        self.declare_output_port_using_trait('detected_object_set', optional )

    # ----------------------------------------------
    def _configure(self):
        logger.debug(' ----- configure ' + self.__class__.__name__)
        config = tmp_smart_cast_config(self)
        print('detector config = {}'.format(ub.repr2(config, nl=2)))
        self.detector = ctalgo.GMMForegroundObjectDetector(**config)
        self._base_configure()

    # ----------------------------------------------
    def _dowork(self, img_container):
        """
        Helper to decouple the algorithm and pipeline logic

        CommandLine:
            python -m xdoctest viame.processes.camtrawl.processes CamtrawlDetectFishProcess._dowork

        Example:
            >>> from viame.processes.camtrawl.processes import *
            >>> from vital.types import ImageContainer
            >>> import kwiver.sprokit.pipeline.config
            >>> # construct dummy process instance
            >>> conf = kwiver.sprokit.pipeline.config.empty_config()
            >>> self = CamtrawlDetectFishProcess(conf)
            >>> self._configure()
            >>> # construct test data
            >>> from vital.util import VitalPIL
            >>> from PIL import Image as PILImage
            >>> pil_img = PILImage.open(ub.grabdata('https://i.imgur.com/Jno2da3.png'))
            >>> pil_img = PILImage.fromarray(np.zeros((512, 512, 3), dtype=np.uint8))
            >>> img_container = ImageContainer(VitalPIL.from_pil(pil_img))
            >>> # Initialize the background detector by sending 10 black frames
            >>> for i in range(10):
            >>>     empty_set = self._dowork(img_container)
            >>> # now add a white box that should be detected
            >>> np_img = np.zeros((512, 512, 3), dtype=np.uint8)
            >>> np_img[300:340, 220:380] = 255
            >>> img_container = ImageContainer.fromarray(np_img)
            >>> detection_set = self._dowork(img_container)
            >>> assert len(detection_set) == 1
            >>> obj = detection_set[0]
        """
        # This should be read as np.uint8
        np_img = img_container.asarray()

        detection_set = vital.types.DetectedObjectSet()
        ct_detections = self.detector.detect(np_img)

        for detection in ct_detections:
            bbox = vital.types.BoundingBox(*detection.bbox.coords)
            mask = detection.mask.astype(np.uint8)
            vital_mask = vital.types.ImageContainer.fromarray(mask)
            obj = vital.types.DetectedObject(bbox, 1.0, mask=vital_mask)
            detection_set.add(obj)
        return detection_set

    def _step(self):
        logger.debug(' ----- ' + self.__class__.__name__ + ' step')
        # grab image container from port using traits
        img_container = self.grab_input_using_trait('image')

        # Process image container
        detection_set = self._dowork(img_container)

        # Push the output
        self.push_to_port_using_trait('detected_object_set', detection_set)

        self._base_step()


@tmp_sprokit_register_process(name='camtrawl_measure',
                              doc='preliminatry fish length measurement')
class CamtrawlMeasureProcess(KwiverProcess):
    """
    This process gets an image and detection_set as input, extracts each chip,
    does postprocessing and then sends the extracted chip to the output port.
    """
    # ----------------------------------------------
    def __init__(self, conf):
        logger.debug(' ----- ' + self.__class__.__name__ + ' init')

        KwiverProcess.__init__(self, conf)

        camtrawl_setup_config(self, ctalgo.FishStereoMeasurments.default_params())

        self.add_config_trait('output_fpath', 'output_fpath', 'camtrawl_out.csv',
                              'output file to write detection measurements')
        self.declare_config_using_trait('output_fpath')
        self.add_config_trait('cal_fpath', 'cal_fpath', 'cal_201608.mat',
                              'matlab or npz file with calibration info')
        self.declare_config_using_trait('cal_fpath')

        # optional = process.PortFlags()
        required = process.PortFlags()
        required.add(self.flag_required)

        # self.add_port_trait('camera' + '1', 'camera', 'Left camera calibration')
        # self.add_port_trait('camera' + '2', 'camera', 'Right camera calibration')
        self.add_port_trait('detected_object_set' + '1', 'detected_object_set', 'Detections from camera1')
        self.add_port_trait('detected_object_set' + '2', 'detected_object_set', 'Detections from camera2')
        self.add_port_trait('image_file_name' + '1', 'file_name', 'desc1')
        self.add_port_trait('image_file_name' + '2', 'file_name', 'desc2')
        # self.add_port_trait('frame_id1', 'int', 'frame id')
        # self.add_port_trait('frame_id2', 'int', 'frame id')

        #  declare our input port ( port-name,flags)
        # self.declare_input_port_using_trait('camera' + '1', optional)
        # self.declare_input_port_using_trait('camera' + '2', optional)
        self.declare_input_port_using_trait('image_file_name' + '1', required)
        self.declare_input_port_using_trait('image_file_name' + '2', required)
        self.declare_input_port_using_trait('detected_object_set' + '1', required)
        self.declare_input_port_using_trait('detected_object_set' + '2', required)

    # ----------------------------------------------
    def _configure(self):
        logger.debug(' ----- ' + self.__class__.__name__ + ' configure')
        config = tmp_smart_cast_config(self)

        logger.info('triangulator config = {}'.format(ub.repr2(config, nl=2)))
        output_fpath = config.pop('output_fpath')
        cal_fpath = config.pop('cal_fpath')
        self.triangulator = ctalgo.FishStereoMeasurments(**config)

        # Camera loading process is not working correctly.
        # Load camera calibration data here for now.
        #
        if not os.path.exists(cal_fpath):
            raise KeyError('must specify a valid camera calibration path')
        self.cal = ctalgo.StereoCalibration.from_file(cal_fpath)
        logger.info('self.cal = {!r}'.format(self.cal))

        self.headers = ['current_frame', 'fishlen', 'range', 'error', 'dz',
                        'box_pts1', 'box_pts2']
        self.output_file = open(output_fpath, 'w')
        self.output_file.write(','.join(self.headers) + '\n')
        self.output_file.close()

        self.output_file = open(output_fpath, 'a')
        self._base_configure()

        self.prog = ub.ProgIter(verbose=3)
        self.prog.begin()

    # ----------------------------------------------
    def _step(self):
        logger.debug(' ----- ' + self.__class__.__name__ + ' step')
        self.prog.step()

        if self.cal is None:
            self.cal = True
            logger.debug(' ----- ' + self.__class__.__name__ + ' grab cam1')
            # grab camera only if we dont have one yet
            camera1 = self.grab_input_using_trait('camera' + '1')
            logger.debug(' ----- ' + self.__class__.__name__ + ' grab cam2')
            camera2 = self.grab_input_using_trait('camera' + '2')

            def _cal_from_vital(vital_camera):
                vital_intrinsics = vital_camera.intrinsics
                cam_dict = {
                    'extrinsic': {
                        'om': vital_camera.rotation.rodrigues().ravel(),
                        'T': vital_camera.translation.ravel(),
                    },
                    'intrinsic': {
                        'cc': vital_intrinsics.principle_point.ravel(),
                        'fc': [vital_intrinsics.focal_length, vital_intrinsics.focal_length / vital_intrinsics.aspect_ratio],
                        'alpha_c': vital_intrinsics.skew,
                        'kc': vital_intrinsics.dist_coeffs.ravel(),
                    }
                }
                return cam_dict

            logger.debug(' ----- ' + self.__class__.__name__ + ' parse cameras')
            self.cal = ctalgo.StereoCalibration({
                'left': _cal_from_vital(camera1),
                'right': _cal_from_vital(camera2),
            })
            logger.debug(' ----- ' + self.__class__.__name__ + ' no more need for cameras')

        image_file_name1 = self.grab_input_using_trait('image_file_name1')  # .get_datum()
        image_file_name2 = self.grab_input_using_trait('image_file_name2')  # .get_datum()

        def _parse_frameid(fname):
            return int(os.path.basename(fname).split('_')[0])

        frame_id1 = _parse_frameid(image_file_name1)
        frame_id2 = _parse_frameid(image_file_name2)
        assert frame_id1 == frame_id2
        frame_id = frame_id1

        # frame_id1 = self.grab_input_using_trait('frame_id' + '1')
        # frame_id2 = self.grab_input_using_trait('frame_id' + '2')
        detection_set1 = self.grab_input_using_trait('detected_object_set' + '1')
        detection_set2 = self.grab_input_using_trait('detected_object_set' + '2')

        # Convert back to the format the algorithm understands
        def _detections_from_vital(detection_set):
            for vital_det in detection_set:
                bbox = vital_det.bounding_box()
                coords = [bbox.min_x(), bbox.min_y(),
                          bbox.max_x(), bbox.max_y()]
                mask = vital_det.mask.asarray()
                ct_bbox = ctalgo.BoundingBox(coords)
                ct_det = ctalgo.DetectedObject(ct_bbox, mask)
                yield ct_det
        detections1 = list(_detections_from_vital(detection_set1))
        detections2 = list(_detections_from_vital(detection_set2))

        assignment, assign_data, cand_errors = self.triangulator.find_matches(
            self.cal, detections1, detections2)

        logger.debug(' ----- ' + self.__class__.__name__ + ' found {} matches'.format(len(assign_data)))

        def csv_repr(d):
            if isinstance(d, np.ndarray):
                d = d.tolist()
            s = repr(d)
            return s.replace('\n', '').replace(',', ';').replace(' ', '')

        # Append assignments to the measurements
        for data in assign_data:
            data['current_frame'] = frame_id
            line = ','.join([csv_repr(d) for d in ub.take(data, self.headers)])
            self.output_file.write(line + '\n')

        if assign_data:
            self.output_file.flush()

        # push dummy image object (same as input) to output port
        # self.push_to_port_using_trait('out_image', vital.types.ImageContainer(in_img))
        self._base_step()


def __sprokit_register__():

    from kwiver.sprokit.pipeline import process_factory

    module_name = 'python_' + __name__

    # module_name = 'python:camtrawl.processes'
    # module_name = 'python' + __name__
    if process_factory.is_process_module_loaded(module_name):
        return

    # print('TMP_SPROKIT_PROCESS_REGISTRY = {}'.format(ub.repr2(TMP_SPROKIT_PROCESS_REGISTRY)))

    for name, doc, cls in TMP_SPROKIT_PROCESS_REGISTRY:
        # print("REGISTER PROCESS:")
        # print(' * name = {!r}'.format(name))
        # print(' * cls = {!r}'.format(cls))
        process_factory.add_process(name, doc, cls)

    # process_factory.add_process('camtrawl_detect_fish',
    #                             'preliminatry detection / feature extraction',
    #                             CamtrawlDetectFishProcess)

    # process_factory.add_process('camtrawl_measure',
    #                             'preliminatry measurement',
    #                             CamtrawlMeasureProcess)

    process_factory.mark_process_module_as_loaded(module_name)
