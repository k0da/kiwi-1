# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
# project
from logger import log
from collections import namedtuple

from exceptions import (
    KiwiCommandError
)


class CommandProcess(object):
    """
        Implements processing of non blocking Command calls
        with and without progress information
    """
    def __init__(self, command, log_topic='system'):
        self.command = CommandIterator(command)
        self.log_topic = log_topic
        self.items_processed = 0

    def poll(self):
        try:
            while True:
                line = self.command.next()
                if line:
                    log.debug('%s: %s', self.log_topic, line)
        except StopIteration:
            if self.command.get_error_code() != 0:
                raise KiwiCommandError(
                    self.command.get_error_output()
                )

    def poll_show_progress(self, items_to_complete, match_method):
        self.__init_progress()
        try:
            while True:
                line = self.command.next()
                if line:
                    log.debug('%s: %s', self.log_topic, line)
                    self.__update_progress(
                        match_method, items_to_complete, line
                    )
        except StopIteration:
            self.__stop_progress()
            if self.command.get_error_code() != 0:
                raise KiwiCommandError(
                    self.command.get_error_output()
                )

    def poll_and_watch(self):
        log.info(self.log_topic)
        log.debug('--------------out start-------------')
        try:
            while True:
                line = self.command.next()
                if line:
                    log.debug(line)
        except StopIteration:
            log.debug('--------------out stop--------------')

        error_code = self.command.get_error_code()
        error_output = self.command.get_error_output()
        result = namedtuple(
            'result', ['stderr', 'returncode']
        )
        if error_output:
            log.debug('--------------err start-------------')
            log.debug(error_output)
            log.debug('--------------err stop--------------')
        return result(
            stderr=error_output, returncode=error_code
        )

    def create_match_method(self, method):
        """
            create a matcher method with the following interface
            f(item_to_match, data)
        """
        def create_method(item_to_match, data):
            return method(item_to_match, data)
        return create_method

    def __init_progress(self):
        log.progress(
            0, 100, '[ INFO    ]: Processing'
        )

    def __stop_progress(self):
        log.progress(
            100, 100, '[ INFO    ]: Processing'
        )

    def __update_progress(
        self, match_method, items_to_complete, command_output
    ):
        items_count = len(items_to_complete)
        for item in items_to_complete:
            if match_method(item, command_output):
                self.items_processed += 1
                if self.items_processed <= items_count:
                    log.progress(
                        self.items_processed, items_count,
                        '[ INFO    ]: Processing'
                    )

    def __del__(self):
        if self.command and self.command.get_error_code() is None:
            log.info(
                'Terminating subprocess %d', self.command.get_pid()
            )
            self.command.kill()


class CommandIterator(object):
    def __init__(self, command):
        self.command = command
        self.command_error_output = ''
        self.command_output_line = ''
        self.output_eof_reached = False
        self.errors_eof_reached = False

    def next(self):
        line_read = None
        if self.command.process.poll() is not None:
            if self.output_eof_reached and self.errors_eof_reached:
                raise StopIteration()

        if self.command.output_available():
            byte_read = self.command.output.read(1)
            if not byte_read:
                self.output_eof_reached = True
            elif byte_read == '\n':
                line_read = self.command_output_line
                self.command_output_line = ''
            else:
                self.command_output_line += byte_read

        if self.command.error_available():
            byte_read = self.command.error.read(1)
            if not byte_read:
                self.errors_eof_reached = True
            else:
                self.command_error_output += byte_read

        return line_read

    def get_error_output(self):
        return self.command_error_output

    def get_error_code(self):
        return self.command.process.returncode

    def get_pid(self):
        return self.command.process.pid

    def kill(self):
        self.command.process.kill()

    def __iter__(self):
        return self
