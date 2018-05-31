from configparser import RawConfigParser
from collections import defaultdict
from logging import info, error
import os
from pathlib import Path, PurePath
from pkg_resources import parse_requirements
import re
import shutil
from subprocess import check_output as run, CalledProcessError, STDOUT
import sys
import urllib.request
import urllib.error

from autopip import crontab, exceptions


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

    def install(self, apps):
        """
        Install the given apps

        :param list[str] apps: List of apps to install
        """
        self._ensure_paths()
        self._set_index()

        autopip_path = shutil.which('autopip')
        if (self.paths.user_access and sys.stdout.isatty() and not list(self.apps) and autopip_path and
                autopip_path.startswith(str(self.paths.SYSTEM_SYMLINK_ROOT))):
            info('! Based on permission, this will install to your user home instead of %s',
                 self.paths.SYSTEM_SYMLINK_ROOT.parent)
            info('  To install for everyone, cancel using CTRL+C and then re-run using sudo.')
            info('  As using sudo to install is a security risk, please do so only if you trust the app.')

        failed_apps = []

        for app in apps:
            try:
                app_spec = next(iter(parse_requirements(app)))
                self._install_app(app_spec)

            except Exception as e:
                error(f'! {e}', exc_info=self.debug)
                failed_apps.append(app)

        if failed_apps:
            raise exceptions.FailedAction()

    def _ensure_paths(self):
        """ Ensure install and symlink paths are created """
        self.paths.install_root.mkdir(parents=True, exist_ok=True)
        self.paths.symlink_root.mkdir(parents=True, exist_ok=True)
        self.paths.log_root.mkdir(parents=True, exist_ok=True)

    def _install_app(self, app_spec):
        """ Install the given app """
        version = self._app_version(app_spec)

        app = App(app_spec.name, self.paths)
        app.install(version, app_spec)

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
                raise NameError(f'App does not exist on {self._index_url}')

        version_re = re.compile(app_spec.name + '-(\d+\.\d+\.\d+(?:\.\w+\d+)?)\.')
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
                raise ValueError(f'No app version matching {app_spec} \nAvailable versions: ' + ', '.join(versions))
            else:
                raise ValueError(f'No app version found in {pkg_index_url}')

        version_sep_re = re.compile('[^0-9]+')
        sorted_versions = sorted(matched_versions, key=lambda v: tuple(map(int, version_sep_re.split(v))))

        return sorted_versions[-1]

    def _set_index(self):
        """ Set PyPI url and auth """
        if not self._index_url:
            try:
                pip_conf = Path('~/.pip/pip.conf').expanduser()
                parser = RawConfigParser()
                parser.read(pip_conf)
                self._index_url = parser.get('global', 'index-url')

                auth_re = re.compile('//([^:]+)(?::([^@]+))?@')
                match = auth_re.search(self._index_url)
                if match:
                    self._index_auth = match.groups()
                    self._index_url = auth_re.sub('//', self._index_url)

                if not self._index_url.endswith('/'):
                    self._index_url += '/'

            except Exception:
                self._index_url = 'https://pypi.org/simple/'

    @property
    def apps(self):
        """ Iterator for installed apps """
        for app_path in sorted(self.paths.install_root.iterdir()):
            if app_path in {self.paths.symlink_root, self.paths.log_root}:
                continue

            app = App(app_path.name, self.paths)

            if app.is_installed:
                yield app

    def list(self, scripts=False):
        """
        List installed apps

        :param bool scripts: Show scripts
        """
        self._ensure_paths()

        app_info = []
        info_lens = defaultdict(int)

        for app in self.apps:
            app_path = str(app.current_path.resolve())
            app_info.append((app.name, app.current_version, app_path))

            if scripts:
                hide_path = False
                for script in sorted(app.scripts()):
                    script_symlink = self.paths.symlink_root / script
                    if script_symlink.exists() and str(script_symlink.resolve()).startswith(app_path):
                        script_path = str(script_symlink)
                        if hide_path:
                            script_path = script_path.replace(str(script_symlink.parent) + '/',
                                                              ' ' * len(str(script_symlink.parent)) + ' ')
                        app_info.append(('', '', script_path))
                        hide_path = True

        if app_info:
            # Figure out max length of each column
            for info_part in app_info:
                for i, value in enumerate(info_part):
                    info_lens[i] = len(value) if len(value) > info_lens[i] else info_lens[i]

            # Print table
            table_style = '  '.join('{{:{}}}'.format(l) for l in info_lens.values())
            for info_part in app_info:
                info(table_style.format(*info_part))

        else:
            info('No apps are installed yet.')

            autopip_path = shutil.which('autopip')
            if (self.paths.user_access and sys.stdout.isatty() and autopip_path and
                    autopip_path.startswith(str(self.paths.SYSTEM_SYMLINK_ROOT))):
                info('To see apps installed in %s, re-run using sudo.', self.paths.SYSTEM_SYMLINK_ROOT.parent)

    def uninstall(self, apps):
        """ Uninstall apps """
        self._ensure_paths()

        for name in apps:
            if name == 'bin':  # Don't try to remove bin (contains symlinks to scripts) from the app dir
                continue

            app = App(name, self.paths)
            if app.is_installed:
                app.uninstall()
            else:
                info(f'{name} is not installed')


class App:
    """ Represents an app that may or may not be installed on disk """

    #: Prefixes of scripts to skip when creating symlinks
    SKIP_SCRIPT_PREFIXES = {'activate', 'pip', 'easy_install', 'python', 'wheel'}

    def __init__(self, name, paths):
        """
        :param str name: Name of the app
        :param AppsPath paths: Path paths
        """
        self.name = name
        self.paths = paths

        self.path = self.paths.install_root / name
        self._current_symlink = self.path / 'current'

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

    def install(self, version, app_spec):
        """
        Install the version of the app if it is not already installed

        :param str version: Version of the app to install
        :param pkg_resources.Requirement app_spec: App version requirement from user
        """
        version_path = self.path / version
        prev_version_path = self.current_path and self.current_path.resolve()
        important_paths = [version_path, prev_version_path, self._current_symlink]

        if not shutil.which('curl'):
            raise exceptions.MissingCommandError('curl is not available and is required to install pip. '
                                                 'Please install and then re-run')

        if version_path.exists():
            if self.current_version == version:
                # Skip printing / ensuring symlinks / cronjob when running from cron
                if not sys.stdout.isatty():
                    return

                info(f'{self.name} is already installed')

            else:
                info(f'Setting {version} as the current version for {self.name}')

        else:
            old_path = None

            try:
                info(f'Installing {self.name} to {version_path}')
                if 'VIRTUAL_ENV' in os.environ:
                    venv_dir = os.environ.pop('VIRTUAL_ENV')
                    old_path = os.environ['PATH']
                    os.environ['PATH'] = os.pathsep.join([p for p in os.environ['PATH'].split(os.pathsep)
                                                          if os.path.exists(p) and not p.startswith(venv_dir)])
                run(f"""set -e
                    python3 -m venv {version_path} --without-pip
                    source {version_path / 'bin/activate'}
                    curl -s https://bootstrap.pypa.io/get-pip.py | python
                    pip install {self.name}=={version}
                    """, executable='/bin/bash', stderr=STDOUT, shell=True)

            except BaseException as e:
                shutil.rmtree(version_path, ignore_errors=True)

                if isinstance(e, CalledProcessError) and e.output:
                    info(re.sub(r'(https?://)[^/]+:[^/]+@', r'\1<xxx>:<xxx>@', e.output.decode('utf-8')))

                raise

            finally:
                if old_path:
                    os.environ['PATH'] = old_path

        # Update current symlink
        if not self.current_path or self.current_path.resolve() != version_path:
            atomic_symlink = self.path / f'atomic_symlink_for_{self.name}'
            atomic_symlink.symlink_to(version_path)
            atomic_symlink.replace(self._current_symlink)

            # Remove older versions
            for path in [p for p in self.path.iterdir() if p not in important_paths]:
                shutil.rmtree(path, ignore_errors=True)

        # Install script symlinks
        current_bin_path = self.current_path / 'bin'
        prev_bin_path = prev_version_path / 'bin' if prev_version_path else None
        current_scripts = self.scripts(current_bin_path)

        if not current_scripts:
            self.uninstall()
            raise exceptions.InvalidAction(
                'Odd, there are no scripts included in the app, so there is no point installing it.\n'
                '  autopip is for installing apps with scripts. To install libraries, please use pip.\n'
                '  If you are the app owner, make sure to setup entry_points in setup.py.\n'
                '  See http://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation')

        prev_scripts = self.scripts(prev_bin_path) if prev_bin_path else set()
        old_scripts = prev_scripts - current_scripts

        printed_updating = False

        for script in sorted(current_scripts):
            script_symlink = self.paths.symlink_root / script
            script_path = current_bin_path / script

            if script_symlink.resolve() == script_path.resolve():
                continue

            if not printed_updating:
                info('Updating symlinks in {}'.format(self.paths.symlink_root))
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

        # Install cronjobs
        if sys.stdout.isatty():  # Skip updating cronjob when run from cron
            autopip_path = shutil.which('autopip')
            if not autopip_path:
                raise exceptions.MissingCommandError(
                    'autopip is not available. Please make sure its bin folder is in PATH env var')
            crontab.add(f'{autopip_path} install "{app_spec}" 2>&1 >> {self.paths.log_root / "cron.log"}')

    def scripts(self, path=None):
        """ Get scripts for the given path. Defaults to current path for app. """
        if not path:
            if not self.current_path:
                return []

            path = self.current_path / 'bin'

        scripts = set()
        for script in path.iterdir():
            if any(p for p in self.SKIP_SCRIPT_PREFIXES if script.name.startswith(p)):
                continue
            scripts.add(script.name)

        return scripts

    def uninstall(self):
        """ Uninstall app """
        info('Uninstalling %s', self.name)

        crontab.remove(f'autopip install "{self.name}')

        for script in self.scripts():
            script_symlink = self.paths.symlink_root / script
            if script_symlink.exists() and str(script_symlink.resolve()).startswith(str(self.path)):
                script_symlink.unlink()

        shutil.rmtree(self.path)


class AppsPath:
    """
    Checks user access and determine if we are installing to system vs user path.

    System paths are /opt and /usr/local/bin and user paths are in ~
    """
    #: Directory name to store apps in.
    _SYSTEM_BASE = Path('/usr/local')   # Use /usr/local so it is possible for user to own/use them without sudo.
    SYSTEM_INSTALL_ROOT = _SYSTEM_BASE / 'opt' / 'apps'
    SYSTEM_SYMLINK_ROOT = _SYSTEM_BASE / 'bin'
    SYSTEM_LOG_ROOT = _SYSTEM_BASE / 'var' / 'log' / 'autopip'

    USER_INSTALL_ROOT = Path('~/.apps').expanduser()
    USER_SYMLINK_ROOT = USER_INSTALL_ROOT / 'bin'
    USER_LOG_ROOT = USER_INSTALL_ROOT / 'log'

    def __init__(self):
        #: A list of reasons why we don't have system access
        self.system_access_denied_reasons = self._check_system_access()

        #: Indicates if we have access to system resources
        self.system_access = not self.system_access_denied_reasons

        #: Indicates if we should act on user resources as we do not have access to system resources.
        self.user_access = not self.system_access

    def _check_system_access(self):
        """ Check to see if we have access to system resources and return the reasons """
        reasons = []

        if not os.access(self.SYSTEM_INSTALL_ROOT.parent, os.W_OK):
            reasons.append(f'No permission to write to {self.SYSTEM_INSTALL_ROOT.parent}')

        if not os.access(self.SYSTEM_SYMLINK_ROOT, os.W_OK):
            reasons.append(f'No permission to write to {self.SYSTEM_SYMLINK_ROOT}')

        if not os.access(self.SYSTEM_LOG_ROOT.parent, os.W_OK):
            reasons.append(f'No permission to write to {self.SYSTEM_LOG_ROOT.parent}')

        return reasons

    @property
    def install_root(self):
        return self.SYSTEM_INSTALL_ROOT if self.system_access else self.USER_INSTALL_ROOT

    @property
    def symlink_root(self):
        return self.SYSTEM_SYMLINK_ROOT if self.system_access else self.USER_SYMLINK_ROOT

    @property
    def log_root(self):
        """ Root path to store log files """
        return self.SYSTEM_LOG_ROOT if self.system_access else self.USER_LOG_ROOT

    def covers(self, path):
        """ True if the given path belongs to autopip """
        path = path.resolve() if isinstance(path, PurePath) else path
        return str(path).startswith(str(self.install_root))
