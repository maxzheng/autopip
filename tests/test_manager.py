import logging

from autopip.manager import AppsPath


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
