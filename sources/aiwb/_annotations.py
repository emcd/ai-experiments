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


''' Standard annotations across Python versions. '''

# ruff: noqa: F401
# pylint: disable=unused-import


from typing_extensions import (
    Annotated as Annotation,
    Any,
    Callable,
    ClassVar,
    Doc,
    Generic,
    Literal,
    Never,
    Optional as Nullable, # Prefer to <type> | None.
    Protocol,
    Self,
    TypeAlias,
    TypeVar,
    Union, # Prefer to <T> | <U> for multiline forms.
    cast,
    override,
    runtime_checkable,
)


__all__ = ( )
