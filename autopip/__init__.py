import argparse
import sys

from autopip.manager import PackagesManager


def cli_args():
    """" Get command-line args """
    parser = argparse.ArgumentParser(description='Easily install packages from PyPI and '
                                                 'automatically keep them updated.')
    subparsers = parser.add_subparsers(title='Commands', help='List of commands')

    install_parser = subparsers.add_parser('install',
                                           help='Install packages in their own virtual environments '
                                                'that automatically updates')
    install_parser.add_argument('packages', nargs='+', help='Packages to install')
    install_parser.set_defaults(command='install')

    list_parser = subparsers.add_parser('list', help='List installed packages')
    list_parser.add_argument('name_filter', nargs='?', help='Optionally filter by name')
    list_parser.set_defaults(command='list')

    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall packages')
    uninstall_parser.add_argument('packages', help='Packages to uninstall')
    uninstall_parser.set_defaults(command='uninstall')

    return parser.parse_args()


def main():
    args = cli_args()
    mgr = PackagesManager()

    if args.command == 'install':
        mgr.install(args.packages)

    elif args.commands == 'list':
        mgr.list()

    elif args.command == 'uninstall':
        mgr.uninstall(args.packages)

    else:
        print('Command {} not implemented yet'.format(args.command))
        sys.exit(1)
