# ckwg +29
# Copyright 2020 by Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#    * Neither name of Kitware, Inc. nor the names of any contributors may be used
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

from kwiver.vital.algo import (
    DetectedObjectSetOutput,
    ImageObjectDetector,
    TrainDetector
)

from kwiver.vital.types import (
    Image, ImageContainer,
    BoundingBoxD, CategoryHierarchy,
    DetectedObjectSet, DetectedObject, DetectedObjectType
)

from distutils.util import strtobool
from shutil import copyfile

import argparse
import numpy as np
import torch
import pickle
import os
import signal
import sys
import subprocess
import threading
import time
import random

class NetHarnTrainer( TrainDetector ):
    """
    Implementation of TrainDetector class
    """
    def __init__( self ):
        TrainDetector.__init__( self )

        self._identifier = "viame-netharn-detector"
        self._mode = "detector"
        self._arch = ""
        self._seed_model = ""
        self._train_directory = "deep_training"
        self._output_directory = "category_models"
        self._output_prefix = "custom_cfrnn"
        self._pipeline_template = ""
        self._gpu_count = -1
        self._tmp_training_file = "training_truth.json"
        self._tmp_validation_file = "validation_truth.json"
        self._augmentation = "complex"
        self._gt_frames_only = False
        self._chip_width = "640"
        self._chip_overlap = "0.20"
        self._max_epochs = "50"
        self._batch_size = "auto"
        self._learning_rate = "auto"
        self._timeout = "1209600"
        self._backbone = ""
        self._pipeline_template = ""
        self._categories = []
        self._resize_option = "original_and_resized"
        self._max_scale_wrt_chip = 2.0
        self._no_format = False
        self._allow_unicode = "auto"
        self._aux_image_labels = ""
        self._aux_image_extensions = ""
        self._area_lower_bound = 0
        self._area_upper_bound = 0
        self._border_exclude = -1
        self._detector_model = ""
        self._min_overlap_for_association = 0.90
        self._max_overlap_for_negative = 0.05
        self._max_neg_per_frame = 5
        self._negative_category = "BACKGROUND"

    def get_configuration( self ):
        # Inherit from the base class
        cfg = super( TrainDetector, self ).get_configuration()

        cfg.set_value( "identifier", self._identifier )
        cfg.set_value( "mode", self._mode )
        cfg.set_value( "arch", self._arch )
        cfg.set_value( "seed_model", self._seed_model )
        cfg.set_value( "train_directory", self._train_directory )
        cfg.set_value( "output_directory", self._output_directory )
        cfg.set_value( "output_prefix", self._output_prefix )
        cfg.set_value( "pipeline_template", self._pipeline_template )
        cfg.set_value( "gpu_count", str( self._gpu_count ) )
        cfg.set_value( "gt_frames_only", str( self._gt_frames_only ) )
        cfg.set_value( "augmentation", str( self._augmentation ) )
        cfg.set_value( "chip_width", str( self._chip_width ) )
        cfg.set_value( "chip_overlap", str( self._chip_overlap ) )
        cfg.set_value( "max_epochs", str( self._max_epochs ) )
        cfg.set_value( "batch_size", self._batch_size )
        cfg.set_value( "learning_rate", self._learning_rate )
        cfg.set_value( "timeout", self._timeout )
        cfg.set_value( "backbone", self._backbone )
        cfg.set_value( "pipeline_template", self._pipeline_template )
        cfg.set_value( "max_scale_wrt_chip", str( self._max_scale_wrt_chip ) )
        cfg.set_value( "no_format", str( self._no_format ) )
        cfg.set_value( "allow_unicode", str( self._allow_unicode ) )
        cfg.set_value( "aux_image_labels", str( self._aux_image_labels ) )
        cfg.set_value( "aux_image_extensions", str( self._aux_image_extensions ) )
        cfg.set_value( "area_lower_bound", str( self._area_lower_bound ) )
        cfg.set_value( "area_upper_bound", str( self._area_upper_bound ) )
        cfg.set_value( "border_exclude", str( self._border_exclude ) )
        cfg.set_value( "detector_model", str( self._detector_model ) )
        cfg.set_value( "max_neg_per_frame", str( self._max_neg_per_frame ) )
        cfg.set_value( "negative_category", self._negative_category )

        return cfg

    def set_configuration( self, cfg_in ):
        cfg = self.get_configuration()
        cfg.merge_config( cfg_in )

        # Read configs from file
        self._identifier = str( cfg.get_value( "identifier" ) )
        self._mode = str( cfg.get_value( "mode" ) )
        self._arch = str( cfg.get_value( "arch" ) )
        self._seed_model = str( cfg.get_value( "seed_model" ) )
        self._train_directory = str( cfg.get_value( "train_directory" ) )
        self._output_directory = str( cfg.get_value( "output_directory" ) )
        self._output_prefix = str( cfg.get_value( "output_prefix" ) )
        self._pipeline_template = str( cfg.get_value( "pipeline_template" ) )
        self._gpu_count = int( cfg.get_value( "gpu_count" ) )
        self._gt_frames_only = strtobool( cfg.get_value( "gt_frames_only" ) )
        self._augmentation = str( cfg.get_value( "augmentation" ) )
        self._chip_width = str( cfg.get_value( "chip_width" ) )
        self._chip_overlap = str( cfg.get_value( "chip_overlap" ) )
        self._max_epochs = str( cfg.get_value( "max_epochs" ) )
        self._batch_size = str( cfg.get_value( "batch_size" ) )
        self._learning_rate = str( cfg.get_value( "learning_rate" ) )
        self._timeout = str( cfg.get_value( "timeout" ) )
        self._backbone = str( cfg.get_value( "backbone" ) )
        self._pipeline_template = str( cfg.get_value( "pipeline_template" ) )
        self._max_scale_wrt_chip = float( cfg.get_value( "max_scale_wrt_chip" ) )
        self._no_format = strtobool( cfg.get_value( "no_format" ) )
        self._allow_unicode = str( cfg.get_value( "allow_unicode" ) )
        self._aux_image_labels = str( cfg.get_value( "aux_image_labels" ) )
        self._aux_image_extensions = str( cfg.get_value( "aux_image_extensions" ) )
        self._area_lower_bound = float( cfg.get_value( "area_lower_bound" ) )
        self._area_upper_bound = float( cfg.get_value( "area_upper_bound" ) )
        self._border_exclude = float( cfg.get_value( "border_exclude" ) )
        self._detector_model = str( cfg.get_value( "detector_model" ) )
        self._max_neg_per_frame = float( cfg.get_value( "max_neg_per_frame" ) )
        self._negative_category = str( cfg.get_value( "negative_category" ) )

        # Check GPU-related variables
        gpu_memory_available = 0
        gpu_param_adj = 1

        if torch.cuda.is_available():
            if self._gpu_count < 0:
                self._gpu_count = torch.cuda.device_count()
                gpu_param_adj = self._gpu_count
            for i in range( self._gpu_count ):
                single_gpu_mem = torch.cuda.get_device_properties( i ).total_memory
                if gpu_memory_available == 0:
                    gpu_memory_available = single_gpu_mem
                else:
                    gpu_memory_available = min( gpu_memory_available, single_gpu_mem )

        if self._mode == "detector":
            if self._batch_size == "auto":
                if len( self._aux_image_labels ) > 0:
                    if gpu_memory_available >= 22e9:
                        self._batch_size = str( 2 * gpu_param_adj )
                    else:
                        self._batch_size = str( 1 * gpu_param_adj )
                elif gpu_memory_available > 9.5e9:
                    self._batch_size = str( 4 * gpu_param_adj )
                elif gpu_memory_available >= 7.5e9:
                    self._batch_size = str( 3 * gpu_param_adj )
                elif gpu_memory_available >= 4.5e9:
                    self._batch_size = str( 2 * gpu_param_adj )
                else:
                    self._batch_size = str( 1 * gpu_param_adj )
            if self._learning_rate == "auto":
                self._learning_rate = str( 1e-3 )
        elif self._mode == "frame_classifier" or self._mode == "detection_refiner":
            if self._batch_size == "auto":
                if gpu_memory_available > 9.5e9:
                    self._batch_size = str( 64 * gpu_param_adj )
                elif gpu_memory_available >= 7.5e9:
                    self._batch_size = str( 32 * gpu_param_adj )
                elif gpu_memory_available >= 4.5e9:
                    self._batch_size = str( 16 * gpu_param_adj )
                else:
                    self._batch_size = str( 8 * gpu_param_adj )
            if self._learning_rate == "auto":
                self._learning_rate = str( 5e-3 )
        else:
            print( "Invalid mode string " + self._mode )
            return False

        # Make required directories and file streams
        if self._train_directory is not None:
            if not os.path.exists( self._train_directory ):
                os.mkdir( self._train_directory )
            self._training_file = os.path.join(
                self._train_directory, self._tmp_training_file )
            self._validation_file = os.path.join(
                self._train_directory, self._tmp_validation_file )
            self._chip_directory = os.path.join(
                self._train_directory, "image_chips" )
        else:
            self._training_file = self._tmp_training_file
            self._validation_file = self._tmp_validation_file

        if self._output_directory is not None:
            if not os.path.exists( self._output_directory ):
                os.mkdir( self._output_directory )

        from kwiver.vital.modules import load_known_modules
        load_known_modules()

        if not self._no_format:
            self._training_writer = \
              DetectedObjectSetOutput.create( "coco" )
            self._validation_writer = \
              DetectedObjectSetOutput.create( "coco" )

            writer_conf = self._training_writer.get_configuration()
            writer_conf.set_value( "aux_image_labels", self._aux_image_labels )
            writer_conf.set_value( "aux_image_extensions", self._aux_image_extensions )
            self._training_writer.set_configuration( writer_conf )

            writer_conf = self._validation_writer.get_configuration()
            writer_conf.set_value( "aux_image_labels", self._aux_image_labels )
            writer_conf.set_value( "aux_image_extensions", self._aux_image_extensions )
            self._validation_writer.set_configuration( writer_conf )

            self._training_writer.open( self._training_file )
            self._validation_writer.open( self._validation_file )

        # Set default architecture if unset
        if not self._arch:
            if self._mode == "frame_classifier" or self._mode == "detection_refiner":
                self._arch = "resnet50"
            else:
                self._arch = "cascade"

        if self._mode == "detection_refiner" and not os.path.exists( self._chip_directory ):
            os.mkdir( self._chip_directory )

        # Load object detector if enabled
        if self._detector_model:
            self._detector = ImageObjectDetector.create( "netharn" )
            detector_config = self._detector.get_configuration()
            detector_config.set_value( "deployed", self._detector_model )
            if not self._detector.set_configuration( detector_config ):
                print( "Unable to configure detector" )
                return False

        # Initialize persistent variables
        self._training_data = []
        self._validation_data = []
        self._sample_count = 0
        return True

    def check_configuration( self, cfg ):
        if not cfg.has_value( "identifier" ) or \
          len( cfg.get_value( "identifier") ) == 0:
            print( "A model identifier must be specified!" )
            return False
        return True

    def filter_truth( self, init_truth, categories ):
        filtered_truth = DetectedObjectSet()
        use_frame = True
        max_length = int( self._max_scale_wrt_chip * float( self._chip_width ) )
        for i, item in enumerate( init_truth ):
            if item.type is None:
                continue
            class_lbl = item.type.get_most_likely_class()
            if categories is not None and not categories.has_class_name( class_lbl ):
                if self._mode == "detection_refiner":
                    class_lbl = self._negative_category
                else:
                    continue
            if categories is not None:
                class_lbl = categories.get_class_name( class_lbl )
            elif class_lbl not in self._categories:
                self._categories.append( class_lbl )

            item.type = DetectedObjectType( class_lbl, 1.0 )

            if self._mode == "detector" and \
               ( item.bounding_box.width() > max_length or \
                 item.bounding_box.height() > max_length ):
                use_frame = False
                break

            filtered_truth.add( item )

        if self._gt_frames_only and len( init_truth ) == 0:
            use_frame = False

        return filtered_truth, use_frame

    def extract_chips_for_dets( self, image_files, truth_sets ):
        import cv2
        output_files = []
        output_dets = []

        for i in range( len( image_files ) ):
            filename = image_files[ i ]
            groundtruth = truth_sets[ i ]
            detections = []

            if len( groundtruth ) > 0:
                img = cv2.imread( filename )
  
                img_max_x = np.shape( img )[1]
                img_max_y = np.shape( img )[0]

                # Run optional background detector on data
                if self._detector_model:
                    kw_image = Image( img )
                    kw_image_container = ImageContainer( kw_image )
                    detections = self._detector.detect( kw_image_container )

            if len( groundtruth ) == 0 and len( detections ) == 0:
                continue

            overlaps = np.zeros( ( len( detections ), len( groundtruth ) ) )
            det_boxes = []

            for det in detections:
                bbox = det.bounding_box()
                det_boxes.append( ( int( bbox.min_x() ),
                                    int( bbox.min_y() ),
                                    int( bbox.width() ),
                                    int( bbox.height() ) ) )

            for i, gt in enumerate( groundtruth ):
                # Extract chip for this detection
                bbox = gt.bounding_box()

                bbox_min_x = int( bbox.min_x() )
                bbox_max_x = int( bbox.max_x() )
                bbox_min_y = int( bbox.min_y() )
                bbox_max_y = int( bbox.max_y() )

                bbox_width = bbox_max_x - bbox_min_x
                bbox_height = bbox_max_y - bbox_min_y

                max_overlap = 0.0

                for j, det in enumerate( det_boxes ):

                    # Compute overlap between detection and truth
                    ( det_min_x, det_min_y, det_width, det_height ) = det

                    # Get the overlap rectangle
                    overlap_x0 = max( bbox_min_x, det_min_x )
                    overlap_y0 = max( bbox_min_y, det_min_y )
                    overlap_x1 = min( bbox_max_x, det_min_x + det_width )
                    overlap_y1 = min( bbox_max_y, det_min_y + det_height )

                    # Check if there is an overlap
                    if overlap_x1 - overlap_x0 <= 0 or overlap_y1 - overlap_y0 <= 0:
                        continue

                    # If yes, calculate the ratio of the overlap
                    det_area = float( det_width * det_height )
                    gt_area = float( bbox_width * bbox_height )
                    int_area = float( ( overlap_x1 - overlap_x0 ) * ( overlap_y1 - overlap_y0 ) )
                    overlap = min( int_area / det_area, int_area / gt_area )
                    overlaps[ j, i ] = overlap

                    if overlap >= self._min_overlap_for_association and overlap > max_overlap:
                        max_overlap = overlap

                        bbox_min_x = det_min_x
                        bbox_min_y = det_min_y
                        bbox_max_x = det_min_x + det_width
                        bbox_max_y = det_min_y + det_height

                        bbox_width = det_width
                        bbox_height = det_height

                bbox_area = bbox_width * bbox_height

                if self._area_lower_bound > 0 and bbox_area < self._area_lower_bound:
                    continue
                if self._area_upper_bound > 0 and bbox_area > self._area_upper_bound:
                    continue

                if self._border_exclude > 0:
                    if bbox_min_x <= self._border_exclude:
                        continue
                    if bbox_min_y <= self._border_exclude:
                        continue
                    if bbox_max_x >= img_max_x - self._border_exclude:
                        continue
                    if bbox_max_y >= img_max_y - self._border_exclude:
                        continue

                crop = img[ bbox_min_y:bbox_max_y, bbox_min_x:bbox_max_x ]
                self._sample_count = self._sample_count + 1
                crop_str = ( '%09d' %  self._sample_count ) + ".png"
                new_file = os.path.join( self._chip_directory, crop_str )
                cv2.imwrite( new_file, crop )

                # Set new box size for this detection
                gt.set_bounding_box(
                  BoundingBoxD( 0, 0, np.shape( crop )[1], np.shape( crop )[0] ) )
                new_set = DetectedObjectSet()
                new_set.add( gt )

                output_files.append( new_file )
                output_dets.append( new_set )

            neg_count = 0

            for j, det in enumerate( detections ):

                if max( overlaps[j] ) >= self._max_overlap_for_negative:
                    continue

                bbox = det.bounding_box()

                bbox_min_x = int( bbox.min_x() )
                bbox_max_x = int( bbox.max_x() )
                bbox_min_y = int( bbox.min_y() )
                bbox_max_y = int( bbox.max_y() )

                bbox_width = bbox_max_x - bbox_min_x
                bbox_height = bbox_max_y - bbox_min_y

                bbox_area = bbox_width * bbox_height

                if self._area_lower_bound > 0 and bbox_area < self._area_lower_bound:
                    continue
                if self._area_upper_bound > 0 and bbox_area > self._area_upper_bound:
                    continue

                if self._border_exclude > 0:
                    if bbox_min_x <= self._border_exclude:
                        continue
                    if bbox_min_y <= self._border_exclude:
                        continue
                    if bbox_max_x >= img_max_x - self._border_exclude:
                        continue
                    if bbox_max_y >= img_max_y - self._border_exclude:
                        continue

                # Handle random factor
                if self._max_neg_per_frame < 1.0 and random.uniform( 0, 1 ) > self._max_neg_per_frame:
                    break

                crop = img[ bbox_min_y:bbox_max_y, bbox_min_x:bbox_max_x ]
                self._sample_count = self._sample_count + 1
                crop_str = ( '%09d' %  self._sample_count ) + ".png"
                new_file = os.path.join( self._chip_directory, crop_str )
                cv2.imwrite( new_file, crop )

                # Set new box size for this detection
                det.set_bounding_box(
                  BoundingBoxD( 0, 0, np.shape( crop )[1], np.shape( crop )[0] ) )
                det.set_type(
                  DetectedObjectType( self._negative_category, 1.0 ) )
                new_set = DetectedObjectSet()
                new_set.add( det )

                output_files.append( new_file )
                output_dets.append( new_set )

                # Check maximum negative count
                neg_count = neg_count + 1
                if neg_count > self._max_neg_per_frame:
                    break

        return [ output_files, output_dets ]

    def add_data_from_disk( self, categories, train_files, train_dets, test_files, test_dets ):
        if self._no_format:
            return
        if len( train_files ) != len( train_dets ):
            print( "Error: train file and groundtruth count mismatch" )
            return
        if categories is not None:
            if self._detector_model:
                categories.add_class( self._negative_category, "", -1 )
            self._categories = categories.all_class_names()
        if self._mode == "detection_refiner":
            [ train_files, train_dets ] = self.extract_chips_for_dets( train_files, train_dets )
            [ test_files, test_dets ] = self.extract_chips_for_dets( test_files, test_dets )          
        for i in range( len( train_files ) + len( test_files ) ):
            if i < len( train_files ):
                filename = train_files[ i ]
                groundtruth, use_frame = self.filter_truth( train_dets[ i ], categories )
                if use_frame:
                    self._training_writer.write_set( groundtruth, os.path.abspath( filename ) )
            else:
                filename = test_files[ i-len( train_files ) ]
                groundtruth, use_frame = self.filter_truth( test_dets[ i-len( train_files ) ], categories )
                if use_frame:
                    self._validation_writer.write_set( groundtruth, os.path.abspath( filename ) )

    def update_model( self ):
        if not self._no_format:
            self._training_writer.complete()
            self._validation_writer.complete()

        gpu_string = ','.join([ str(i) for i in range(0,self._gpu_count) ])

        cmd = [ "python.exe" if os.name == 'nt' else "python", "-m" ]

        if self._mode == "frame_classifier" or self._mode == "detection_refiner":
            cmd += [ "bioharn.clf_fit",
                     "--name=" + self._identifier,
                     "--arch=" + self._arch,
                     "--schedule=ReduceLROnPlateau-p3-c3",
                     "--input_dims=" + self._chip_width + "," + self._chip_width,
                     "--patience=20" ]
        else:
            cmd += [ "bioharn.detect_fit",
                     "--nice=" + self._identifier,
                     "--arch=" + self._arch,
                     "--schedule=ReduceLROnPlateau-p2-c2",
                     "--input_dims=window",
                     "--window_dims=" + self._chip_width + "," + self._chip_width,
                     "--window_overlap=" + self._chip_overlap,
                     "--multiscale=False",
                     "--bstep=4" ]

            if os.name == 'nt':
                cmd.append( "--test_on_finish=False" )

            if len( self._backbone ) > 0:
                cmd.append( "--backbone_init=" + self._backbone )

        cmd += [ "--train_dataset=" + self._training_file,
                 "--vali_dataset=" + self._validation_file,
                 "--workdir=" + self._train_directory,
                 "--xpu=" + gpu_string,
                 "--workers=4",
                 "--normalize_inputs=True",
                 "--init=noop",
                 "--optim=sgd",
                 "--augmenter=" + self._augmentation,
                 "--max_epoch=" + self._max_epochs,
                 "--batch_size=" + self._batch_size,
                 "--lr=" + self._learning_rate,
                 "--timeout=" + self._timeout,
                 "--sampler_backend=none" ]

        if len( self._seed_model ) > 0:
            cmd.append( "--pretrained=" + self._seed_model )

        if self._allow_unicode != "auto":
            cmd.append( "--allow_unicode=" + self._allow_unicode  )

        channel_str = "rgb"
        if len( self._aux_image_labels ) > 0:
            for label in self._aux_image_labels.rstrip().split(','):
                channel_str = channel_str + "," + label
        cmd.append( "--channels=" + channel_str )

        if threading.current_thread().__class__.__name__ == '_MainThread':
            signal.signal( signal.SIGINT, lambda signal, frame: self.interupt_handler() )
            signal.signal( signal.SIGTERM, lambda signal, frame: self.interupt_handler() )

        self.proc = subprocess.Popen( cmd )
        self.proc.wait()

        self.save_final_model()

        print( "\nModel training complete!\n" )

    def interupt_handler( self ):
        self.proc.send_signal( signal.SIGINT )
        timeout = 0
        while self.proc.poll() is None:
            time.sleep( 0.1 )
            timeout += 0.1
            if timeout > 5:
                self.proc.kill()
                break
        self.save_final_model()
        sys.exit( 0 )

    def save_final_model( self ):
        if len( self._pipeline_template ) > 0:
            # Copy model file to final directory
            if self._mode == "frame_classifier" or self._mode == "detection_refiner":
                output_model_name = "trained_classifier.zip"
            else:
                output_model_name = "trained_detector.zip"

            final_model = os.path.join( self._train_directory,
              "fit", "nice", self._identifier, "deploy.zip" )
            output_model = os.path.join( self._output_directory,
              output_model_name )

            if not os.path.exists( final_model ):
                print( "\nModel failed to finsh training\n" )
                sys.exit( 0 )

            copyfile( final_model, output_model )

            # Copy pipeline file
            fin = open( self._pipeline_template )
            fout = open( os.path.join( self._output_directory, "detector.pipe" ), 'w' )
            all_lines = []
            for s in list( fin ):
                all_lines.append( s )
            for i, line in enumerate( all_lines ):
                line = line.replace( "[-MODEL-FILE-]", output_model_name )
                all_lines[i] = line.replace( "[-WINDOW-OPTION-]", self._resize_option )
            for s in all_lines:
                fout.write( s )
            fout.close()
            fin.close()

            # Output additional completion text
            print( "\nWrote finalized model to " + output_model )

            print( "\nThe " + self._train_directory + " directory can now be deleted, " \
                   "unless you want to review training metrics or generated plots in " \
                   "there first." )

def __vital_algorithm_register__():
    from kwiver.vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "netharn"

    if algorithm_factory.has_algorithm_impl_name(
      NetHarnTrainer.static_type_name(), implementation_name ):
        return

    algorithm_factory.add_algorithm( implementation_name,
      "PyTorch NetHarn detection training routine", NetHarnTrainer )

    algorithm_factory.mark_algorithm_as_loaded( implementation_name )
