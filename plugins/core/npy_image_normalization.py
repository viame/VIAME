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

from kwiver.vital.algo import ImageFilter

from kwiver.vital.types import Image
from kwiver.vital.types import ImageContainer

import numpy as np

class PercentileNorm16BitTo8Bit( ImageFilter ):
  """
  Implementation of ImageFilter class
  """
  def __init__( self ):
    ImageFilter.__init__( self )

  def get_configuration( self ):
    cfg = super( ImageFilter, self ).get_configuration()
    return cfg

  def set_configuration( self, cfg_in ):
    return

  def check_configuration( self, cfg ):
    return True

  def filter( self, in_img ):
    img = in_img.image().asarray().astype( "uint16" )

    mi = np.percentile( img, 1 )
    ma = np.percentile( img, 100 )

    normalized = ( img - mi ) / ( ma - mi )
    normalized = normalized * 255
    normalized[ normalized < 0 ] = 0

    output = ImageContainer( Image( normalized.astype( "uint8" ) ) )
    return output

def __vital_algorithm_register__():
  from kwiver.vital.algo import algorithm_factory

  # Register Algorithm
  implementation_name  = "npy_percentile_norm"
  if algorithm_factory.has_algorithm_impl_name(
      PercentileNorm16BitTo8Bit.static_type_name(), implementation_name ):
    return

  algorithm_factory.add_algorithm( implementation_name,
    "Numpy percentile normalization", PercentileNorm16BitTo8Bit )

  algorithm_factory.mark_algorithm_as_loaded( implementation_name )
