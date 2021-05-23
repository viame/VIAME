# ckwg +29
# Copyright 2019 by Kitware, Inc.
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

from kwiver.vital.algo import DetectedObjectSetOutput, TrainDetector

from kwiver.vital.types import (
    BoundingBoxD, CategoryHierarchy, DetectedObject, DetectedObjectSet,
)

from PIL import Image

from distutils.util import strtobool
from shutil import copyfile

import argparse
import numpy as np
import torch
import pickle
import os
import signal
import sys

class MMDetTrainer( TrainDetector ):
    """
    Implementation of TrainDetector class
    """
    def __init__( self ):
        TrainDetector.__init__( self )

        self._config_file = ""
        self._seed_weights = ""
        self._train_directory = "deep_training"
        self._output_directory = "category_models"
        self._output_prefix = "custom_cfrnn"
        self._pipeline_template = ""
        self._gpu_count = -1
        self._random_seed = "none"
        self._tmp_training_file = "training_truth.pickle"
        self._tmp_validation_file = "validation_truth.pickle"
        self._validate = True
        self._gt_frames_only = False
        self._launcher = "pytorch"  # "none, pytorch, slurm, or mpi" 
        self._train_in_new_process = True
        self._categories = []

    def get_configuration( self ):
        # Inherit from the base class
        cfg = super( TrainDetector, self ).get_configuration()

        cfg.set_value( "config_file", self._config_file )
        cfg.set_value( "seed_weights", self._seed_weights )
        cfg.set_value( "train_directory", self._train_directory )
        cfg.set_value( "output_directory", self._output_directory )
        cfg.set_value( "output_prefix", self._output_prefix )
        cfg.set_value( "pipeline_template", self._pipeline_template )
        cfg.set_value( "gpu_count", str( self._gpu_count ) )
        cfg.set_value( "random_seed", str( self._random_seed ) )
        cfg.set_value( "validate", str( self._validate ) )
        cfg.set_value( "gt_frames_only", str( self._gt_frames_only ) )
        cfg.set_value( "launcher", str( self._launcher ) )
        cfg.set_value( "train_in_new_process", str( self._train_in_new_process ) )

        return cfg

    def set_configuration( self, cfg_in ):
        cfg = self.get_configuration()
        cfg.merge_config( cfg_in )

        # Read configs from file
        self._config_file = str( cfg.get_value( "config_file" ) )
        self._seed_weights = str( cfg.get_value( "seed_weights" ) )
        self._train_directory = str( cfg.get_value( "train_directory" ) )
        self._output_directory = str( cfg.get_value( "output_directory" ) )
        self._output_prefix = str( cfg.get_value( "output_prefix" ) )
        self._pipeline_template = str( cfg.get_value( "pipeline_template" ) )
        self._gpu_count = int( cfg.get_value( "gpu_count" ) )
        self._validate = strtobool( cfg.get_value( "validate" ) )
        self._gt_frames_only = strtobool( cfg.get_value( "gt_frames_only" ) )
        self._launcher = str( cfg.get_value( "launcher" ) )
        self._train_in_new_process = strtobool( cfg.get_value( "train_in_new_process" ) )

        # Check variables
        if self._launcher != "none" and self._validate:
            print( "Warning: defaulting to distributed train due to validation enable" )
            self._launcher = "pytorch"

        if ( self._validate or self._gpu_count != 1 ) and torch.cuda.is_available():
            if self._gpu_count < 0:
                self._gpu_count = torch.cuda.device_count()
        else:
            print( "Multiple GPUs not available for distributed training, disabling" )
            self._validate = False
            self._launcher = "none"

        if self._launcher != "none":
            if self._gpu_count == 1 and not self._validate:
                print( "Warning: defaulting to non-distributed training procedure" )
                self._launcher = "none"
            if not self._train_in_new_process:
                print( "Warning: defaulting to external train in spawned process" )
                self._train_in_new_process = True

        if self._gpu_count > 1:
            print( "Warning: multi-GPU only supports frames with GT, disabling others" )
            self._gt_frames_only = True

        # Make required directories
        self._train_config = "train_config.py"

        if self._train_directory is not None:
            self._train_config = os.path.join( self._train_directory,
                self._train_config )
            self._training_store = os.path.join(
                self._train_directory, self._tmp_training_file )
            self._validation_store = os.path.join(
                self._train_directory, self._tmp_validation_file )
            if not os.path.exists( self._train_directory ):
                os.mkdir( self._train_directory )
        else:
            self._training_store = self._tmp_training_file
            self._validation_store = self._tmp_validation_file

        # Initialize persistent variables
        self._training_data = []
        self._validation_data = []

        self._sample_count = 0
        self._training_width_sum = 0
        self._training_height_sum = 0

        self._images_per_gpu = 2
        self._workers_per_gpu = 2
        self._base_size = "(1333, 800)"

        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            total_mem = torch.cuda.get_device_properties( 0 ).total_memory
            if total_mem < 9e9:
                self._images_per_gpu = 1
                self._workers_per_gpu = 1

    def check_configuration( self, cfg ):
        if not cfg.has_value( "config_file" ) or len( cfg.get_value( "config_file") ) == 0:
            print( "A config file must be specified!" )
            return False
        return True

    def __getstate__( self ):
        return self.__dict__

    def __setstate__( self, dict ):
        self.__dict__ = dict

    def load_network( self ):
        from mmcv import Config
        self._cfg = Config.fromfile( self._train_config )

        if self._cfg.get( 'cudnn_benchmark', False ):
            torch.backends.cudnn.benchmark = True

        if self._train_directory is not None:
            self._cfg.work_dir = self._train_directory

        if self._seed_weights is not None:
            self._cfg.load_from = self._seed_weights

        if self._gpu_count is not None and self._gpu_count > 0:
            self._cfg.gpus = self._gpu_count
            flux_factor = self._images_per_gpu * self._gpu_count
            self._cfg.optimizer['lr'] = self._cfg.optimizer['lr'] * flux_factor

        if self._cfg.checkpoint_config is not None:
            from mmdet import __version__
            self._cfg.checkpoint_config.meta = dict(
                mmdet_version=__version__, config=self._cfg.text )

        if self._launcher == 'none':
            self._distributed = False
        else:
            self._distributed = True
            from mmcv.runner import init_dist
            init_dist( self._launcher, **self._cfg.dist_params )

        from mmdet.apis import get_root_logger
        self._logger = get_root_logger( self._cfg.log_level )
        self._logger.info( 'Distributed training: {}'.format( self._distributed ) )

        if self._random_seed is not 'none':
            self._logger.info( 'Set random seed to {}'.format( self._random_seed ) )
            from mmdet.apis import set_random_seed
            if isinstance( self._random_seed, int ):
                set_random_seed( int( self._random_seed ) )

        from mmdet.models import build_detector

        if self._cfg.model[ 'pretrained' ] is not None:
            if not os.path.exists( self._cfg.model[ 'pretrained' ] ):
                dirname = os.path.dirname( self._config_file )
                relpath = os.path.join( dirname, self._cfg.model[ 'pretrained' ] )
                if os.path.exists( relpath ):
                    self._cfg.model[ 'pretrained' ] = relpath

        self._model = build_detector(
            self._cfg.model, train_cfg=self._cfg.train_cfg, test_cfg=self._cfg.test_cfg )

    def add_data_from_disk( self, categories, train_files, train_dets, test_files, test_dets ):
        if len( train_files ) != len( train_dets ):
            print( "Error: train file and groundtruth count mismatch" )
            return

        if categories is not None:
            self._categories = categories.all_class_names()

        for i in range( len( train_files ) + len( test_files ) ):
            entry = dict()

            is_train = ( i < len( train_files ) )

            if is_train:
                filename = train_files[ i ]
                groundtruth = train_dets[ i ]
            else:
                filename = test_files[ i-len( train_files ) ]
                groundtruth = test_dets[ i-len( train_files ) ]

            im = Image.open( filename, 'r' )
            width, height = im.size

            if width <= 1 or height <= 1:
                continue

            annotations = dict()

            boxes = np.ndarray( ( 0, 4 ) )
            labels = np.ndarray( 0 )

            for i, item in enumerate( groundtruth ):

                class_lbl = item.type.get_most_likely_class()

                if categories is not None and not categories.has_class_name( class_lbl ):
                    continue

                obj_box = [ [ item.bounding_box().min_x(),
                              item.bounding_box().min_y(),
                              item.bounding_box().max_x(),
                              item.bounding_box().max_y() ] ]

                if categories is not None:
                    class_id = categories.get_class_id( class_lbl ) + 1
                else:
                    if class_lbl not in self._categories:
                        self._categories.append( class_lbl )
                    class_id = self._categories.index( class_lbl ) + 1

                boxes = np.append( boxes, obj_box, axis = 0 )
                labels = np.append( labels, class_id )

            if self._gt_frames_only and len( labels ) == 0:
                continue

            annotations[ "bboxes" ] = boxes.astype( np.float32 )
            annotations[ "labels" ] = labels.astype( np.int_ )

            entry[ "filename" ] = filename
            entry[ "width" ] = width
            entry[ "height" ] = height
            entry[ "ann" ] = annotations

            self._sample_count = self._sample_count + 1

            self._training_width_sum = self._training_width_sum + width
            self._training_height_sum = self._training_height_sum + height

            if is_train or not self._validate:
                self._training_data.append( entry )
            else:
                self._validation_data.append( entry )

    def update_model( self ):

        with open( self._training_store, 'wb' ) as fp:
            pickle.dump( self._training_data, fp )

        if len( self._validation_store ) > 0:
            with open( self._validation_store, 'wb' ) as fp:
                pickle.dump( self._validation_data, fp )
        else:
            self._validate = False

        self.insert_training_params( self._config_file, self._train_config )

        self.save_model_files( is_final=False )

        if self._train_in_new_process:
            self.external_update()
        else:
            self.internal_update()

        self.save_model_files( is_final=True )

        print( "\nModel training complete!\n" )

    def internal_update( self ):
        self.load_network()

        from mmdet.datasets.custom import CustomDataset

        signal.signal( signal.SIGINT, lambda signal, frame: self.interupt_handler() )

        train_dataset = CustomDataset(
            self._training_store,
            self._cfg.train_pipeline )

        if self._validate:
            validation_dataset = CustomDataset(
                self._validation_store,
                self._cfg.test_pipeline )
            self._cfg.data.val = validation_dataset
            self._cfg.data.val.type = "CustomDataset"

        from mmdet.apis import train_detector

        train_detector(
            self._model,
            train_dataset,
            self._cfg,
            distributed = self._distributed,
            validate = self._validate )

    def external_update( self ):
        state_file = os.path.join( self._train_directory, "trainer_state.pickle" )

        with open( state_file, 'wb' ) as fp:
            pickle.dump( self, fp )

        state_file = state_file.replace( "\\", "\\\\" )

        cmd = [ str( sys.executable ) ]

        if self._launcher == "pytorch":
            current_folder = os.path.dirname( os.path.realpath( __file__) )
            launcher_script = os.path.join( current_folder, "mmdet_launcher.py" )
            launcher_script.replace( "\\", "\\\\" )

            cmd += [ "-m", "torch.distributed.launch" ]
            cmd += [ "--nproc_per_node=" + str( self._gpu_count ) ]
            cmd += [ launcher_script, state_file ]
        else:
            cmd += [ "-c", "\"import pickle;"
                     "infile=open('" + state_file + "','rb');"
                     "trainer=pickle.load(infile);"
                     "trainer.internal_update();\"" ]

        print( "Executing external command: " + ' '.join( cmd ) )

        os.system( ' '.join( cmd ) )

    def interupt_handler( self ):
        self.save_model_files( is_final=True )
        sys.exit( 0 )

    def save_model_files( self, is_final=False ):
        input_wgt_file_fp = os.path.join( self._train_directory, "latest.pth" )

        output_cfg_file = self._output_prefix + ".py"
        output_wgt_file = self._output_prefix + ".pth"
        output_lbl_file = self._output_prefix + ".lbl"
        output_pipeline = "detector.pipe"

        if len( self._output_directory ) > 0:
            if not os.path.exists( self._output_directory ):
                os.mkdir( self._output_directory )
            output_cfg_file_fp = os.path.join( self._output_directory, output_cfg_file )
            output_wgt_file_fp = os.path.join( self._output_directory, output_wgt_file )
            output_lbl_file_fp = os.path.join( self._output_directory, output_lbl_file )
            output_pipeline_fp = os.path.join( self._output_directory, output_pipeline )
        else:
            output_cfg_file_fp = output_cfg_file
            output_wgt_file_fp = output_wgt_file
            output_lbl_file_fp = output_lbl_file
            output_pipeline_fp = output_pipeline

        self.insert_training_params( self._config_file, output_cfg_file_fp )

        if is_final:
            copyfile( input_wgt_file_fp, output_wgt_file_fp )

        with open( output_lbl_file_fp, "w" ) as fout:
            for category in self._categories:
                fout.write( category + "\n" )

        if len( self._pipeline_template ) > 0:
            input_wgt_relpath = input_wgt_file_fp

            if not os.path.isabs( input_wgt_file_fp ):
                input_wgt_relpath = os.path.join( "..", input_wgt_relpath )

            self.insert_model_files( self._pipeline_template,
                                     output_pipeline_fp,
                                     output_cfg_file,
                                     output_wgt_file if is_final else input_wgt_relpath,
                                     output_lbl_file )

    def insert_training_params( self, input_cfg, output_cfg ):

        average_height = int( self._training_height_sum / self._sample_count )
        average_width = int( self._training_width_sum / self._sample_count )

        repl_strs = [ [ "[-CLASS_COUNT_INSERT-]", str(len(self._categories)+1) ],
                      [ "[-IMAGE_SCALE_INSERT-]", self._base_size ],
                      [ "[-IMAGES_PER_GPU_INSERT-]", str(self._images_per_gpu) ],
                      [ "[-WORKERS_PER_GPU_INSERT-]", str(self._workers_per_gpu) ] ]

        self.replace_strs_in_file( input_cfg, output_cfg, repl_strs )

    def insert_model_files( self, input_cfg, output_cfg, net, wgt, cls ):

        repl_strs = [ [ "[-NETWORK-CONFIG-]", net ],
                      [ "[-NETWORK-WEIGHTS-]", wgt ],
                      [ "[-NETWORK-CLASSES-]", cls ] ]

        self.replace_strs_in_file( input_cfg, output_cfg, repl_strs )

    def replace_strs_in_file( self, input_cfg, output_cfg, repl_strs ):

        fin = open( input_cfg )
        fout = open( output_cfg, 'w' )

        all_lines = []
        for s in list( fin ):
            all_lines.append( s )

        for repl in repl_strs:
            for i, s in enumerate( all_lines ):
                all_lines[i] = s.replace( repl[0], repl[1] )
        for s in all_lines:
            fout.write( s )

        fout.close()
        fin.close()


def __vital_algorithm_register__():
    from kwiver.vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "mmdet"

    if algorithm_factory.has_algorithm_impl_name(
      MMDetTrainer.static_type_name(), implementation_name ):
        return

    algorithm_factory.add_algorithm( implementation_name,
      "PyTorch MMDetection training routine", MMDetTrainer )

    algorithm_factory.mark_algorithm_as_loaded( implementation_name )
