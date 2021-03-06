from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.filesystem_builder import FileSystemBuilder


class TestFileSystemBuilder(object):
    @patch('kiwi.filesystem_builder.FileSystemSetup')
    @patch('platform.machine')
    def setup(self, mock_machine, mock_fs_setup):
        mock_machine.return_value = 'x86_64'
        self.loop_provider = mock.Mock()
        self.loop_provider.get_device = mock.Mock(
            return_value='/dev/loop1'
        )
        self.loop_provider.create = mock.Mock()

        self.filesystem = mock.Mock()
        self.filesystem.create_on_device = mock.Mock()
        self.filesystem.create_on_file = mock.Mock()
        self.filesystem.sync_data = mock.Mock()

        self.xml_state = mock.Mock()
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='ext3'
        )
        self.xml_state.get_image_version = mock.Mock(
            return_value='1.2.3'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='myimage'
        )
        self.xml_state.build_type.get_target_blocksize = mock.Mock(
            return_value=4096
        )

        self.fs_setup = mock.Mock()
        self.fs_setup.get_size_mbytes = mock.Mock(
            return_value=42
        )

    @raises(KiwiFileSystemSetupError)
    def test_create_unknown_filesystem(self):
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='super-fs'
        )
        fs = FileSystemBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        fs.create()

    @raises(KiwiFileSystemSetupError)
    def test_no_filesystem_configured(self):
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='pxe'
        )
        self.xml_state.build_type.get_filesystem = mock.Mock(
            return_value=None
        )
        FileSystemBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )

    @patch('kiwi.filesystem_builder.LoopDevice')
    @patch('kiwi.filesystem_builder.FileSystem')
    @patch('kiwi.filesystem_builder.FileSystemSetup')
    @patch('platform.machine')
    def test_create_on_loop(
        self, mock_machine, mock_fs_setup, mock_fs, mock_loop
    ):
        mock_machine.return_value = 'x86_64'
        mock_fs_setup.return_value = self.fs_setup
        mock_fs.return_value = self.filesystem
        mock_loop.return_value = self.loop_provider
        fs = FileSystemBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        fs.create()
        mock_loop.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.ext3', 42, 4096
        )
        self.loop_provider.create.assert_called_once_with()
        mock_fs.assert_called_once_with(
            'ext3', self.loop_provider, 'root_dir', None
        )
        self.filesystem.create_on_device.assert_called_once_with(None)
        self.filesystem.sync_data.assert_called_once_with(
            ['image', '.profile', '.kconfig', 'var/cache/kiwi']
        )

    @patch('kiwi.filesystem_builder.FileSystem')
    @patch('kiwi.filesystem_builder.DeviceProvider')
    @patch('platform.machine')
    def test_create_on_file(
        self, mock_machine, mock_provider, mock_fs
    ):
        mock_machine.return_value = 'x86_64'
        provider = mock.Mock()
        mock_provider.return_value = provider
        mock_fs.return_value = self.filesystem
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='squashfs'
        )
        fs = FileSystemBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        fs.create()
        mock_fs.assert_called_once_with(
            'squashfs', provider, 'root_dir', None
        )
        self.filesystem.create_on_file.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.squashfs', None
        )
