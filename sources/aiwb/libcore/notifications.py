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


''' Notifications queue and envents. '''


from . import __


class _NotificationBase(
    __.immut.DataclassObject
):
    ''' Common base for notifications. '''

    summary: str
    details: __.a.Any


class ApprisalNotification(
    _NotificationBase, class_decorators = ( __.standard_dataclass, )
):
    ''' Notification for recoverable error or similar condition. '''

    exception: BaseException = None


class ErrorNotification(
    _NotificationBase, class_decorators = ( __.standard_dataclass, )
):
    ''' Notification for non-recoverable error. '''

    error: Exception


class Queue(
    __.immut.DataclassObject
):
    ''' Queue for notifications to be consumed by application. '''

    # TODO: Hide queue attribute.
    queue: __.SimpleQueue = __.dataclass_declare(
        default_factory = __.SimpleQueue )

    # TODO? enqueue_admonition

    def enqueue_apprisal(
        self,
        summary: str, *,
        details: __.a.Any = None,
        exception: BaseException = None,
        inscribe_trace: bool = False,
        scribe: __.Scribe = None,
    ) -> __.a.Self:
        ''' Enqueues apprisal notification, optionally logging it. '''
        if scribe:
            scribe_args = { }
            if exception and inscribe_trace:
                scribe_args[ 'exc_info' ] = exception
            scribe.warn( summary, **scribe_args )
        return self._enqueue(
            ApprisalNotification(
                summary = summary, details = details, exception = exception ) )

    def enqueue_error(
        self,
        error: Exception,
        summary: str, *,
        append_reason: bool = True,
        details: __.a.Any = None,
        inscribe_trace: bool = False,
        scribe: __.Scribe = None,
    ) -> __.a.Self:
        ''' Enqueues error notification, optionally logging it. '''
        if append_reason: summary = f"{summary} Reason: {error}"
        if scribe:
            scribe_args = { }
            if inscribe_trace: scribe_args[ 'exc_info' ] = error
            scribe.error( summary, **scribe_args )
        return self._enqueue(
            ErrorNotification(
                error = error, summary = summary, details = details ) )

    # TODO: enqueue_future

    @__.exit_manager
    def enqueue_on_error(
        self,
        summary: str, *,
        append_reason: bool = True,
        details: __.a.Any = None,
        inscribe_trace: bool = False,
        scribe: __.Scribe = None
    ):
        ''' Produces context manager which enqueues errors. '''
        try: yield
        except Exception as exc:
            self.enqueue_error(
                exc, summary,
                append_reason = append_reason,
                details = details,
                inscribe_trace = inscribe_trace,
                scribe = scribe )

    def _enqueue( self, notification: _NotificationBase ) -> __.a.Self:
        self.queue.put( notification )
        return self
