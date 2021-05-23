#ckwg +28
# Copyright 2019 by Kitware, Inc.
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

from kwiver.sprokit.processes.kwiver_process import KwiverProcess
from kwiver.sprokit.pipeline import process

from kwiver.vital.types import Image
from kwiver.vital.types import ImageContainer

from PIL import Image as pil_image
from kwiver.vital.util.VitalPIL import get_pil_image, from_pil

import cv2
import numpy as np

class filter_based_on_ref_process( KwiverProcess ):
    """
    This process blanks out images which don't have detections on them.
    """
    # -------------------------------------------------------------------------
    def __init__( self, conf ):
        KwiverProcess.__init__( self, conf )

        # set up configs
        self.add_config_trait( "reference_image", "reference_image",
                               '', 'Reference noise image' )
        self.add_config_trait( "response_kernel", "response_kernel",
                               '25', 'Response kernel size.' )
        self.add_config_trait( "smooth_kernel", "smooth_kernel",
                               '50', 'Local average kernel size' )

        self.declare_config_using_trait( 'reference_image' )
        self.declare_config_using_trait( 'response_kernel' )
        self.declare_config_using_trait( 'smooth_kernel' )

        # set up required flags
        optional = process.PortFlags()
        required = process.PortFlags()
        required.add( self.flag_required )

        # declare our ports (port-name, flags)
        self.declare_input_port_using_trait( 'image', required )
        self.declare_output_port_using_trait( 'image', optional )

    # -------------------------------------------------------------------------
    def _configure( self ):
        self._base_configure()

        self._reference_image = str( self.config_value( 'reference_image' ) )
        self._response_kernel = int( self.config_value( 'response_kernel' ) )
        self._smooth_kernel = int( self.config_value( 'smooth_kernel' ) )

        noise_frame = cv2.imread( self._reference_image )
        self._noise_fft = np.fft.fft2( noise_frame )

    # -------------------------------------------------------------------------
    def _step( self ):
        # grab image container from port using traits
        input_c = self.grab_input_using_trait( 'image' )

        # Get python image from conatiner and perform operation
        input_npy = input_c.image().asarray()
        input_8bit = input_npy.astype( 'uint8' )

        input_fft = np.fft.fft2( input_8bit )

        filt = input_fft - self._noise_fft

        im_filt = np.absolute( np.fft.ifft2( filt ) )

        im_filt = np.log( cv2.blur( im_filt, ( self._response_kernel, self._response_kernel ) ) )
        im_filt = ( im_filt - im_filt.min() ) / ( im_filt.max() - im_filt.min() )

        smoothed_8bit = cv2.blur( input_8bit, ( self._smooth_kernel, self._smooth_kernel ) )
        
        output_image = input_8bit * im_filt + smoothed_8bit * ( 1.0 - im_filt )

        self.push_to_port_using_trait( 'image', ImageContainer( \
          from_pil( pil_image.fromarray( output_image.astype( 'uint8' ) ) ) ) )
    
        self._base_step()
