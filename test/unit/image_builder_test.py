from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.image_builder import ImageBuilder


class TestImageBuilder(object):
    @patch('kiwi.image_builder.FileSystemBuilder')
    def test_filesystem_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='ext4'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir'
        )

    @patch('kiwi.image_builder.DiskBuilder')
    def test_disk_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='vmx'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir'
        )

    @patch('kiwi.image_builder.LiveImageBuilder')
    def test_live_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='iso'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir'
        )

    @patch('kiwi.image_builder.PxeBuilder')
    def test_pxe_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='pxe'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir'
        )

    @patch('kiwi.image_builder.ArchiveBuilder')
    def test_archive_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='tbz'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir'
        )

    @patch('kiwi.image_builder.ContainerBuilder')
    def test_container_builder(self, mock_builder):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='docker'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
        mock_builder.assert_called_once_with(
            xml_state, 'target_dir', 'root_dir'
        )

    @raises(KiwiRequestedTypeError)
    def test_unsupported_build_type(self):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='bogus'
        )
        ImageBuilder(xml_state, 'target_dir', 'root_dir')
