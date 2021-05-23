#ckwg +28
# Copyright 2018 by Kitware, Inc.
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

from kwiver.kwiver_process import KwiverProcess

from kwiver.vital.types import new_descriptor, DescriptorSet

class SmqtkFetchDescriptors (KwiverProcess):
    def __init__(self, conf):
        KwiverProcess.__init__(self, conf)

        # register python config file
        self.add_config_trait(
            'config_file', 'config_file', '',
            'Path to the json configuration file for the descriptor index to fetch from.'
        )
        self.declare_config_using_trait('config_file')

        # set up required flags
        optional = process.PortFlags()
        required = process.PortFlags()
        required.add(self.flag_required)

        self.declare_input_port_using_trait('descriptor_set', required)
        self.declare_output_port_using_trait('string_vector', optional)

    def _configure(self):
        self.config_file = self.config_value('config_file')

        # parse json file
        with open(self.config_file) as data_file:
          self.json_config = json.load(data_file)

        # setup smqtk elements
        self.smqtk_descriptor_element_factory = \
            smqtk.representation.DescriptorElementFactory.from_config(
                self.json_config['descriptor_factory']
            )

        #: :type: smqtk.representation.DescriptorIndex
        self.smqtk_descriptor_index = smqtk.utils.plugin.from_plugin_config(
            self.json_config['descriptor_index'],
            smqtk.representation.get_descriptor_index_impls()
        )

        self._base_configure()

    def _step(self):
        #
        # Grab input values from ports using traits.
        #
        # Vector of UIDs for vector of descriptors in descriptor_set.
        #
        #: :type: list[str]
        string_tuple = self.grab_input_using_trait('string_vector')

        descriptors = self.smqtk_descriptor_index.get_many_descriptors(string_tuple)
        vital_descriptors = []

        for desc in descriptors:
            vector = desc.vector()
            vital_desc = new_descriptor(len(vector), "d")
            vital_desc[:] = vector
            vital_descriptors.append(vital_desc)

        vital_descriptor_set = DescriptorSet(vital_descriptors)
        self.push_to_port_using_trait('descriptor_set', vital_descriptor_set)

        self._base_step()
