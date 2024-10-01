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

''' Utilities for implementing location accessors. '''


from __future__ import annotations

from . import __
from . import core as _core
from . import exceptions as _exceptions


def honor_inode_attributes(
    inode: _core.Inode,
    attributes: _core.InodeAttributes,
    error_to_raise: _exceptions.LocationOperateFailure,
    content: __.Optional[ bytes ] = __.absent,
) -> _core.Inode:
    ''' Honor requests for specific inode attributes. '''
    # Note: This function is too long. Not seeing a good way to break it up.
    Iattrs = _core.InodeAttributes
    aname = None
    have_content = __.absent is not content
    bytes_count = inode.bytes_count
    if (    not aname and Iattrs.BytesCount & attributes
            and not isinstance( bytes_count, int ) # 0 is falsey
    ):
        if have_content: bytes_count = len( content )
        else: aname = 'bytes_count'
    content_id = inode.content_id
    if not aname and Iattrs.ContentId & attributes and not content_id:
        if have_content:
            from hashlib import sha256
            hasher = sha256( )
            hasher.update( content )
            content_id = "sha256:{}".format( hasher.hexdigest( ) )
        else: aname = 'content_id'
    mimetype = inode.mimetype
    if not aname and Iattrs.Mimetype & attributes and not mimetype:
        if have_content:
            from magic import from_buffer
            mimetype = from_buffer( content, mime = True )
        else: aname = 'mimetype'
    charset = inode.charset
    if not aname and Iattrs.Charset & attributes and not charset:
        if not mimetype or not mimetype.startswith( 'text/' ): charset = None
        elif have_content:
            from chardet import detect
            charset = detect( content )[ 'encoding' ]
        else: aname = 'charset'
    mtime = inode.mtime
    if not aname and Iattrs.Mtime & attributes and not mtime:
        aname = 'mtime'
    etime = inode.etime
    if not aname and Iattrs.Etime & attributes and not etime:
        aname = 'etime'
    if aname:
        reason = f"No data to substantiate attribute '{aname}' on inode."
        raise error_to_raise( reason = reason )
    return inode.with_attributes(
        bytes_count = bytes_count,
        content_id = content_id,
        mimetype = mimetype, charset = charset,
        mtime = mtime, etime = etime )
