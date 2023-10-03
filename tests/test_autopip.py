import re
from time import time

from mock import Mock, call

from autopip.utils import run
from autopip.constants import PYTHON_VERSION, PYTHON_PATH


def test_autopip_help(autopip, capsys):
    autopip('', raises=SystemExit)
    stdout, stderr = capsys.readouterr()

    assert 'usage: autopip' in stdout


def test_autopip_common(monkeypatch, autopip, capsys, mock_paths, mock_run):
    system_root, _, _ = mock_paths
    monkeypatch.setattr('autopip.crontab.randint', Mock(return_value=10))

    # Install latest
    stdout = autopip('install bumper --update hourly')
    assert 'Installing bumper to' in stdout
    assert 'Updating script symlinks in' in stdout
    assert '+ bump' in stdout
    assert len(stdout.split('\n')) == 6

    assert run([str(system_root / 'bin' / 'bump'), '-h']).startswith('usage: bump')

    assert len(mock_run.call_args_list) == 6
    assert mock_run.call_args_list[0:-1] == [
        call('which crontab', stderr=-2, shell=True),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', stderr=-2, shell=True),
        call('crontab -l | grep -i "autopip"', stderr=-2, shell=True),
        call('which crontab', stderr=-2, shell=True),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', stderr=-2, shell=True),
        ]
    update_call = re.sub('(/tmp|/private)/.*/system/', '/tmp/system/',
                         re.sub('/home/.*/autopip/', '/home/venv/autopip/',
                                re.sub(' /Users/.*/autopip/', ' /home/venv/autopip/',
                                       mock_run.call_args_list[-1][0][0])))
    assert update_call == (
        rf'( crontab -l | grep -vi "autopip update"; echo "10 * * * * PATH={PYTHON_PATH}:\$PATH '
        r'/home/venv/autopip/bin/autopip update 2>&1 >> /tmp/system/log/cron.log" ) | crontab -')

    assert 'system/bumper/0.1.13' in autopip('list')
    assert autopip('list --scripts').split('\n')[1].strip().endswith('/bin/bump')

    # Already installed
    mock_run.reset_mock()
    assert autopip('install bumper --update hourly') == """\
bumper is up-to-date
Adding to crontab (may require admin permission)
Hourly auto-update enabled via cron service
Scripts are in /tmp/system/bin: bump
"""
    assert mock_run.call_count == 6

    # Update manually
    assert autopip('update') == 'bumper is up-to-date\n'
    assert autopip('update blah') == 'No apps found matching: blah\nAvailable apps: bumper\n'

    # Update via cron
    assert autopip('update', isatty=False) == ''
    bumper_root = system_root / 'bumper'
    last_modified = bumper_root.stat().st_mtime
    with monkeypatch.context() as m:
        m.setattr('autopip.manager.time', Mock(return_value=time() + 3600))
        assert autopip('update', isatty=False) == ''
        current_modified = bumper_root.stat().st_mtime
        assert current_modified > last_modified

    # Wait for new version
    mock_sleep = Mock(side_effect=[0, 0, 0, Exception('No new version')])
    monkeypatch.setattr('autopip.manager.sleep', mock_sleep)

    stdout, e = autopip('update bumper --wait', raises=SystemExit)
    assert stdout.startswith('! No new version')

    stdout, _ = capsys.readouterr()
    assert 'Waiting for new version of bumper to be published...' in stdout
    assert '\033[1AWaiting for new version of bumper to be published...' in stdout

    assert mock_sleep.call_count == 4

    # Uninstall
    mock_run.reset_mock()
    assert autopip('uninstall bumper') == ('Uninstalling bumper\n'
                                           'Removing from crontab (may require admin permission)\n')
    assert mock_run.call_args_list == [
        call('which crontab', stderr=-2, shell=True),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', stderr=-2, shell=True),
        call('crontab -l | grep -i "autopip"', stderr=-2, shell=True),
        call('which crontab', stderr=-2, shell=True),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', stderr=-2, shell=True),
        call('( crontab -l | grep -vi "autopip" ) | crontab -', stderr=-2, shell=True)
    ]

    assert autopip('list') == 'No apps are installed yet.\n'


def test_update(autopip):
    assert autopip('update') == 'No apps installed yet.\n'


def test_install_lib(autopip):
    stdout, e = autopip('install utils-core', raises=SystemExit)
    assert 'Uninstalling utils-core' in stdout
    assert '! Odd, there are no scripts included in the app' in stdout


def test_install_bad_version(autopip, monkeypatch):
    stdout, _ = autopip('install bumper==100.*', raises=SystemExit)
    assert '! No app version matching bumper==100.*' in stdout
    assert 'Available versions: 0.1.8, 0.1.9, 0.1.10, 0.1.11, 0.1.12' in stdout


def test_install_no_path(autopip, monkeypatch):
    monkeypatch.setenv('PATH', '')
    stdout, _ = autopip('install bumper', raises=SystemExit)

    assert stdout == (f'! python{PYTHON_VERSION} does not exist. '
                      'Please install it first, or ensure its path is in PATH.\n')


def test_install_nonexisting(autopip):
    stdout, _ = autopip('install this-does-not-exist-blah-blah', raises=SystemExit)
    assert stdout.startswith('! No app version found in http') \
        or stdout.startswith('! this-does-not-exist-blah-blah does not exist on http')


def test_install_failed(autopip, monkeypatch, mock_run):
    mock_run.side_effect = Exception('install failed')
    monkeypatch.setattr('autopip.manager.run', mock_run)
    stdout, _ = autopip('install utils-core', raises=SystemExit)
    assert '! install failed' in stdout


def test_install_autopip(autopip, monkeypatch):
    assert autopip('install autopip==1.4.2 --update hourly') == """\
Installing autopip to /tmp/system/autopip/1.4.2
Auto-update will be disabled since we are pinning to a specific version.
To enable, re-run without pinning to specific version with --update option
Updating script symlinks in /tmp/system/bin
+ app
+ autopip
"""
    with monkeypatch.context() as m:
        remove_cron = Mock(side_effect=Exception('failed'))
        m.setattr('autopip.manager.crontab.remove', remove_cron)
        assert autopip('update', isatty=False) == ''
        remove_cron.assert_called_with('autopip')

    stdout = autopip('list auto --scripts')
    assert re.sub(' +autopip', ' ' * 32 + 'autopip', stdout) == """\
autopip  1.4.2  /tmp/system/autopip/1.4.2  
                /tmp/system/bin/app        
                                autopip    
"""  # noqa

    assert autopip('uninstall autopip') == ('Uninstalling autopip\n'
                                            'Removing from crontab (may require admin permission)\n')


def test_autopip_group(monkeypatch, autopip, mock_run):
    monkeypatch.setattr('autopip.crontab.randint', Mock(return_value=10))

    def mock_group_specs(self, path=None, name_only=False):
        if self.name == 'developer-tools':
            return ['bumper'] if name_only else [('bumper==0.1.10', None)]
        else:
            return []

    monkeypatch.setattr('autopip.manager.App.group_specs', mock_group_specs)

    # Install latest
    stdout = autopip('install developer-tools --update weekly')
    installed_version = stdout.split('\n')[0].split('/')[-1]
    assert 'Installing developer-tools to' in stdout
    assert 'Updating script symlinks in' in stdout
    assert 'This app has defined "autopip" entry points to install: bumper==0.1.10' in stdout
    assert '+ bump' in stdout
    assert len(stdout.split('\n')) == 8

    assert len(mock_run.call_args_list) == 6
    assert mock_run.call_args_list[0:-1] == [
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2),
        call('crontab -l | grep -i "autopip"', shell=True, stderr=-2),
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2)
        ]
    update_call = re.sub('(/tmp|/private)/.*/system/', '/tmp/system/',
                         re.sub('/home/.*/autopip/', '/home/venv/autopip/',
                                re.sub(' /Users/.*/autopip/', ' /home/venv/autopip/',
                                       mock_run.call_args_list[-1][0][0])))
    assert update_call == (
        rf'( crontab -l | grep -vi "autopip update"; echo "10 * * * * PATH={PYTHON_PATH}:\$PATH '
        r'/home/venv/autopip/bin/autopip update 2>&1 >> /tmp/system/log/cron.log" ) | crontab -')

    assert 'system/bumper/0.1.10' in autopip('list')
    assert f'system/developer-tools/{installed_version}' in autopip('list')
    assert autopip('list --scripts').split('\n')[1].strip().endswith('/bin/bump')
    assert autopip('list blah') == 'No apps matching "blah"\n'

    # Uninstall autopip
    assert autopip('uninstall autopip') == ('! autopip can not be uninstalled until other apps are uninstalled: '
                                            'bumper developer-tools\n')

    # Update
    assert autopip('update') == """\
bumper is up-to-date [per spec: ==0.1.10]
developer-tools is up-to-date
This app has defined "autopip" entry points to install: bumper==0.1.10
"""

    # Already installed
    mock_run.reset_mock()
    assert autopip(f'install developer-tools=={installed_version}') == """\
developer-tools is up-to-date [per spec: ==1.0.8]
Auto-update will be disabled since we are pinning to a specific version.
To enable, re-run without pinning to specific version with --update option
This app has defined "autopip" entry points to install: bumper==0.1.10
bumper is up-to-date [per spec: ==0.1.10]
Scripts are in /tmp/system/bin: bump
"""
    # Uninstall
    mock_run.reset_mock()
    assert autopip('uninstall developer-tools') == """\
Uninstalling developer-tools
This app has defined "autopip" entry points to uninstall: bumper
Uninstalling bumper
Removing from crontab (may require admin permission)
"""
    assert mock_run.call_args_list == [
        call('which crontab', stderr=-2, shell=True),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', stderr=-2, shell=True),
        call('crontab -l | grep -i "autopip"', stderr=-2, shell=True),
        call('which crontab', stderr=-2, shell=True),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', stderr=-2, shell=True),
        call('( crontab -l | grep -vi "autopip" ) | crontab -', stderr=-2, shell=True)
    ]

    assert autopip('list') == 'No apps are installed yet.\n'
