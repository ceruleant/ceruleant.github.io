#!/usr/bin/env python
import sys
from pathlib import Path


def main():
    _, input_path, output_path = sys.argv
    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()
    deps = list(input_path.parent.rglob("*.py"))
    with output_path.open("w") as fo:
        fo.write(f"""\
#!/bin/bash
exec uv run {input_path} $@
""")
    output_path.chmod(0o755)

    dep_path = output_path.parent.joinpath(f"{output_path.name}.d")
    with dep_path.open("w") as fo:
        fo.write(f"{output_path}: {input_path} \\\n")
        for i, dep in enumerate(sorted(deps)):
            if i < (len(deps) - 1):
                fo.write(f"    {dep} \\\n")
            else:
                fo.write(f"    {dep} \n")


if __name__ == "__main__":
    main()
