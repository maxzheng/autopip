from configparser import RawConfigParser
from collections import defaultdict
from functools import lru_cache
import json
import imp
from logging import info, error, debug
import os
from pathlib import Path, PurePath
import pkg_resources
import re
import shutil
from subprocess import check_output as run, CalledProcessError, STDOUT
import sys
from time import time
import urllib.request
import urllib.error

from autopip.constants import UpdateFreq
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

    def install(self, apps, update=None):
        """
        Install the given apps

        :param list[str] apps: List of apps to install
        :param UpdateFreq|None update: How often to update
        """
        self._set_index()

        autopip_path = shutil.which('autopip')
        if (self.paths.is_user and sys.stdout.isatty() and not list(self.apps) and autopip_path and
                autopip_path.startswith(str(self.paths.SYSTEM_SYMLINK_ROOT))):
            info('# Based on permission, this will install to your user home instead of %s',
                 self.paths.SYSTEM_SYMLINK_ROOT)
            info('  To install for everyone, cancel using CTRL+C and then re-run using sudo.')

        failed_apps = []

        for name in apps:
            try:
                if isinstance(name, tuple):  # From app.group_specs() below
                    name, update = name
                    if update:
                        update = UpdateFreq.from_name(update)

                app_spec = next(iter(pkg_resources.parse_requirements(name)))
                app, updated = self._install_app(app_spec, update=update)

                group_specs = app.group_specs()
                if updated and group_specs:
                    info('This app has defined "autopip" entry points to install: %s', ' '.join(
                         s[0] for s in group_specs))
                    apps.extend(group_specs)

            except Exception as e:
                error(f'! {e}', exc_info=self.debug)
                failed_apps.append(name)

        if failed_apps:
            raise exceptions.FailedAction()

    def _install_app(self, app_spec, update=None):
        """ Install the given app """
        app = App(app_spec.name, self.paths)
        updated = False

        # Skip update if install was done within the update frequency when run from cron
        if (sys.stdout.isatty() or not app.is_installed or
                update and app.path.stat().st_mtime + update.seconds < time()):
            if app.is_installed:
                app.path.touch()

            version = self._app_version(app_spec)
            updated = app.install(version, app_spec, update=update)

        else:
            debug('App is up to date')

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
            update = f"[updates {app.settings()['update']}]" if app.settings().get('update') else ''
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
            if (self.paths.is_user and sys.stdout.isatty() and autopip_path and
                    autopip_path.startswith(str(self.paths.SYSTEM_SYMLINK_ROOT))):
                info('To see apps installed in %s, re-run using sudo.', self.paths.SYSTEM_SYMLINK_ROOT)

    def uninstall(self, apps):
        """ Uninstall apps """
        for name in apps:
            if name == 'bin':  # Don't try to remove bin (contains symlinks to scripts) from the app dir
                continue

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

        #: Path to install all app versions
        self.path = self.paths.install_root / name

        #: Symlink to current version
        self._current_symlink = self.path / 'current'

        # Unique crontab name to to easily add and remove from crontab
        self._crontab_id = rf'autopip install "{self.name}[^a-z]*"'

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

    def install(self, version, app_spec, update=None):
        """
        Install the version of the app if it is not already installed

        :param str version: Version of the app to install
        :param pkg_resources.Requirement app_spec: App version requirement from user
        :param UpdateFreq|None update: How often to update. Choose from hourly, daily, weekly, monthly
        :return: True if install or update happened, otherwise False when nothing happened (already installed / non-tty)
        """
        version_path = self.path / version
        prev_version_path = self.current_path and self.current_path.resolve()
        important_paths = [version_path, prev_version_path, self._current_symlink]

        if version_path.exists():
            if self.current_version == version:
                # Skip printing / ensuring symlinks / cronjob when running from cron
                if not sys.stdout.isatty():
                    return False

                info(f'{self.name} is already installed')

            else:
                info(f'Setting {version} as the current version for {self.name}')

        else:
            old_venv_dir = None
            old_path = None

            try:
                info(f'Installing {self.name} to {version_path}')
                if 'VIRTUAL_ENV' in os.environ:
                    old_venv_dir = os.environ.pop('VIRTUAL_ENV')
                    old_path = os.environ['PATH']
                    os.environ['PATH'] = os.pathsep.join([p for p in os.environ['PATH'].split(os.pathsep)
                                                          if os.path.exists(p) and not p.startswith(old_venv_dir)])

                run(f"""set -e
                    python3 -m venv {version_path}
                    source {version_path / 'bin/activate'}
                    pip install --upgrade pip
                    pip install {self.name}=={version}
                    """, executable='/bin/bash', stderr=STDOUT, shell=True)

            except BaseException as e:
                shutil.rmtree(version_path, ignore_errors=True)

                if isinstance(e, CalledProcessError) and e.output:
                    info(re.sub(r'(https?://)[^/]+:[^/]+@', r'\1<xxx>:<xxx>@', e.output.decode('utf-8')))

                raise

            finally:
                if old_venv_dir:
                    os.environ['VIRTUAL_ENV'] = old_venv_dir
                    os.environ['PATH'] = old_path

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

        # Install cronjobs
        if sys.stdout.isatty() and update:  # Skip updating cronjob when run from cron
            try:
                autopip_path = shutil.which('autopip')
                if not autopip_path:
                    raise exceptions.MissingError(
                        'autopip is not available. Please make sure its bin folder is in PATH env var')
                auto_update = f'--update {update.name.lower()} ' if update and update != UpdateFreq.DEFAULT else ''
                crontab.add(f'{autopip_path} install "{app_spec}" {auto_update}'
                            f'2>&1 >> {self.paths.log_root / "cron.log"}', cmd_id=self._crontab_id)
                info(update.name.title() + ' auto-update enabled via cron service')

                self.settings(update=update.name.lower())

            except Exception as e:
                error('! Auto-update was not enabled because: %s', e)

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

        if not printed_updating and sys.stdout.isatty() and current_scripts:
            info('Scripts are in {}: {}'.format(self.paths.symlink_root, ', '.join(sorted(current_scripts))))

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
        dist = self._pkg_distribution(path=path)

        if dist:
            console_scripts = dist.get_entry_map('console_scripts')

            if console_scripts:
                return set(console_scripts.keys())

            try:
                records = dist.get_metadata('RECORD')
            except Exception:
                records = dist.get_metadata('installed-files.txt')

            if records:
                scripts = set()
                bin_re = re.compile('../bin/([^,]+),?')

                for line in records.split('\n'):
                    match = bin_re.search(line)

                    if match:
                        scripts.add(match.group(1))

                return scripts

        return set()

    def group_specs(self, path=None, name_only=False):
        """ List of app specs from this app's "autopip" entry points for the given app path (defaults to current)"""
        app_specs = []
        dist = self._pkg_distribution(path=path)

        if dist:
            for app, spec in dist.get_entry_map('autopip').items():
                if name_only:
                    app_specs.append(app)

                elif spec.module_name == 'latest':
                    app_specs.append((app, UpdateFreq.DEFAULT.name.lower()))

                else:
                    if len(spec.module_name.split('.')) < 3 or spec.extras:     # Wildcard with auto-update
                        app_specs.append((f'{app}=={spec.module_name}.*',
                                         next(iter(spec.extras), UpdateFreq.DEFAULT.name.lower())))
                    else:
                        app_specs.append((f'{app}=={spec.module_name}', None))  # Specific version without auto-update

        return app_specs

    @lru_cache()
    def _pkg_distribution(self, path=None):
        """ Get pkg_resources.Distribution() for the given path (defaults to current path) """
        if not path:
            if not self.current_path:
                return

            path = self.current_path

        try:
            return pkg_resources.get_distribution(self.name)

        except pkg_resources.DistributionNotFound:
            activated = False

            try:
                activate_this_file = path / 'bin' / 'activate_this.py'

                if not activate_this_file.exists():
                    shutil.copyfile(Path(__file__).parent / 'embedded' / 'activate_this.py', activate_this_file)

                old_os_path = os.environ.get('PATH', '')
                old_sys_path = list(sys.path)
                old_prefix = sys.prefix

                exec(open(activate_this_file).read(), dict(__file__=activate_this_file))
                activated = True

                imp.reload(pkg_resources)
                return pkg_resources.get_distribution(self.name)

            except Exception as e:
                error('! Can not get package distribution info because: %s', e)

            finally:
                if activated:
                    os.environ['PATH'] = old_os_path
                    sys.path = old_sys_path
                    sys.prefix = old_prefix
                    imp.reload(pkg_resources)

    def uninstall(self):
        """ Uninstall app """
        info('Uninstalling %s', self.name)

        try:
            crontab.remove(self._crontab_id)
        except exceptions.MissingError as e:
            debug(e)

        for script in self.scripts():
            script_symlink = self.paths.symlink_root / script
            if ((script_symlink.exists() or script_symlink.is_symlink()) and
                    str(script_symlink.resolve()).startswith(str(self.path))):
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
    USER_INSTALL_ROOT = Path('~/.apps').expanduser()
    USER_SYMLINK_ROOT = USER_INSTALL_ROOT / 'bin'
    USER_LOG_ROOT = USER_INSTALL_ROOT / 'log'

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
            if not os.access(self.LOCAL_INSTALL_ROOT.parent, os.W_OK):
                local_reasons.append(f'No permission to write to {self.LOCAL_INSTALL_ROOT.parent}')

            if not os.access(self.LOCAL_SYMLINK_ROOT, os.W_OK):
                local_reasons.append(f'No permission to write to {self.LOCAL_SYMLINK_ROOT}')

            if not (self.LOCAL_LOG_ROOT.parent.exists() and os.access(self.LOCAL_LOG_ROOT.parent, os.W_OK) or
                    not self.LOCAL_LOG_ROOT.parent.exists() and os.access(self.LOCAL_LOG_ROOT.parent.parent, os.W_OK)):
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
        return (str(path).startswith(str(self.SYSTEM_INSTALL_ROOT)) or
                str(path).startswith(str(self.LOCAL_INSTALL_ROOT)) or
                str(path).startswith(str(self.USER_INSTALL_ROOT)))
