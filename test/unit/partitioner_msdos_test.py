from nose.tools import *
from mock import patch

import mock

import nose_helper

from collections import namedtuple
from kiwi.partitioner_msdos import PartitionerMsDos
from kiwi.exceptions import *


class TestPartitionerMsDos(object):
    def setup(self):
        disk_provider = mock.Mock()
        disk_provider.get_device = mock.Mock(
            return_value='/dev/loop0'
        )
        self.partitioner = PartitionerMsDos(disk_provider)

    def test_get_id(self):
        assert self.partitioner.get_id() == 0

    @patch('kiwi.partitioner_msdos.Command.run')
    @patch('kiwi.partitioner_msdos.PartitionerMsDos.set_flag')
    @patch('kiwi.partitioner_msdos.NamedTemporaryFile')
    @patch('__builtin__.open')
    def test_create(self, mock_open, mock_temp, mock_flag, mock_command):
        mock_command.side_effect = Exception
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_temp.return_value = temp_type(
            name='tempfile'
        )
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.partitioner.create('name', 100, 't.linux', ['f.active'])

        file_mock.write.assert_called_once_with(
            'n\np\n1\n\n+100M\nw\nq\n'
        )
        mock_command.assert_called_once_with(
            ['bash', '-c', 'cat tempfile | fdisk /dev/loop0']
        )
        call = mock_flag.call_args_list[0]
        assert mock_flag.call_args_list[0] == \
            call(1, 't.linux')
        call = mock_flag.call_args_list[1]
        assert mock_flag.call_args_list[1] == \
            call(1, 'f.active')

    @patch('kiwi.partitioner_msdos.Command.run')
    @patch('kiwi.partitioner_msdos.PartitionerMsDos.set_flag')
    @patch('kiwi.partitioner_msdos.NamedTemporaryFile')
    @patch('__builtin__.open')
    def test_create_all_free(
        self, mock_open, mock_temp, mock_flag, mock_command
    ):
        mock_command.side_effect = Exception
        temp_type = namedtuple(
            'temp_type', ['name']
        )
        mock_temp.return_value = temp_type(
            name='tempfile'
        )
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.partitioner.create('name', 'all_free', 't.linux')

        file_mock.write.assert_called_once_with(
            'n\np\n1\n\n\nw\nq\n'
        )

    @raises(KiwiPartitionerMsDosFlagError)
    def test_set_flag_invalid(self):
        self.partitioner.set_flag(1, 'foo')

    @patch('kiwi.partitioner_msdos.Command.run')
    def test_set_flag(self, mock_command):
        self.partitioner.set_flag(1, 't.linux')
        mock_command.assert_called_once_with(
            ['sfdisk', '-c', '/dev/loop0', '1', '83']
        )

    @patch('kiwi.partitioner_msdos.Command.run')
    def test_set_active(self, mock_command):
        self.partitioner.set_flag(1, 'f.active')
        mock_command.assert_called_once_with(
            ['sfdisk', '--activate=1', '/dev/loop0']
        )

    @patch('kiwi.logger.log.warning')
    def test_set_flag_ignored(self, mock_warn):
        self.partitioner.set_flag(1, 't.csm')
        assert mock_warn.called
