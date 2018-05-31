import argparse
import logging
import sys

from autopip.manager import AppsManager


def main():
    args = cli_args()
    setup_logger(debug=args.debug)
    mgr = AppsManager(debug=args.debug)

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
        if str(e):
            logging.error(f'! {e}', exc_info=args.debug)
        sys.exit(1)


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


def setup_logger(debug=False):
    if debug:
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', stream=sys.stdout, level=logging.DEBUG)

    elif sys.stdout.isatty():
        logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)

    else:
        logging.basicConfig(format='%(asctime)s %(message)s', stream=sys.stdout, level=logging.INFO)
