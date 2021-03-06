from nose.tools import *
from mock import patch

import mock

import kiwi

import nose_helper

from collections import namedtuple

from kiwi.exceptions import *
from kiwi.pxe_builder import PxeBuilder


class TestPxeBuilder(object):
    @patch('kiwi.pxe_builder.FileSystemBuilder')
    @patch('kiwi.pxe_builder.BootImageTask')
    def setup(self, mock_boot, mock_filesystem):
        self.system_setup = mock.Mock()
        kiwi.pxe_builder.SystemSetup = mock.Mock(
            return_value=self.system_setup
        )
        self.boot_image_task = mock.MagicMock()
        self.boot_image_task.boot_root_directory = 'initrd_dir'
        mock_boot.return_value = self.boot_image_task
        self.filesystem = mock.MagicMock()
        self.filesystem.filename = 'myimage'
        mock_filesystem.return_value = self.filesystem
        self.xml_state = mock.MagicMock()
        kernel_type = namedtuple(
            'kernel', ['filename', 'version']
        )
        xen_type = namedtuple(
            'xen', ['filename', 'name']
        )
        self.kernel = mock.Mock()
        self.kernel.get_kernel = mock.Mock(
            return_value=kernel_type(filename='some-kernel', version='42')
        )
        self.kernel.get_xen_hypervisor = mock.Mock(
            return_value=xen_type(filename='hypervisor', name='xen.gz')
        )
        kiwi.pxe_builder.Kernel = mock.Mock(
            return_value=self.kernel
        )
        self.pxe = PxeBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        self.machine = mock.Mock()
        self.machine.get_domain = mock.Mock(
            return_value='dom0'
        )
        self.pxe.machine = self.machine
        self.pxe.image_name = 'myimage'

    @patch('kiwi.pxe_builder.Checksum')
    @patch('kiwi.pxe_builder.Compress')
    @patch('kiwi.logger.log.warning')
    def test_create(self, mock_log_warn, mock_compress, mock_checksum):
        compress = mock.Mock()
        mock_compress.return_value = compress
        checksum = mock.Mock()
        mock_checksum.return_value = checksum
        self.boot_image_task.required = mock.Mock(
            return_value=True
        )
        self.pxe.create()
        self.filesystem.create.assert_called_once_with()
        compress.xz.assert_called_once_with()
        checksum.md5.assert_called_once_with('myimage.md5')
        self.boot_image_task.prepare.assert_called_once_with()
        self.system_setup.export_modprobe_setup.assert_called_once_with(
            'initrd_dir'
        )
        self.boot_image_task.create_initrd.assert_called_once_with()
        # warning for not implemented pxedeploy handling
        assert mock_log_warn.called

    @patch('kiwi.pxe_builder.Checksum')
    @patch('kiwi.pxe_builder.Compress')
    @raises(KiwiPxeBootImageError)
    def test_create_no_kernel_found(self, mock_compress, mock_checksum):
        self.kernel.get_kernel.return_value = False
        self.pxe.create()

    @patch('kiwi.pxe_builder.Checksum')
    @patch('kiwi.pxe_builder.Compress')
    @raises(KiwiPxeBootImageError)
    def test_create_no_hypervisor_found(self, mock_compress, mock_checksum):
        self.kernel.get_xen_hypervisor.return_value = False
        self.pxe.create()
