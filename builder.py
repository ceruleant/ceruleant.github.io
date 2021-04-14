import os
import shutil
import logging
import subprocess
from pathlib import Path
from datetime import datetime

import sass
import jinja2

DIR = Path(__file__).resolve().parent
SOURCE = DIR.joinpath("site")
BUILD = DIR.joinpath("build")
log = logging.getLogger("site")


def git_current_sha() -> str:
    result = subprocess.check_output(f"git -C {DIR.parent.as_posix()} rev-parse HEAD")
    return result.strip()


def git_current_branch() -> str:
    result = subprocess.check_output(
        f"git -C {DIR.parent.as_posix()} rev-parse --abbrev-ref HEAD"
    )
    return result.strip()


GIT_SHA = git_current_sha()
GIT_BRANCH = git_current_branch()


class Builder:
    def __init__(self, source: Path, build: Path, development: bool = True):
        self._source = source
        self._build = build
        self._html = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self._source),
            undefined=jinja2.StrictUndefined,
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )
        self._development = development

    def build_html(self, path: Path):
        rel = path.relative_to(self._source)
        dest = self._build.joinpath(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        template = self._html.get_template(rel.as_posix())
        now = datetime.utcnow()
        with open(dest, "w") as fd:
            fd.write(
                template.render(
                    year=now.year,
                    date=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    reflink=f"https://github.com/ceruleant/ceruleant.github.io/tree/{GIT_SHA}",
                    refname=f"{GIT_BRANCH}",
                )
            )
        log.info(f"[html] {rel}")

    def build_sass(self, path: Path):
        rel = path.relative_to(self._source)
        dest = self._build.joinpath(rel).with_suffix(".css")
        dest.parent.mkdir(parents=True, exist_ok=True)
        output = sass.compile(
            filename=path.as_posix(),
            output_style="compressed",
            include_paths=[self._source.as_posix()],
        )
        with open(dest, "w") as fd:
            fd.write(output)
        log.info(f"[css] {rel}")

    def build_copy(self, path: Path):
        rel = path.relative_to(self._source)
        dest = self._build.joinpath(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        log.info(f"[copy] {rel}")

    def build_path(self, path: Path):
        if path.suffix == ".html":
            return self.build_html(path)
        elif path.suffix == ".sass":
            return self.build_sass(path)
        return self.build_copy(path)

    def build(self):
        for root, dirs, files in os.walk(self._source):
            for name in files:
                if name.startswith("_"):
                    continue
                self.build_path(Path(root).joinpath(name))
            valid_dirs = set(filter(lambda d: not d.startswith("_"), dirs))
            dirs.clear()
            for d in valid_dirs:
                dirs.append(d)


def main():
    from argparse import ArgumentParser

    p = ArgumentParser()
    args = p.parse_args()
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    builder = Builder(SOURCE, BUILD)
    builder.build()


if __name__ == "__main__":
    main()
