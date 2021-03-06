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
from boot_image_kiwi import BootImageKiwi

from exceptions import(
    KiwiBootImageSetupError
)


class BootImageTask(object):
    """
        BootImageTask factory
    """
    def __new__(
        self, initrd_type, xml_state, target_dir, root_dir=None
    ):
        if initrd_type == 'kiwi':
            return BootImageKiwi(xml_state, target_dir, root_dir)
        else:
            raise KiwiBootImageSetupError(
                'Support for %s boot image task not implemented' % initrd_type
            )
