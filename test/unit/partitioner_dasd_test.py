from nose.tools import *
from mock import patch

import mock

import nose_helper

from collections import namedtuple
from kiwi.partitioner_dasd import PartitionerDasd
from kiwi.exceptions import *


class TestPartitionerDasd(object):
    @patch('kiwi.partitioner_dasd.Command.run')
    @patch('kiwi.partitioner_dasd.NamedTemporaryFile')
    @patch('__builtin__.open')
    def setup(self, mock_open, mock_temp, mock_command):
        self.tempfile = mock.Mock()
        self.tempfile.name = 'tempfile'
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        mock_temp.return_value = self.tempfile
        mock_open.return_value = self.context_manager_mock

        disk_provider = mock.Mock()
        disk_provider.get_device = mock.Mock(
            return_value='/dev/loop0'
        )

        self.partitioner = PartitionerDasd(disk_provider)

    def test_get_id(self):
        assert self.partitioner.get_id() == 0

    @patch('kiwi.partitioner_dasd.Command.run')
    @patch('kiwi.partitioner_dasd.NamedTemporaryFile')
    @patch('__builtin__.open')
    def test_create(self, mock_open, mock_temp, mock_command):
        mock_temp.return_value = self.tempfile
        mock_open.return_value = self.context_manager_mock

        self.partitioner.create('name', 100, 't.linux', ['f.active'])

        self.file_mock.write.assert_called_once_with(
            'n\np\n\n+100M\nw\nq\n'
        )
        mock_command.assert_called_once_with(
            ['bash', '-c', 'cat tempfile | fdasd -f /dev/loop0']
        )

    @patch('kiwi.partitioner_dasd.Command.run')
    @patch('kiwi.partitioner_dasd.NamedTemporaryFile')
    @patch('__builtin__.open')
    def test_create_all_free(
        self, mock_open, mock_temp, mock_command
    ):
        mock_temp.return_value = self.tempfile
        mock_open.return_value = self.context_manager_mock

        self.partitioner.create('name', 'all_free', 't.linux')

        self.file_mock.write.assert_called_once_with(
            'n\np\n\n\nw\nq\n'
        )

    def test_set_flag(self):
        # This is a noop for fdasd, just does nothing but has to
        # exist to complete the partitioner interface
        self.partitioner.set_flag('id', 'flag_name')
