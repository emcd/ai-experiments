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


''' Filters for directory entries. '''

# ruff: noqa: F401


from . import __
from . import gitignore
from . import vcs
# TODO: -permissions:r
# TODO: -permissions:cud
# TODO: +permissions:cud
# TODO: +permissions:x
# TODO: -species:file
# TODO: +species:directory
# TODO: +species:symlink
# TODO: +species:SPECIALS
# TODO? +mimetype:image/*
# TODO? +mimetype:application/octet-stream
# TODO? +expiration>=4h  # also: Unix epoch or ISO 8601
# TODO? +mtime<30d


