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

from kwiver.sprokit.processes.kwiver_process import KwiverProcess
from kwiver.sprokit.pipeline import process

from kwiver.vital.types import Image
from kwiver.vital.types import ImageContainer

class hello_world_filter(KwiverProcess):
    """
    This process gets an image as input, does some stuff to it and
    sends the modified version to the output port.
    """
    # ----------------------------------------------
    def __init__(self, conf):
        KwiverProcess.__init__(self, conf)

        self.add_config_trait("text", "text", 'Hello World',
          'Text to display to user.')

        self.declare_config_using_trait('text')

        self.add_port_trait('out_image', 'image', 'Processed image')

        # set up required flags
        optional = process.PortFlags()
        required = process.PortFlags()
        required.add(self.flag_required)

        #  declare our input port ( port-name,flags)
        self.declare_input_port_using_trait('image', required)
        self.declare_output_port_using_trait('out_image', optional )

    # ----------------------------------------------
    def _configure(self):
        print( "[DEBUG] ----- configure" )
        self.text = self.config_value('text')

        self._base_configure()

    # ----------------------------------------------
    def _step(self):
        print( "[DEBUG] ----- start step" )
        # grab image container from port using traits
        in_img_c = self.grab_input_using_trait('image')

        # Get python image from conatiner (just for show)
        in_img = in_img_c.get_image()

        # Print out text to screen
        print( "Text: " + str( self.text ) )

        # push dummy image object (same as input) to output port
        self.push_to_port_using_trait('out_image', ImageContainer(in_img))

        self._base_step()
