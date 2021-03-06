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
import collections
import os

# project
from command import Command

from exceptions import (
    KiwiContainerSetupError
)


class ContainerSetupBase(object):
    """
        Base class for setting up the root system to create
        a container image from for e.g docker. The methods here
        are generic to linux systems following the FHS standard
        and modern enough e.g based on systemd
    """
    def __init__(self, root_dir, custom_args=None):
        if not os.path.exists(root_dir):
            raise KiwiContainerSetupError(
                'Container root directory %s does not exist' % root_dir
            )
        self.root_dir = root_dir
        self.custom_args = {
            'container_name': 'systemContainer'
        }
        self.post_init(custom_args)

    def post_init(self, custom_args):
        pass

    def setup(self):
        """
            implement in specialized container setup class
        """
        raise NotImplementedError

    def create_fstab(self):
        """
            initialize an empty fstab file, mount processes in a
            container are controlled by the container infrastructure
        """
        with open(self.root_dir + '/etc/fstab', 'w') as fstab:
            pass

    def deactivate_bootloader_setup(self):
        """
            tell the system there is no bootloader configuration
            it needs to care for. A container does not boot
        """
        bootloader_setup = self.root_dir + '/etc/sysconfig/bootloader'
        if os.path.exists(bootloader_setup):
            self.__update_config(
                bootloader_setup,
                {
                    'LOADER_LOCATION': 'LOADER_LOCATION="none"',
                    'LOADER_TYPE': 'LOADER_TYPE="none"'
                }
            )

    def deactivate_root_filesystem_check(self):
        """
            the root filesystem of a container could be an overlay
            or a mapped device. In any case it should not be checked
            for consistency as this is should be done by the container
            infrastructure
        """
        boot_setup = self.root_dir + '/etc/sysconfig/boot'
        if os.path.exists(boot_setup):
            self.__update_config(
                boot_setup,
                {
                    'ROOTFS_BLKDEV': 'ROOTFS_BLKDEV="/dev/null"'
                }
            )

    def deactivate_systemd_service(self, name):
        """
            init systems among others also controls services which
            starts at boot time. A container does not really boot.
            Thus some services needs to be deactivated
        """
        service_file = self.root_dir + '/usr/lib/systemd/system/' + name
        if not os.path.exists(service_file):
            raise KiwiContainerSetupError(
                'Systemd service %s does not exist' % service_file
            )
        try:
            Command.run(
                ['ln', '-s', '-f', '/dev/null', service_file]
            )
        except Exception as e:
            raise KiwiContainerSetupError(
                'Failed to deactivate service %s: %s' %
                (name, format(e))
            )

    def setup_root_console(self):
        """
            /dev/console should be allowed to login by root
        """
        securetty = self.root_dir + '/etc/securetty'
        if not os.path.exists(securetty):
            with open(securetty, 'w') as empty_securetty:
                pass
        self.__update_config(
            securetty,
            {
                'console': 'console'
            }
        )

    def setup_static_device_nodes(self):
        """
            without subsystems like udev running in a container it is
            required to provide a set of device nodes to let the
            system in the container function correctly. This is
            done by syncing the host system nodes to the container.
            That this will also create device nodes which are not
            necessarily present in the container later is a know
            limitation of this method and considered harmless
        """
        try:
            Command.run(
                [
                    'rsync', '-zavx', '--devices', '--specials',
                    '/dev/', self.root_dir + '/dev/'
                ]
            )
        except Exception as e:
            raise KiwiContainerSetupError(
                'Failed to create static container nodes %s' % format(e)
            )

    def get_container_name(self):
        return self.custom_args['container_name']

    def __update_config(self, filename, update_record):
        data = []
        with open(filename, 'r') as config:
            data = config.read().rsplit('\n')

        sorted_record = collections.OrderedDict(
            sorted(update_record.items())
        )
        for current_value, new_value in sorted_record.iteritems():
            entry_found = False
            for index in range(0, len(data)):
                line = data[index]
                if line.startswith(current_value):
                    entry_found = True
                    data[index] = new_value
            if not entry_found:
                data.append(new_value)

        with open(filename, 'w') as config:
            config.write('%s\n' % '\n'.join(data))
