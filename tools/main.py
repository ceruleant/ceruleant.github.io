from pathlib import Path
from argparse import ArgumentParser

from analyze import command_analyze


def main():
    parser = ArgumentParser("site tools")
    subparsers = parser.add_subparsers(dest="command")

    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze metadata and compile into site.json",
    )
    analyze.add_argument(
        "input_paths",
        nargs="+",
        type=Path,
    )
    analyze.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output json to write",
    )

    args = parser.parse_args()
    if args.command == "analyze":
        command_analyze(
            inputs=args.input_paths,
            output=args.output,
        )


if __name__ == "__main__":
    main()
