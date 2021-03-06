from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.data_sync import DataSync


class TestDataSync(object):
    def setup(self):
        self.sync = DataSync('source_dir', 'target_dir')

    @patch('kiwi.data_sync.Command.run')
    def test_sync_data(self, mock_command):
        self.sync.sync_data(['exclude_me'])
        mock_command.assert_called_once_with(
            [
                'rsync', '-a', '-H', '-X', '-A', '--one-file-system',
                '--exclude', '/exclude_me', 'source_dir', 'target_dir'
            ]
        )
