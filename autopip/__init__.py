import argparse
import sys

from autopip.manager import AppsManager


def cli_args():
    """" Get command-line args """
    parser = argparse.ArgumentParser(description='Easily install apps from PyPI and '
                                                 'automatically keep them updated.')
    parser.add_argument('--debug', action='store_true', help='Turn on debug mode')
    subparsers = parser.add_subparsers(title='Commands', help='List of commands')

    install_parser = subparsers.add_parser('install',
                                           help='Install apps in their own virtual environments '
                                                'that automatically updates')
    install_parser.add_argument('apps', nargs='+', help='Apps to install')
    install_parser.set_defaults(command='install')

    list_parser = subparsers.add_parser('list', help='List installed apps')
    list_parser.add_argument('name_filter', nargs='?', help='Optionally filter by name')
    list_parser.add_argument('--scripts', action='store_true', help='Show scripts')
    list_parser.set_defaults(command='list')

    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall apps')
    uninstall_parser.add_argument('apps', nargs='+', help='Apps to uninstall')
    uninstall_parser.set_defaults(command='uninstall')

    return parser.parse_args()


def main():
    args = cli_args()
    mgr = AppsManager()

    try:
        if args.command == 'install':
            mgr.install(args.apps)

        elif args.command == 'list':
            mgr.list(scripts=args.scripts)

        elif args.command == 'uninstall':
            mgr.uninstall(args.apps)

        else:
            raise NotImplementedError('Command {} not implemented yet'.format(args.command))

    except Exception as e:
        if args.debug:
            raise
        elif str(e):
            print(f'! {e}')
        sys.exit(1)
