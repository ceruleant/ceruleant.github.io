import json
from typing import Dict, Any
from pathlib import Path
from argparse import ArgumentParser

import commonmark


def render_page(
    *,
    source: Path,
    dest: Path,
    metadata: Dict[str, Any],
    index: Dict[str, Any],
):
    with open(dest, "w") as file:
        pass


def main():
    p = ArgumentParser()
    p.add_argument(
        "--name",
        type=str,
        required=True,
    )
    p.add_argument(
        "--source",
        type=Path,
        required=True,
    )
    p.add_argument(
        "--output",
        required=True,
        type=Path,
    )
    p.add_argument(
        "--index",
        type=Path,
        required=True,
        help="index.json to load Page metadata",
    )
    args = p.parse_args()
    with args.index.open() as file:
        index = json.load(file)
    render_page(
        source=args.source,
        dest=args.output,
        metadata=index["pages"][args.name],
        index=index,
    )


if __name__ == "__main__":
    main()
