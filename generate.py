import os
import time
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
import tomllib
from collections import defaultdict
from functools import lru_cache
from typing import Callable, Tuple, Dict, Any, Set, Iterable, List, Optional
from concurrent.futures import ThreadPoolExecutor, Future

import commonmark
import sass
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent
BUILD = ROOT.joinpath("build")
TEMPLATES = ROOT.joinpath("templates")
CSS = ROOT.joinpath("css")


@lru_cache
def get_jinja_env():
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        undefined=StrictUndefined,
    )
    return env


def parse_annotated_markdown(source: Path) -> Tuple[Dict[str, Any], str]:
    with source.open() as fo:
        raw = fo.read()
        toml_source, _, md_source = raw.partition("\n---\n")

    toml = tomllib.loads(toml_source)
    html = commonmark.commonmark(md_source)
    return toml, html


def build_page(
    *,
    source: str,
    dest: Path,
    template: str,
    context: Dict[str, Any],
):
    html = commonmark.commonmark(source)
    # TODO: jinja2 env should not allow arbitrary FS paths given our dep
    # tracking model
    j2 = get_jinja_env()
    with dest.open("w") as fo:
        fo.write(j2.get_template(template).render(body=html, **context))


def build_scss(*, source: Path, dest: Path):
    css = sass.compile(
        filename=source.as_posix(),
        source_comments=True,
        include_paths={CSS.as_posix()},
    )
    with dest.open("w") as fo:
        fo.write(css)


@dataclass
class BuildTarget:
    dest: Path
    source: Path
    rule: Callable[..., None]
    deps: Set[Path]
    context: Dict[str, Any]

    def __hash__(self):
        return hash(self.dest)

    def __eq__(self, other: "BuildTarget"):
        return self.dest == other.dest

    def is_dirty(self, mtimes: Dict[Path, int]) -> bool:
        self_mtime = mtimes.get(self.dest)
        if self_mtime is None:
            return True
        for dep in self.deps:
            if mtimes[dep] > self_mtime:
                return True
        return False

    def deps_satisfied(self, mtimes: Dict[Path, int]):
        for dep in self.deps:
            if dep not in mtimes:
                return False
        return True


class Builder:
    def __init__(self):
        self._targets: Dict[Path, BuildTarget] = dict()
        self._templates: Dict[str, str] = dict()
        self._template_paths: Set[Path] = set()
        self._scss_paths: Set[Path] = set()

    def _add_target(self, target: BuildTarget):
        if target.dest in self._targets:
            raise RuntimeError(f"Duplicate targets to path '{target.dest}'")
        self._targets[target.dest] = target

    def template(self, path: Path):
        self._template_paths.add(path)
        with path.open() as fo:
            self._templates[path.name] = fo.read()

    def css(self, *, dest: str, source: Path):
        deps = {source, *self._scss_paths}
        self._add_target(
            BuildTarget(
                dest=BUILD.joinpath(dest),
                source=source,
                deps=deps,
                rule=build_scss,
                context={"source": source},
            )
        )

    def page(self, spec: Path):
        meta, source = parse_annotated_markdown(spec)
        # everything gets the generate.py source added as a dep
        deps: Set[Path] = {spec}
        template = meta["template"]
        full = TEMPLATES.joinpath(template)
        deps.add(full)
        deps.update(self._template_paths)
        self._add_target(
            BuildTarget(
                dest=BUILD.joinpath(meta["path"]),
                source=spec,
                deps=deps,
                rule=build_page,
                context={
                    "source": source,
                    "template": template,
                    "context": {
                        "meta": meta,
                    },
                },
            )
        )

    def build(self, *, force_rebuild: bool, parallelism: int):
        downstream: Dict[Path, Set[Path]] = defaultdict(set)
        building: Dict[Path, Any] = dict()
        mtimes: Dict[Path, int] = dict()
        to_build: Set[BuildTarget] = set()

        for target in self._targets.values():
            try:
                info = os.stat(target.dest)
                mtimes[target.dest] = info.st_mtime_ns
            except FileNotFoundError:
                pass
            for dep in target.deps:
                downstream[dep].add(target.dest)
                if dep not in self._targets:
                    try:
                        info = os.stat(dep)
                        mtimes[dep] = info.st_mtime_ns
                    except FileNotFoundError as e:
                        raise ValueError(
                            f"File '{dep}' is expected as a dependency but does not exist."
                        ) from e

        for dest in sorted(self._targets.keys()):
            target = self._targets[dest]
            if target.deps_satisfied(mtimes) and (
                force_rebuild or target.is_dirty(mtimes)
            ):
                to_build.add(target)

        paths_finished: List[Path] = list()
        targets_built: Set[BuildTarget] = set()
        with ThreadPoolExecutor(max_workers=parallelism) as pool:
            while len(building) or len(to_build):
                while len(building) < parallelism and len(to_build):
                    target = next(iter(to_build))
                    print(f"building {target.dest}")
                    to_build.remove(target)
                    building[target.dest] = pool.submit(
                        target.rule,
                        dest=target.dest,
                        **target.context,
                    )
                for path, fut in building.items():
                    if fut.done():
                        paths_finished.append(path)
                if len(paths_finished):
                    for path in paths_finished:
                        targets_built.add(self._targets[path])
                        fut = building[path]
                        fut.result()
                        info = os.stat(path)
                        mtimes[path] = info.st_mtime_ns
                        del building[path]
                        for dep in downstream[path]:
                            to_build.add(self._targets[dep])
                    paths_finished.clear()
                else:
                    time.sleep(0.01)

        print(f"Built {len(targets_built)} dirty targets.")


def build():
    builder = Builder()

    builder.template(TEMPLATES.joinpath("base.html"))
    builder.template(TEMPLATES.joinpath("page.html"))

    builder.css(
        dest="main.css",
        source=CSS.joinpath("main.scss"),
    )

    builder.page(ROOT.joinpath("pages", "index.md"))

    return builder


def serve():
    pass


def build_once(force_rebuild: bool):
    builder = build()
    builder.build(
        force_rebuild=force_rebuild,
        parallelism=1,
    )


def main():
    p = ArgumentParser()
    p.add_argument(
        "mode",
        choices=["serve", "build"],
        type=str,
    )

    p.add_argument(
        "--force-rebuild",
        default=False,
        action="store_true",
        help="In build mode, force a complete rebuild.",
    )

    args = p.parse_args()
    {"serve": serve, "build": build_once,}[args.mode](
        force_rebuild=args.force_rebuild,
    )


if __name__ == "__main__":
    main()
