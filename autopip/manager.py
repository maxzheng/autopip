from configparser import RawConfigParser
from collections import defaultdict
from functools import lru_cache
import json
from logging import info, error, debug
import os
from pathlib import Path, PurePath
import pkg_resources
import re
import shutil
from subprocess import CalledProcessError, STDOUT
import sys
from time import time, sleep
import urllib.request
import urllib.error

from autopip import crontab, exceptions
from autopip.constants import UpdateFreq, PYTHON_VERSION
from autopip.utils import run, sorted_versions


class AppsManager:
    """ Manages apps """

    def __init__(self, debug=False):
        #: Turn on debug mode
        self.debug = debug

        #: An instance of :cls:`AppsPath`
        self.paths = AppsPath()

        # PyPI url
        self._index_url = None

        # PyPI auth. Tuple of user and password.
        self._index_auth = None

    def install(self, apps, update=None, python_version=None, wait=False):
        """
        Install the given apps

        :param list[str] apps: List of apps to install
        :param UpdateFreq|None update: How often to update
        :param str python_version: Python version to run the app
        :param bool wait: Wait for a new version to be published and then install it.
        """
        self._set_index()

        autopip_path = shutil.which('autopip')
        if (self.paths.is_user and sys.stdout.isatty() and not list(self.apps) and autopip_path
                and autopip_path.startswith(str(self.paths.SYSTEM_SYMLINK_ROOT))):
            info('# Based on permission, this will install to your user home instead of %s',
                 self.paths.SYSTEM_SYMLINK_ROOT)
            info('  To install for everyone, cancel using CTRL+C and then re-run using sudo.')

        failed_apps = []
        printed_wait = False

        for name in apps:
            try:
                if isinstance(name, tuple):  # From app.group_specs()
                    name, update = name
                    if update:
                        update = UpdateFreq.from_name(update)

                app_spec = next(iter(pkg_resources.parse_requirements(name)))
                app, updated = self._install_app(app_spec, update=update, python_version=python_version, wait=wait)

                if updated:
                    printed_wait = False
                    group_specs = app.group_specs()
                    if group_specs:
                        info('This app has defined "autopip" entry points to install: %s', ' '.join(
                             s[0] for s in group_specs))
                        apps.extend([s for s in group_specs if s not in apps])

                elif wait:
                    goback = '\033[1A' if printed_wait else ''
                    print(f'{goback}Waiting for new version of {name} to be published...'.ljust(80))
                    sleep(60)
                    apps.append(name)
                    printed_wait = True

            except Exception as e:
                error(f'! {e}', exc_info=self.debug)
                failed_apps.append(name)
                printed_wait = False

        if failed_apps:
            raise exceptions.FailedAction()

    def _install_app(self, app_spec, update=None, python_version=None, wait=False):
        """ Install the given app """
        app = App(app_spec.name, self.paths, debug=self.debug)
        updated = False

        # Skip update if install was done within the update frequency when run from cron
        if (sys.stdout.isatty() or not app.is_installed or wait
                or update and app.path.stat().st_mtime + update.seconds < time()):
            if app.is_installed:
                app.path.touch()

            version = self._app_version(app_spec)

            if not wait or version != app.current_version:
                updated = app.install(version, app_spec, update=update, python_version=python_version)

        else:
            debug(f'{app.name} does not need to be updated yet.')

        return app, updated

    def _app_version(self, app_spec):
        """ Get app version from PyPI """
        pkg_index_url = self._index_url + app_spec.name + '/'

        try:
            if self._index_auth:
                password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                password_mgr.add_password(None, self._index_url, self._index_auth[0], self._index_auth[1])
                handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
                opener = urllib.request.build_opener(handler)

            else:
                opener = urllib.request.build_opener()

            with opener.open(str(pkg_index_url), timeout=10) as fp:
                version_links = fp.read().decode('utf-8')

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NameError(f'{app_spec.name} does not exist on {self._index_url}')
            else:
                raise Exception(f'Failed to read from {pkg_index_url}: {e}')

        version_re = re.compile(app_spec.name + r'-(\d+\.\d+\.\d+(?:\.\w+\d+)?)\.')
        versions = []
        matched_versions = []

        for line in version_links.split('\n'):
            match = version_re.search(line)
            if match:
                if match.group(1) in app_spec:
                    matched_versions.append(match.group(1))
                else:
                    versions.append(match.group(1))

        if not matched_versions:
            if versions:
                raise ValueError(f'No app version matching {app_spec} \nAvailable versions: '
                                 + ', '.join(sorted_versions(versions)))
            else:
                raise ValueError(f'No app version found in {pkg_index_url}')

        return sorted_versions(matched_versions)[-1]

    def _set_index(self):
        """ Set PyPI url and auth """
        if not self._index_url:
            for conf_file in ['~/.config/pip/pip.conf', '~/.pip/pip.conf', '/etc/pip.conf']:
                self._index_url, self._index_auth = self._parse_pip_conf_for_index(conf_file)
                if self._index_url:
                    break

            if self._index_url and not self._index_auth:
                self._index_auth = self._parse_netrc_credential_for(self._index_url)

            if not self._index_url:  # No need to check for login/password for this as everything is public
                self._index_url = 'https://pypi.org/simple/'

    @staticmethod
    def _parse_pip_conf_for_index(conf_file):
        """
        Parse the given pip.conf file for index-url

        :param str pip_conf_path: Path to pip.conf file
        :return: Tuple of index_url and another tuple of user and password (or None)
        """
        index_url = index_auth = None

        pip_conf = Path(conf_file).expanduser()
        if pip_conf.exists():
            try:
                parser = RawConfigParser()
                parser.read(pip_conf)

                index_url = parser.get('global', 'index-url')

                auth_re = re.compile('//([^:]+)(?::([^@]+))?@')
                match = auth_re.search(index_url)
                if match:
                    index_auth = match.groups()
                    index_url = auth_re.sub('//', index_url)

                if not index_url.endswith('/'):
                    index_url += '/'

            except Exception:
                pass

        return index_url, index_auth

    @staticmethod
    def _parse_netrc_credential_for(index_url, netrc_file='~/.netrc'):
        """
        Parse .netrc for login/password for the given index_url

        :param str index_url: Machine URL to find credential for
        :return: Tuple of login and password or None
        """
        netrc = Path(netrc_file).expanduser()
        if netrc.exists():
            machine = login = password = None
            for line in netrc.open():
                try:
                    _, machine, _, login, _, password = line.strip().split()

                except Exception:
                    name, value = line.strip().split()
                    if name == 'machine':
                        machine = value
                    elif name == 'login':
                        login = value
                    elif name == 'password':
                        password = value

                if password:
                    if machine in index_url:
                        return (login, password)
                    machine = login = password = None

    @property
    def apps(self):
        """ Iterator for installed apps """
        for app_path in sorted(self.paths.install_root.iterdir()):
            if app_path in {self.paths.symlink_root, self.paths.log_root}:
                continue

            app = App(app_path.name, self.paths)

            if app.is_installed:
                yield app

    def list(self, name_filter=False, scripts=False):
        """
        List installed apps

        :param str name_filter: Filter apps by name
        :param bool scripts: Show scripts
        """
        app_info = []
        info_lens = defaultdict(int)

        for app in self.apps:
            if name_filter and name_filter not in app.name:
                continue

            app_path = str(app.current_path.resolve())

            if app.settings().get('update'):
                update = f"[updates {app.settings()['update']}]"
            else:
                update = ''

            app_info.append((app.name, app.current_version, app_path, update))

            if scripts:
                hide_path = False
                for script in sorted(app.scripts()):
                    script_symlink = self.paths.symlink_root / script
                    if script_symlink.exists() and str(script_symlink.resolve()).startswith(app_path):
                        script_path = str(script_symlink)
                        if hide_path:
                            script_path = script_path.replace(str(script_symlink.parent) + '/',
                                                              ' ' * len(str(script_symlink.parent)) + ' ')
                        app_info.append(('', '', script_path, ''))
                        hide_path = True

        if app_info:
            # Figure out max length of each column
            for info_part in app_info:
                for i, value in enumerate(info_part):
                    info_lens[i] = len(value) if len(value) > info_lens[i] else info_lens[i]

            # Print table
            table_style = '  '.join('{{:{}}}'.format(l) if l else '{}' for l in info_lens.values())
            for info_part in app_info:
                info(table_style.format(*info_part))

        elif name_filter:
            info(f'No apps matching "{name_filter}"')

        else:
            info('No apps are installed yet.')

            autopip_path = shutil.which('autopip')
            if (self.paths.is_user and sys.stdout.isatty() and autopip_path
                    and autopip_path.startswith(str(self.paths.SYSTEM_SYMLINK_ROOT))):
                info('To see apps installed in %s, re-run using sudo.', self.paths.SYSTEM_INSTALL_ROOT)

    def uninstall(self, apps):
        """ Uninstall apps """
        for name in apps:
            if name == 'autopip' and len(list(self.apps)) > 1:
                if apps[-1] == 'autopip':
                    error('! autopip can not be uninstalled until other apps are uninstalled: %s', ' '.join(
                        a.name for a in self.apps if a.name != 'autopip'))
                else:  # Try again after uninstall the other apps
                    apps.append('autopip')

                continue

            app = App(name, self.paths)
            if app.is_installed:
                group_specs = app.group_specs(name_only=True)
                app.uninstall()

                if group_specs:
                    info('This app has defined "autopip" entry points to uninstall: %s', ' '.join(group_specs))
                    apps.extend(group_specs)

            else:
                info(f'{name} is not installed')

        if not list(self.apps):
            try:
                crontab.remove('autopip')
            except Exception as e:
                debug('Could not remove crontab for autopip: %s', e)

    def update(self, apps=None, wait=False):
        """
        Update installed apps

        :param list apps: List of apps to update. Defaults to all.
        :param bool wait: Wait for a new version to be published and then install it.
        """
        app_instances = list([a for a in self.apps if a.name in apps] if apps else self.apps)

        if app_instances:
            app_specs = []
            for app in app_instances:
                settings = app.settings()
                if settings.get('update'):
                    app_specs.append((settings['app_spec'], settings['update']))
                elif sys.stdout.isatty() or wait:
                    app_specs.append((settings.get('app_spec', app.name), None))

            if app_specs:
                self.install(app_specs, wait=wait)

            elif not apps:
                try:
                    crontab.remove('autopip')
                except Exception as e:
                    debug('Could not remove crontab for autopip: %s', e)

        elif list(self.apps):
            info('No apps found matching: %s', ', '.join(apps))
            info('Available apps: %s', ', '.join([a.name for a in self.apps]))

        else:
            info('No apps installed yet.')


class App:
    """ Represents an app that may or may not be installed on disk """

    #: Prefixes of scripts to skip when creating symlinks
    SKIP_SCRIPT_PREFIXES = {'activate', 'pip', 'easy_install', 'python', 'wheel'}

    def __init__(self, name, paths, debug=False):
        """
        :param str name: Name of the app
        :param AppsPath paths: Path paths
        :param bool debug: Turn on debug mode
        """
        self.name = name
        self.paths = paths
        self.debug = debug

        #: Path to install all app versions
        self.path = self.paths.install_root / name

        #: Symlink to current version
        self._current_symlink = self.path / 'current'

        # Unique crontab name to to easily add and remove from crontab
        self._crontab_id = rf'autopip install "{self.name}[^a-z]*"'

    def __repr__(self):
        return f"App('{self.name}')"

    @property
    def is_installed(self):
        """ Is the app installed? """
        return self._current_symlink.exists()

    @property
    def current_path(self):
        """ Path to currently installed app """
        return self._current_symlink if self.is_installed else None

    @property
    def current_version(self):
        """ Currently installed version """
        if self.current_path:
            return self.current_path.resolve().name

    def install(self, version, app_spec, update=None, python_version=None):
        """
        Install the version of the app if it is not already installed

        :param str version: Version of the app to install
        :param pkg_resources.Requirement app_spec: App version requirement from user
        :param UpdateFreq|None update: How often to update. Choose from hourly, daily, weekly, monthly
        :param str python_version: Python version to run app
        :return: True if install or update happened, otherwise False when nothing happened (already installed / non-tty)
        """
        version_path = self.path / version
        prev_version_path = self.current_path and self.current_path.resolve()
        important_paths = [version_path, prev_version_path, self._current_symlink]

        if self.settings():
            if not python_version:
                python_version = self.settings().get('python_version')

            if not update:
                update = self.settings().get('update') and UpdateFreq.from_name(self.settings()['update'])

        if not python_version:
            python_version = PYTHON_VERSION

        if version_path.exists():
            if self.current_version == version:
                # Skip printing / ensuring symlinks / cronjob when running from cron
                if not sys.stdout.isatty():
                    return False

                pinned = str(app_spec).lstrip(self.name)
                pin_info = f' [per spec: {pinned}]' if pinned else ''

                info(f'{self.name} is up-to-date{pin_info}')

            else:
                info(f'{self.name} {version} was previously installed and will be set as the current version')

        else:
            if not shutil.which('python' + python_version):
                error(f'! python{python_version} does not exist. '
                      'Please install it first, or ensure its path is in PATH.')
                sys.exit(1)

            if python_version.startswith('2'):
                venv = f'virtualenv --python=python{python_version}'
            else:
                venv = f'python{python_version} -m venv'

            old_venv_dir = None
            old_path = None
            no_compile = '--no-compile ' if os.getuid() else ''

            info(f'Installing {self.name} to {version_path}')

            os.environ.pop('PYTHONPATH', None)
            if 'VIRTUAL_ENV' in os.environ:
                old_venv_dir = os.environ.pop('VIRTUAL_ENV')
                old_path = os.environ['PATH']
                os.environ['PATH'] = os.pathsep.join([p for p in os.environ['PATH'].split(os.pathsep)
                                                      if os.path.exists(p) and not p.startswith(old_venv_dir)])

            try:
                run(f"""set -e
                    {venv} {version_path}
                    source {version_path / 'bin' / 'activate'}
                    pip install --upgrade pip wheel
                    pip install {no_compile}{self.name}=={version}
                    """, executable='/bin/bash', stderr=STDOUT, shell=True)

            except BaseException as e:
                shutil.rmtree(version_path, ignore_errors=True)

                if isinstance(e, CalledProcessError):
                    if e.output:
                        output = e.output.decode('utf-8')

                        if not python_version.startswith('2'):
                            python2 = shutil.which('python2') or shutil.which('python2.7')
                            if python2:
                                py2_version = Path(python2).name.lstrip('python')
                                if 'is a builtin module since Python 3' in output:
                                    info(f'Failed to install using Python {python_version} venv, '
                                         f'let\'s try using Python {py2_version} virtualenv.')
                                    return self.install(version, app_spec, update=update, python_version=py2_version)

                        info(re.sub(r'(https?://)[^/]+:[^/]+@', r'\1<xxx>:<xxx>@', output))

                    error(f'! Failed to install using Python {python_version}.'
                          ' If this app requires a different Python version, please specify it using --python option.')

                raise

            finally:
                if old_venv_dir:
                    os.environ['VIRTUAL_ENV'] = old_venv_dir
                    os.environ['PATH'] = old_path

            try:
                shutil.rmtree(version_path / 'share' / 'python-wheels', ignore_errors=True)
                run(f"""set -e
                    source {version_path / 'bin' / 'activate'}
                    pip uninstall --yes pip
                    """, executable='/bin/bash', stderr=STDOUT, shell=True)

            except Exception as e:
                debug('Could not remove unnecessary packages/files: %s', e)

        # Update current symlink
        if not self.current_path or self.current_path.resolve() != version_path:
            atomic_symlink = self.path / f'atomic_symlink_for_{self.name}'
            atomic_symlink.symlink_to(version_path)
            atomic_symlink.replace(self._current_symlink)

            # Remove older versions
            for path in [p for p in self.path.iterdir() if p not in important_paths]:
                shutil.rmtree(path, ignore_errors=True)

        current_scripts = self.scripts()

        if not (current_scripts or self.group_specs()):
            self.uninstall()
            raise exceptions.InvalidAction(
                'Odd, there are no scripts included in the app, so there is no point installing it.\n'
                '  autopip is for installing apps with scripts. To install libraries, please use pip.\n'
                '  If you are the app owner, make sure to setup entry_points in setup.py.\n'
                '  See http://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation')

        self.settings(app_spec=str(app_spec), python_version=python_version)

        # Install cronjobs
        if 'update' not in sys.argv:
            pinning = '==' in str(app_spec) and not str(app_spec).endswith('*')
            if pinning and (self.settings().get('update') or update):
                info('Auto-update will be disabled since we are pinning to a specific version.')
                info('To enable, re-run without pinning to specific version with --update option')

                if self.settings().get('update'):
                    self.settings(update=None)
                    try:
                        crontab.remove(self._crontab_id)
                    except exceptions.MissingError as e:
                        debug('Could not remove crontab for %s: %s', self._crontab_id, e)

            elif update:
                try:
                    autopip_path = shutil.which('autopip')
                    if not autopip_path:
                        raise exceptions.MissingError(
                            'autopip is not available. Please make sure its bin folder is in PATH env var')

                    # Migrate old crontabs
                    try:
                        old_crons = [c for c in crontab.list().split('\n') if c and 'autopip update' not in c]
                        if old_crons:
                            cron_re = re.compile('autopip install "(.+)"')
                            for cron in old_crons:
                                match = cron_re.search(cron)
                                if match:
                                    old_app_spec = next(iter(pkg_resources.parse_requirements(match.group(1))))
                                    old_app = App(old_app_spec.name, self.paths)
                                    if old_app.is_installed:
                                        old_app.settings(app_spec=str(old_app_spec))
                            crontab.remove('autopip')

                    except Exception as e:
                        debug('Could not migrate old crontabs: %s', e)

                    crontab.add(f'{autopip_path} update '
                                f'2>&1 >> {self.paths.log_root / "cron.log"}', cmd_id='autopip update')
                    info(update.name.title() + ' auto-update enabled via cron service')

                    self.settings(update=update.name.lower())

                except Exception as e:
                    error('! Auto-update was not enabled because: %s', e, exc_info=self.debug)

        # Install script symlinks
        prev_scripts = self.scripts(prev_version_path) if prev_version_path else set()
        old_scripts = prev_scripts - current_scripts

        printed_updating = False

        for script in sorted(current_scripts):
            script_symlink = self.paths.symlink_root / script
            script_path = self.current_path / 'bin' / script

            if script_symlink.resolve() == script_path.resolve():
                continue

            if not printed_updating:
                info('Updating script symlinks in {}'.format(self.paths.symlink_root))
                printed_updating = True

            if script_symlink.exists():
                if self.paths.covers(script_symlink) or self.name == 'autopip':
                    atomic_symlink = self.paths.symlink_root / f'atomic_symlink_for_{self.name}'
                    atomic_symlink.symlink_to(script_path)
                    atomic_symlink.replace(script_symlink)
                    info('* {} (updated)'.format(script_symlink.name))

                else:
                    info('! {} (can not change / not managed by autopip)'.format(script_symlink.name))

            else:
                script_symlink.symlink_to(script_path)
                info('+ ' + str(script_symlink.name))

        for script in sorted(old_scripts):
            script_symlink = self.paths.symlink_root / script
            if script_symlink.exists():
                script_symlink.unlink()
                info('- '.format(script_symlink.name))

        if not printed_updating and sys.stdout.isatty() and current_scripts and 'update' not in sys.argv:
            info('Scripts are in {}: {}'.format(self.paths.symlink_root, ', '.join(sorted(current_scripts))))

        # Remove pyc for non-root installs for all versions, not just current.
        if os.getuid():
            try:
                run(f'find {self.path} -name *.pyc | xargs rm', executable='/bin/bash', stderr=STDOUT, shell=True)
            except Exception as e:
                debug('Could not remove *.pyc files: %s', e)

        return True

    def settings(self, **new_settings):
        """ Get or set settings """
        current_settings = {}

        if self.path.exists():
            settings_file = self.path / 'settings.json'
            if settings_file.exists():
                try:
                    current_settings.update(json.load(settings_file.open()))
                except Exception as e:
                    debug('Could not load app settings: %s', e)

            if new_settings:
                current_settings.update(new_settings)
                with settings_file.open('w') as fh:
                    json.dump(current_settings, fh)

        return current_settings

    def scripts(self, path=None):
        """ Set of scripts for the given app path (defaults to current). """
        dist = self._pkg_info(path=path)
        return dist and set(dist['scripts']) or set()

    def group_specs(self, path=None, name_only=False):
        """ List of app specs from this app's "autopip" entry points for the given app path (defaults to current)"""
        app_specs = []
        dist = self._pkg_info(path=path)

        if dist:
            for app, version, update in dist.get('group_specs', []):
                if name_only:
                    app_specs.append(app)

                elif version == 'latest':
                    app_specs.append((app, update or UpdateFreq.DEFAULT.name.lower()))

                elif len(version.split('.')) < 3:
                    app_specs.append((f'{app}=={version}.*', update or UpdateFreq.DEFAULT.name.lower()))

                else:  # Specific version without auto-update
                    app_specs.append((f'{app}=={version}', None))

        return app_specs

    @lru_cache()
    def _pkg_info(self, path=None):
        """ Get scripts and entry points from the app """
        if not path:
            if not self.current_path:
                return

            path = self.current_path

        inspect_py = Path(__file__).parent / 'inspect_app.py'

        try:
            info = run(f"""set -e
                source {path / 'bin/activate'}
                python {inspect_py} {self.name}
                """, executable='/bin/bash', stderr=STDOUT, shell=True)
            return json.loads(info)

        except Exception as e:
            debug('! Can not get package distribution info because: %s', e)

    def uninstall(self):
        """ Uninstall app """
        info('Uninstalling %s', self.name)

        try:
            crontab.remove(self._crontab_id)
        except exceptions.MissingError as e:
            debug('Could not remove crontab for %s: %s', self._crontab_id, e)

        for script in self.scripts():
            script_symlink = self.paths.symlink_root / script
            if ((script_symlink.exists() or script_symlink.is_symlink())
                    and str(script_symlink.resolve()).startswith(str(self.path))):
                script_symlink.unlink()

        shutil.rmtree(self.path)


class AppsPath:
    """
    Checks user access and determine if we are installing to system vs user path.

    System paths are /opt and /usr/local/bin and user paths are in ~
    """
    # System install paths (e.g. root)
    SYSTEM_INSTALL_ROOT = Path('/opt/apps')
    SYSTEM_SYMLINK_ROOT = Path('/usr/local/bin')
    SYSTEM_LOG_ROOT = Path('/var/log/autopip')

    # Local install paths (e.g. user owned /usr/local on macOS)
    _LOCAL_BASE = Path('/usr/local')
    LOCAL_INSTALL_ROOT = _LOCAL_BASE / 'opt' / 'apps'
    LOCAL_SYMLINK_ROOT = _LOCAL_BASE / 'bin'
    LOCAL_LOG_ROOT = _LOCAL_BASE / 'var' / 'log' / 'autopip'

    # User install paths
    USER_INSTALL_ROOT = Path.home() / '.apps'
    USER_SYMLINK_ROOT = Path.home() / 'bin'
    USER_LOG_ROOT = USER_INSTALL_ROOT / '.log'

    def __init__(self):
        #: Root to install apps. This will be set at runtime based on permission by :meth:`_set_roots`
        self.install_root = None

        #: Root to install symlinks. This will be set at runtime based on permission by :meth:`_set_roots`
        self.symlink_root = None

        #: Root to write log files. This will be set at runtime based on permission by :meth:`_set_roots`
        self.log_root = None

        #: Indicates if we are using user paths as we do not have access to system paths.
        self.is_user = False

        self._set_roots()

    def _set_roots(self):
        """ Check to see if we have access to system paths and set roots accordingly. """
        system_reasons = []
        local_reasons = []

        # Check system
        if not os.access(self.SYSTEM_INSTALL_ROOT.parent, os.W_OK):
            system_reasons.append(f'No permission to write to {self.SYSTEM_INSTALL_ROOT.parent}')

        if not os.access(self.SYSTEM_SYMLINK_ROOT, os.W_OK):
            system_reasons.append(f'No permission to write to {self.SYSTEM_SYMLINK_ROOT}')

        if not (os.access(self.SYSTEM_LOG_ROOT.parent, os.W_OK)):
            system_reasons.append(f'No permission to write to {self.SYSTEM_LOG_ROOT.parent}')

        if system_reasons:
            debug('Not using system paths because:\n%s', '* ' + '\n* '.join(system_reasons))

        # Check local
        if system_reasons:
            if not (os.access(self.LOCAL_INSTALL_ROOT.parent, os.W_OK)
                    or not self.LOCAL_INSTALL_ROOT.parent.exists()
                    and os.access(self.LOCAL_INSTALL_ROOT.parent.parent, os.W_OK)):
                local_reasons.append(f'No permission to write to {self.LOCAL_INSTALL_ROOT.parent}')

            if not os.access(self.LOCAL_SYMLINK_ROOT, os.W_OK):
                local_reasons.append(f'No permission to write to {self.LOCAL_SYMLINK_ROOT}')

            if not (os.access(self.LOCAL_LOG_ROOT.parent, os.W_OK)
                    or not self.LOCAL_LOG_ROOT.parent.exists()
                    and os.access(self.LOCAL_LOG_ROOT.parent.parent, os.W_OK)):
                local_reasons.append(f'No permission to write to {self.LOCAL_LOG_ROOT.parent}')

            if local_reasons:
                debug('Not using local paths because:\n%s', '* ' + '\n* '.join(local_reasons))

        if not system_reasons:
            self.install_root = self.SYSTEM_INSTALL_ROOT
            self.symlink_root = self.SYSTEM_SYMLINK_ROOT
            self.log_root = self.SYSTEM_LOG_ROOT

        elif not local_reasons:
            self.install_root = self.LOCAL_INSTALL_ROOT
            self.symlink_root = self.LOCAL_SYMLINK_ROOT
            self.log_root = self.LOCAL_LOG_ROOT

        else:
            self.install_root = self.USER_INSTALL_ROOT
            self.symlink_root = self.USER_SYMLINK_ROOT
            self.log_root = self.USER_LOG_ROOT
            self.is_user = True

        self.install_root.mkdir(parents=True, exist_ok=True)
        self.symlink_root.mkdir(parents=True, exist_ok=True)
        self.log_root.mkdir(parents=True, exist_ok=True)

    def covers(self, path):
        """ True if the given path belongs to autopip """
        path = path.resolve() if isinstance(path, PurePath) else path
        return (str(path).startswith(str(self.SYSTEM_INSTALL_ROOT))
                or str(path).startswith(str(self.LOCAL_INSTALL_ROOT))
                or str(path).startswith(str(self.USER_INSTALL_ROOT)))
