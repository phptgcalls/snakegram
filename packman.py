# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import threading
import typing as t
from itertools import cycle
from datetime import timedelta
from contextlib import contextmanager


from builder import (
    clean,
    generate_code,
    TL_FOLDER, ERRORS_FOLDER
)

if sys.version_info >= (3, 11):
    import tomllib

else:
    import tomli as tomllib

def prompt(question: str, default: bool = False) -> bool:
    yes_no = 'Y/n' if default else 'y/N'
    answer = input(f'{question} [{yes_no}] ').strip()
    if not answer:
        return default

    return answer.lower() == 'y'

def seconds_to_hms(seconds: t.Union[int, float]):
    return str(timedelta(seconds=int(seconds)))

def is_empty_folder(path: str) -> bool:
    return not os.path.exists(path) or not os.listdir(path)


@contextmanager
def spinner(message, delay=.1):
    stop_thread = False

    def worker():
        chars = cycle('|/-\\')
        start_time = time.time()

        while not stop_thread:
            elapsed = seconds_to_hms(time.time() - start_time)

            sys.stdout.write(f'\r{message} {next(chars)} [{elapsed}]')
            sys.stdout.flush()
            time.sleep(delay)

        GREEN = '\033[32m'
        RESET = '\033[0m'
        elapsed = seconds_to_hms(time.time() - start_time)
        sys.stdout.write(f'\r{message} {GREEN}Done{RESET} [{elapsed}]\n')

    thread = threading.Thread(target=worker)
    thread.start()

    try:
        yield

    finally:
        stop_thread = True
        thread.join()


def get_version() -> t.Optional[str]:
    path = os.path.join(
        os.path.dirname(__file__),
        'pyproject.toml'
    )
    with open(path, 'rb') as fp:
        data = tomllib.load(fp)
        project = data.get('project')

        if isinstance(project, dict):
            return project.get('version')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=f'Package manager (v: {get_version()})'
    )

    command_parser = parser.add_subparsers(
        dest='command',
        required=True
    )

    # generate --force
    gen_parser = command_parser.add_parser(
        'generate',
        help='generate tl and errors'
    )
    gen_parser.add_argument(
        '--force',
        action='store_true',
        help='skip prompt'
    )

    # clean --what [all, tl, errors] --force
    clean_parser = command_parser.add_parser(
        'clean',
        help='clean generated files'
    )
    clean_parser.add_argument(
        '--what',
        default='all',
        choices=['all', 'tl', 'errors'],
        help='specify what to clean'
    )
    clean_parser.add_argument(
        '--force',
        action='store_true',
        help='skip prompt'
    )

    args = parser.parse_args()

    if args.command == 'generate':
        
        if not args.force:
            existing = []

            if not is_empty_folder(TL_FOLDER):
                existing.append('TL')
    
            if not is_empty_folder(ERRORS_FOLDER):
                existing.append('Errors')

            if existing:
                folders = ' and '.join(existing)
                
                confirm = prompt(
                    f'The {folders} folder(s) already exist. '
                    'Do you want to continue?'
                )
                if not confirm:
                    sys.exit(0)

        with spinner('Generating ...'):
            generate_code()

    elif args.command == 'clean':
        if not args.force:

            confirm = prompt(f'Are you sure you want to clean {args.what!r}?')
            if not confirm:
                sys.exit(0)

        with spinner(f'Cleaning {args.what.title()!r} ...'):
            clean(args.what)
