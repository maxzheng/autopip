import argparse
import logging
import signal
import sys

from autopip.constants import UpdateFreq
from autopip.manager import AppsManager


def main():
    args = cli_args()
    setup_logger(debug=args.debug)
    mgr = AppsManager(debug=args.debug)

    signal.signal(signal.SIGALRM, lambda *args, **kwargs: exit("""Uh oh, something is wrong...
  autopip has been running for an hour and is likely stuck, so exiting to prevent resource issues.
  Please report this issue at https://github.com/maxzheng/autopip/issues"""))
    signal.alarm(3600)

    try:
        if args.command == 'install':
            mgr.install(args.apps, update=UpdateFreq.from_name(args.update) if args.update else None)

        elif args.command == 'list':
            mgr.list(name_filter=args.name_filter, scripts=args.scripts)

        elif args.command == 'uninstall':
            mgr.uninstall(args.apps)

        else:
            raise NotImplementedError('Command {} not implemented yet'.format(args.command))

    except BaseException as e:
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
    default_update = UpdateFreq.DEFAULT.name.lower() if parser.prog == 'autopip' else None
    install_parser.add_argument('--update', choices=[m.name.lower() for m in UpdateFreq],
                                default=default_update,
                                help='How often to update the app. {}'.format(
                                    '[default: %(default)s]' if default_update else ''))
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
