#!/usr/bin/env python

import argparse
import json
import re


def gather_intel(app):
    """ Get scripts and entry points info from app """
    try:
        from importlib.metadata import entry_points

        scripts = [e.name for e in entry_points(group='console_scripts') if e.dist.name == app]
        intel = {
            'scripts': scripts,
            'group_specs': []  # Not supported as it isn't used anymore
        }

    except Exception:
        import pkg_resources  # Deprecated as API: https://setuptools.pypa.io/en/latest/pkg_resources.html
        dist = pkg_resources.get_distribution(app)
        intel = {
            'scripts': get_scripts(dist),
            'group_specs': get_group_specs(dist),
        }

    return intel


def get_scripts(dist):
    console_scripts = dist.get_entry_map('console_scripts')

    if console_scripts:
        return list(console_scripts.keys())

    scripts = set()

    for record_file in ['RECORD', 'installed-files.txt', 'SOURCES.txt']:
        try:
            records = dist.get_metadata(record_file)

        except Exception:
            continue

        if records:
            bin_re = re.compile(r'\.\./bin/([^,]+),?')

            for line in records.split('\n'):
                match = bin_re.search(line)

                if match:
                    scripts.add(match.group(1))

    return list(scripts)


def get_group_specs(dist):
    app_specs = []

    for app, spec in dist.get_entry_map('autopip').items():
        app_specs.append((app, spec.module_name, next(iter(spec.extras), None)))

    return app_specs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=gather_intel.__doc__)
    parser.add_argument('app', help='App to get info from')
    args = parser.parse_args()

    print(json.dumps(gather_intel(args.app)))
