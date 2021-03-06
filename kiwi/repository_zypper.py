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
import os
from ConfigParser import ConfigParser
from tempfile import NamedTemporaryFile

# project
from command import Command
from repository_base import RepositoryBase
from path import Path

from exceptions import (
    KiwiRepoTypeUnknown
)


class RepositoryZypper(RepositoryBase):
    """
        Implements repo handling for zypper package manager
    """
    def post_init(self, custom_args=None):
        self.custom_args = custom_args
        if not custom_args:
            self.custom_args = []

        self.repo_names = []

        # zypper support by default point all actions into the root
        # directory of the image system. This information is passed
        # as arguments to zypper and adapted if the call runs as
        # chrooted operation. Therefore the use of the shared location
        # via RootBind::mount_shared_directory is optional but
        # recommended to make use of the repo cache
        manager_base = self.root_dir + self.shared_location

        self.shared_zypper_dir = {
            'pkg-cache-dir': manager_base + '/packages',
            'reposd-dir': manager_base + '/zypper/repos',
            'solv-cache-dir': manager_base + '/zypper/solv',
            'raw-cache-dir': manager_base + '/zypper/raw',
            'cache-dir': manager_base + '/zypper'
        }

        self.runtime_zypper_config_file = NamedTemporaryFile(
            dir=self.root_dir
        )
        self.runtime_zypp_config_file = NamedTemporaryFile(
            dir=self.root_dir
        )

        self.zypper_args = [
            '--non-interactive', '--no-gpg-checks',
            '--pkg-cache-dir', self.shared_zypper_dir['pkg-cache-dir'],
            '--reposd-dir', self.shared_zypper_dir['reposd-dir'],
            '--solv-cache-dir', self.shared_zypper_dir['solv-cache-dir'],
            '--cache-dir', self.shared_zypper_dir['cache-dir'],
            '--raw-cache-dir', self.shared_zypper_dir['raw-cache-dir'],
            '--config', self.runtime_zypper_config_file.name
        ] + self.custom_args

        self.command_env = self.__create_zypper_runtime_environment()

        # config file parameters for zypper tool
        self.runtime_zypper_config = ConfigParser()
        self.runtime_zypper_config.add_section('main')

        # config file parameters for libzypp library
        self.runtime_zypp_config = ConfigParser()
        self.runtime_zypp_config.add_section('main')
        self.runtime_zypp_config.set(
            'main', 'cachedir', self.shared_zypper_dir['cache-dir']
        )
        self.runtime_zypp_config.set(
            'main', 'metadatadir', self.shared_zypper_dir['raw-cache-dir']
        )
        self.runtime_zypp_config.set(
            'main', 'solvfilesdir', self.shared_zypper_dir['solv-cache-dir']
        )
        self.runtime_zypp_config.set(
            'main', 'packagesdir', self.shared_zypper_dir['pkg-cache-dir']
        )

        self.__write_runtime_config()

    def runtime_config(self):
        return {
            'zypper_args': self.zypper_args,
            'command_env': self.command_env
        }

    def add_repo(self, name, uri, repo_type='rpm-md', prio=None):
        repo_file = self.shared_zypper_dir['reposd-dir'] + '/' + name + '.repo'
        self.repo_names.append(name + '.repo')
        if 'iso-mount' in uri:
            # iso mount point is a tmpdir, thus different each time we build
            Path.wipe(repo_file)
        if not os.path.exists(repo_file):
            Command.run(
                ['zypper'] + self.zypper_args + [
                    '--root', self.root_dir,
                    'addrepo', '-f',
                    '--type', self.__translate_repo_type(repo_type),
                    '--keep-packages',
                    uri,
                    name
                ],
                self.command_env
            )
            if prio:
                Command.run(
                    ['zypper'] + self.zypper_args + [
                        '--root', self.root_dir,
                        'modifyrepo', '-p', format(prio), name
                    ],
                    self.command_env
                )

    def delete_repo(self, name):
        Command.run(
            ['zypper'] + self.zypper_args + [
                '--root', self.root_dir, 'removerepo', name
            ],
            self.command_env
        )

    def delete_all_repos(self):
        Path.wipe(self.shared_zypper_dir['reposd-dir'])
        Path.create(self.shared_zypper_dir['reposd-dir'])

    def cleanup_unused_repos(self):
        # zypper creates a system solvable which is unwanted for the
        # purpose of building images. In addition zypper fails with
        # an error message 'Failed to cache rpm database' if such a
        # system solvable exists and a new root system is created
        solv_dir = self.shared_zypper_dir['solv-cache-dir']
        Path.wipe(solv_dir + '/@System')

        # repository configurations which are not used for this build
        # must be removed otherwise they are taken into account for
        # the package installations
        repos_dir = self.shared_zypper_dir['reposd-dir']
        for elements in os.walk(repos_dir):
            for repo_file in list(elements[2]):
                if repo_file not in self.repo_names:
                    Path.wipe(repos_dir + '/' + repo_file)
            break

    def __create_zypper_runtime_environment(self):
        for zypper_dir in self.shared_zypper_dir.values():
            Path.create(zypper_dir)
        return dict(
            os.environ,
            LANG='C',
            ZYPP_CONF=self.runtime_zypp_config_file.name
        )

    def __write_runtime_config(self):
        with open(self.runtime_zypper_config_file.name, 'w') as config:
            self.runtime_zypper_config.write(config)
        with open(self.runtime_zypp_config_file.name, 'w') as config:
            self.runtime_zypp_config.write(config)

    def __translate_repo_type(self, repo_type):
        """
            Translate kiwi supported common repo type names from the schema
            into the name the zyper package manager understands
        """
        zypper_type_for = {
            'rpm-md': 'YUM',
            'rpm-dir': 'Plaindir',
            'yast2': 'YaST'
        }
        try:
            return zypper_type_for[repo_type]
        except Exception:
            raise KiwiRepoTypeUnknown(
                'Unsupported zypper repo type: %s' % repo_type
            )
