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


''' Deduplication for I/O tools.

    Supersession matrix for I/O content tools:

    +--------------------------------+-------+---------------+-------------+---------------+-----------------+
    | Supersedes →                   | read  | read          | write_file  | write_pieces  | write_pieces    |
    | Superseded by ↓                |       | number-lines  |             |               | return-content  |
    +================================+=======+===============+=============+===============+=================+
    | read                           | ✅    | ✅            | ✅          | ✅            | ✅              |
    +--------------------------------+-------+---------------+-------------+---------------+-----------------+
    | read number-lines              | ✅    | ✅            | ✅          | ✅            | ✅              |
    +--------------------------------+-------+---------------+-------------+---------------+-----------------+
    | write_file                     | ✅    | ✅            | ✅          | ✅            | ✅              |
    +--------------------------------+-------+---------------+-------------+---------------+-----------------+
    | write_pieces                   | ❌    | ❌            | ❌          | ❌            | ❌              |
    +--------------------------------+-------+---------------+-------------+---------------+-----------------+
    | write_pieces return-content    | ✅    | ✅            | ✅          | ✅            | ✅              |
    +--------------------------------+-------+---------------+-------------+---------------+-----------------+

    Note: Directory survey operations (``list_folder``) are handled by
    ``SurveyDirectoryDeduplicator``.
''' # noqa: E501

from . import __


class IoContentDeduplicator( __.Deduplicator ):
    ''' Deduplicates I/O content operations. '''

    @classmethod
    def provide_invocable_names( selfclass ) -> __.AbstractCollection[ str ]:
        return { 'read', 'write_file', 'write_pieces' }

    def is_duplicate(
        self,
        invocable_name: str,
        arguments: __.AbstractDictionary[ str, __.a.Any ],
    ) -> bool:
        our_location = self.arguments.get( 'location' )
        their_location = arguments.get( 'location' )
        if our_location != their_location: return False
        match self.invocable_name:
            case 'read': return True
            case 'write_file': return True
            case 'write_pieces':
                return self.arguments.get( 'return-content', True )
        return False


class SurveyDirectoryDeduplicator( __.Deduplicator ):
    ''' Deduplicates directory survey operations. '''

    @classmethod
    def provide_invocable_names( selfclass ) -> __.AbstractCollection[ str ]:
        return { 'list_folder' }

    def is_duplicate(
        self,
        invocable_name: str,
        arguments: __.AbstractDictionary[ str, __.a.Any ],
    ) -> bool:
        our_location = self.arguments.get( 'location' )
        their_location = arguments.get( 'location' )
        if our_location != their_location: return False
        # Only supersede if filters and recursion are equivalent
        # or more inclusive
        our_filters = set( self.arguments.get( 'filters', [ ] ) )
        their_filters = set( arguments.get( 'filters', [ ] ) )
        if not our_filters.issubset( their_filters ): return False
        if (    self.arguments.get( 'recurse', True )
            <   arguments.get( 'recurse', True )
        ): return False
        return True
