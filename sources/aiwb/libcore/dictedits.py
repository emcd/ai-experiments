# vim: set filetype=python fileencoding=utf-8:
# -*- coding: utf-8 -*-

#============================================================================#
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License");           #
#  you may not use this file except in compliance with the License.          #
#  You may obtain a copy of the License at                                   #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  Unless required by applicable law or agreed to in writing, software       #
#  distributed under the License is distributed on an "AS IS" BASIS,         #
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  #
#  See the License for the specific language governing permissions and       #
#  limitations under the License.                                            #
#                                                                            #
#============================================================================#


''' Support for edits on nested dictionaries. '''
# TODO: Independent package.
# TODO: Copying edits, not just in-place edits.


from . import __


class Edit(
    __.immut.DataclassProtocol, __.typx.Protocol,
    decorators = ( __.typx.runtime_checkable, ),
):
    ''' Base representation of an edit to configuration. '''

    address: __.cabc.Sequence[ str ]

    @__.abc.abstractmethod
    def __call__( self, configuration: __.cabc.MutableMapping ):
        ''' Performs edit. '''
        raise NotImplementedError

    def dereference(
        self,
        configuration: __.cabc.MutableMapping
    ) -> __.typx.Any:
        ''' Dereferences value at address in configuration. '''
        configuration_ = configuration
        for part in self.address:
            # TODO: Error on missing part.
            configuration_ = configuration_[ part ]
        return configuration_

    def inject(
        self,
        configuration: __.cabc.MutableMapping,
        value: __.typx.Any
    ):
        ''' Injects value at address in configuration. '''
        configuration_ = configuration
        for part in self.address[ : -1 ]:
            if part not in configuration_: configuration_[ part ] = { }
            configuration_ = configuration_[ part ]
        configuration_[ self.address[ -1 ] ] = value


class ElementsEntryEdit( Edit ):
    ''' Applies entry edit to every matching dictionary in array. '''

    editee: tuple[ str, __.typx.Any ]
    identifier: __.typx.Optional[ tuple[ str, __.typx.Any ] ] = None

    def __call__( self, configuration: __.cabc.MutableMapping ):
        array = self.dereference( configuration )
        if self.identifier: iname, ivalue = self.identifier
        else: iname, ivalue = None, None
        ename, evalue = self.editee
        for element in array:
            if iname:
                # TODO: Error on missing identifier.
                if ivalue != element[ iname ]: continue
            element[ ename ] = evalue


class SimpleEdit( Edit ):
    ''' Applies edit to single entity. '''

    value: __.typx.Any

    def __call__( self, configuration: __.cabc.MutableMapping ):
        self.inject( configuration, self.value )


# TODO: Python 3.12: Use type statement for aliases.
Edits: __.typx.TypeAlias = __.cabc.Iterable[ Edit ]
