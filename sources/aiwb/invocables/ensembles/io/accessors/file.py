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


''' Implementation of filesystem I/O operations. '''


from . import __


@__.standard_dataclass
class Accessor( __.Accessor ):

    location: __.Path

    @classmethod
    def from_url_parts( selfclass, parts: __.UrlParts ) -> __.a.Self:
        if '.' == parts.netloc: location = __.Path( ) / parts.path
        elif parts.netloc:
            raise NotImplementedError(
                f"Shares not supported in file URLs. URL: {parts}" )
        else: location = __.Path( parts.path )
        return selfclass( location )

    async def list_folder(
        self, context: __.Context, arguments: __.SurveyDirectoryArguments,
    ) -> __.AbstractDictionary:
        return await survey_directory( context, arguments )

    async def read(
        self, context: __.Context, arguments: __.AcquireContentArguments,
    ) -> __.AbstractDictionary:
        # TODO: Implement.
        raise NotImplementedError

    async def write(
        self, context: __.Context, arguments: __.UpdateContentArguments,
    ) -> __.AbstractDictionary:
        # TODO: Implement.
        raise NotImplementedError

__.accessors[ '' ] = Accessor
__.accessors[ 'file' ] = Accessor


async def survey_directory(
    context: __.Context, arguments: __.SurveyDirectoryArguments
) -> __.AbstractDictionary:
    # TODO: Implement.
    pass
