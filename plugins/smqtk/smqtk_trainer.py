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

from kwiver.vital.algo import TrainDetector
from kwiver.vital.algo import DetectedObjectSetOutput

from distutils.util import strtobool
from shutil import copyfile

import os
import sys
import signal
import sys
import subprocess
import threading
import time

import viame.arrows.smqtk.smqtk_train_svm_models as trainer

class SMQTKTrainer( TrainDetector ):
    """
    Implementation of TrainDetector class
    """
    def __init__( self ):
        TrainDetector.__init__( self )

        self._root_dir = ""

        self._mode = "detector"
        self._gt_frames_only = False
        self._ingest_pipeline = ""
        self._pipeline_template = ""
        self._output_directory = "category_models"

    def get_configuration( self ):
        cfg = super( TrainDetector, self ).get_configuration()
        cfg.set_value( "mode", self._mode )
        cfg.set_value( "gt_frames_only", str( self._gt_frames_only ) )
        cfg.set_value( "ingest_pipeline", self._ingest_pipeline )
        cfg.set_value( "pipeline_template", self._pipeline_template )
        cfg.set_value( "output_directory", self._output_directory )
        return cfg

    def set_configuration( self, cfg_in ):
        cfg = self.get_configuration()
        cfg.merge_config( cfg_in )

        self._mode = str( cfg.get_value( "mode" ) )
        self._gt_frames_only = strtobool( cfg.get_value( "gt_frames_only" ) )
        self._ingest_pipeline = str( cfg.get_value( "ingest_pipeline" ) )
        self._pipeline_template = str( cfg.get_value( "pipeline_template" ) )
        self._output_directory = str( cfg.get_value( "output_directory" ) )

        if not self._ingest_pipeline:
            if self._mode == "detector":
                pipe_file = "index_default.svm.pipe"
            elif self._gt_frames_only:
                pipe_file = "index_full_frame.svm.annot_only.pipe"
            else:
                pipe_file = "index_full_frame.svm.pipe"
            self._ingest_pipeline = os.path.join( "pipelines", pipe_file )

        self._viame_install = os.environ['VIAME_INSTALL']

        if len( self._viame_install ) < 0:
            print( "ERROR: VIAME_INSTALL OS variable required" )
            return False
        return True

    def check_configuration( self, cfg ):
        return True

    def add_data_from_disk( self, categories, train_files, train_dets, test_files, test_dets ):
        for image_file in train_files:
            root_dir = os.path.dirname( os.path.dirname( image_file ) )
            if len( self._root_dir ) > 0 and root_dir != self._root_dir:
                print( "ERROR: Inconsistent root dirs, exiting" )
                sys.exit( 0 )
            self._root_dir = root_dir

    def update_model( self ):

        cmd = [ "python.exe" if os.name == 'nt' else "python" ]

        script = os.path.join( self._viame_install, "configs", "process_video.py" )

        cmd += [ script,
                 "--init",
                 "-d", self._root_dir,
                 "-p", self._ingest_pipeline,
                 "-logs", "PIPE",
                 "-o", "database",
                 "--build-index",
                 "-auto-detect-gt", "viame_csv",
                 "--no-reset-prompt",
                 "-install", self._viame_install ]

        if threading.current_thread().__class__.__name__ == '_MainThread':
            signal.signal( signal.SIGINT, lambda signal, frame: self.interupt_handler() )
            signal.signal( signal.SIGTERM, lambda signal, frame: self.interupt_handler() )

        self.proc = subprocess.Popen( cmd )
        self.proc.wait()

        trainer.generate_svm_models()

        fin = open( self._pipeline_template )
        fout = open( os.path.join( self._output_directory, "detector.pipe" ), 'w' )
        for s in list( fin ):
            fout.write( s )
        fout.close()
        fin.close()

    def interupt_handler( self ):
        self.proc.send_signal( signal.SIGINT )
        timeout = 0
        while self.proc.poll() is None:
            time.sleep( 0.1 )
            timeout += 0.1
            if timeout > 5:
                self.proc.kill()
                break
        sys.exit( 0 )

def __vital_algorithm_register__():
    from kwiver.vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "smqtk"

    if algorithm_factory.has_algorithm_impl_name(
      SMQTKTrainer.static_type_name(), implementation_name ):
        return

    algorithm_factory.add_algorithm( implementation_name,
      "PyTorch SMQTK detection training routine", SMQTKTrainer )

    algorithm_factory.mark_algorithm_as_loaded( implementation_name )
