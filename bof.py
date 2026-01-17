import argparse
from cmds.index import run_index
from cmds.status import run_status
from cmds.scan import run_scan
from cmds.clean import run_clean

def main():
    parser = argparse.ArgumentParser(description="BOF: Box of Files - Deduplication Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Index Command
    idx_parser = subparsers.add_parser('index', help='Index files in current folder')
    idx_parser.add_argument('-p', '--path', default='.', help='Path to run the index')

    # Status Command
    subparsers.add_parser('status', help='Check status of current folder against index')

    # Scan Command
    scan_parser = subparsers.add_parser('scan', help='Scan for duplicates')
    scan_parser.add_argument('-l', '--level', type=int, default=1, help='Level of grouping')

    # Clean Command
    subparsers.add_parser('clean', help='Remove .bof directory')

    args = parser.parse_args()

    if args.command == 'index':
        run_index(args.path)
    elif args.command == 'status':
        run_status()
    elif args.command == 'scan':
        run_scan(args.level)
    elif args.command == 'clean':
        run_clean()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()