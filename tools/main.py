from pathlib import Path
from argparse import ArgumentParser

from analyze import command_analyze
from template import command_template


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

    template = subparsers.add_parser(
        "template",
        help="Generate templated output",
    )
    template.add_argument(
        "--site",
        required=True,
        type=Path,
        help="site.json to load",
    )
    template.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to output to generate",
    )
    template.add_argument(
        "input",
        type=Path,
        help="input file to read",
    )
    template.add_argument(
        "--depfile",
        type=Path,
        default=None,
        help="Path to dependency depfile to generate",
    )

    args = parser.parse_args()
    if args.command == "analyze":
        command_analyze(
            inputs=args.input_paths,
            output=args.output,
        )
    elif args.command == "template":
        command_template(
            site_path=args.site,
            output_path=args.output,
            input_path=args.input,
            depfile_path=args.depfile,
        )


if __name__ == "__main__":
    main()
