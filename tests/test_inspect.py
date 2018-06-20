import pkg_resources

from autopip.inspect_app import gather_intel, get_scripts


def test_gather_intel():
    assert gather_intel('autopip') == {'group_specs': [], 'scripts': ['app', 'autopip']}


def test_scripts(monkeypatch):
    dist = pkg_resources.get_distribution('autopip')
    dist.get_entry_map = lambda *arg: {}
    assert get_scripts(dist) == []
