import logging

from autopip.manager import AppsPath, AppsManager
from utils_core.fs import in_temp_dir


def test_parse_pip_conf():
    with in_temp_dir():
        with open('pip.conf', 'w') as fh:
            fh.write('[global]\nindex-url = https://test.com/pypi/simple')
        assert ('https://test.com/pypi/simple/', None) == AppsManager._parse_pip_conf_for_index('pip.conf')

        with open('pip.conf', 'w') as fh:
            fh.write('[global]\nindex-url = https://user:pass@test.com/pypi/simple')
        assert ('https://test.com/pypi/simple/', ('user', 'pass')) == AppsManager._parse_pip_conf_for_index('pip.conf')


def test_parse_netrc():
    with in_temp_dir():
        with open('netrc', 'w') as fh:
            fh.write('machine test.com\tlogin user password pass')
        assert not AppsManager._parse_netrc_credential_for('blah.com', netrc_file='netrc')

        assert ('user', 'pass') == AppsManager._parse_netrc_credential_for('repo.test.com/pypi/simple',
                                                                           netrc_file='netrc')
        with open('netrc', 'w') as fh:
            fh.write('machine test.com\nlogin user2\npassword pass2')

        assert ('user2', 'pass2') == AppsManager._parse_netrc_credential_for('repo.test.com/pypi/simple',
                                                                             netrc_file='netrc')


def test_paths(monkeypatch, caplog, mock_paths):
    caplog.set_level(logging.DEBUG)
    monkeypatch.setenv('HOME', 'user')

    system_root, local_root, user_root = mock_paths

    # User paths
    system_root.chmod(0o555)
    local_root.chmod(0o555)
    paths = AppsPath()

    assert paths.install_root == user_root
    assert paths.symlink_root == user_root / 'bin'
    assert paths.log_root == user_root / 'log'
    assert paths.is_user
    assert caplog.text == f"""\
Not using system paths because:
* No permission to write to {system_root}
Not using local paths because:
* No permission to write to {local_root}
"""

    # Local paths
    caplog.clear()
    local_root.chmod(0o755)
    paths = AppsPath()

    assert paths.install_root == local_root
    assert paths.symlink_root == local_root / 'bin'
    assert paths.log_root == local_root / 'log'
    assert not paths.is_user
    assert caplog.text == f"""\
Not using system paths because:
* No permission to write to {system_root}
"""

    # System paths
    caplog.clear()
    system_root.chmod(0o755)
    paths = AppsPath()

    assert paths.install_root == system_root
    assert paths.symlink_root == system_root / 'bin'
    assert paths.log_root == system_root / 'log'
    assert not paths.is_user
    assert caplog.text == ''
