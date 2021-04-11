import os
import json
import shutil
import logging
import asyncio
from typing import Dict
from pathlib import Path
from dataclasses import dataclass

import sass
import jinja2
from quart import Quart

DIR = Path(__file__).resolve().parent
SOURCE = DIR.joinpath("site")
BUILD = DIR.joinpath("build")
log = logging.getLogger("site")


@dataclass
class Snapshot:
    path: Path
    mtime: int
    size: int

    def __eq__(self, other: "Snapshot"):
        return (self.path, self.mtime, self.size) == (
            other.path,
            other.mtime,
            other.size,
        )

    @staticmethod
    def from_path(path: Path):
        stat = os.stat(path)
        return Snapshot(path, int(stat.st_mtime), stat.st_size)


class Manifest:
    def __init__(self, root: Path):
        self._root = root.resolve()
        self._entries = self._generate()

    def __iter__(self):
        return iter(self._entries.keys())

    def _generate(self):
        entries: Dict[Path, Snapshot] = dict()
        for root, dirs, files in os.walk(self._root):
            for name in files:
                full = Path(root).joinpath(name)
                snap = Snapshot.from_path(full)
                entries[snap.path] = snap
        return entries

    def is_dirty(self) -> bool:
        current = self._generate()
        matching = list(filter(lambda e: e in self._entries, current.keys()))
        for path in matching:
            existing = self._entries[path]
            new = current[path]
            if existing != new:
                self._entries = current
                return True
        # if they all match, we just need to return "dirty" if something
        # we were watching before has been deleted
        if len(matching) < len(self._entries):
            self._entries = current
            return True
        return False


class Builder:
    def __init__(self, source: Path, build: Path, development: bool = True):
        self._source = source
        self._build = build
        self._html = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self._source),
            undefined=jinja2.StrictUndefined,
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )

        self._development_scripts = list()
        if development:
            dev_scripts = [DIR.joinpath("dev", "development.mjs")]
            for path in dev_scripts:
                dest = BUILD.joinpath("js", path.name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
                self._development_scripts.append(f"/js/{path.name}")

    def build_html(self, path: Path):
        rel = path.relative_to(self._source)
        dest = self._build.joinpath(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        template = self._html.get_template(rel.as_posix())
        with open(dest, "w") as fd:
            fd.write(template.render(development_scripts=self._development_scripts))
        log.info(f"[html] {rel}")

    def build_sass(self, path: Path):
        rel = path.relative_to(self._source)
        dest = self._build.joinpath(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)

    def build_copy(self, path: Path):
        rel = path.relative_to(self._source)
        dest = self._build.joinpath(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        log.info(f"[copy] {rel}")

    def build(self, path: Path):
        if path.name.startswith("_"):
            return
        if path.suffix == ".html":
            return self.build_html(path)
        elif path.suffix == ".sass":
            return self.build_sass(path)
        return self.build_copy(path)


def serve_development():
    manifest = Manifest(SOURCE)
    builder = Builder(SOURCE, BUILD)
    for path in manifest:
        builder.build(path)

    app = Quart("ceruleant", static_folder=BUILD)
    sockets = set()

    @app.websocket("/feed")
    async def feed():
        q = asyncio.Queue()
        sockets.add(q)

        async def publish():
            while True:
                msg = await q.get()
                await websocket.send(msg)

        try:
            await asyncio.gather(publish(), websocket.recieve())
        except asyncio.CancelledError:
            sockets.remove(q)

    @app.route("/")
    async def index():
        return await app.send_static_file("index.html")

    @app.route("/<path:filename>")
    async def static_file(filename: str):
        return await app.send_static_file(filename)

    async def watch_for_updates():
        while True:
            await asyncio.sleep(1.0)
            if manifest.is_dirty():
                log.info(f"Change detected, rebuilding")
                for path in manifest:
                    builder.build(path)
                msg = json.dumps({"type": "rebuild"})
                for q in sockets:
                    q.put_nowait(msg)
                log.info(f"rebuild event published.")

    async def main():
        await asyncio.gather(watch_for_updates(), app.run_task())

    asyncio.run(main())


def build_production():
    raise NotImplementedError


def main():
    from argparse import ArgumentParser

    p = ArgumentParser()
    p.add_argument("command", choices={"build", "serve"}, help="Build command")
    args = p.parse_args()
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    if args.command == "build":
        build_production()
    elif args.command == "serve":
        serve_development()
    else:
        raise ValueError(f"Unexpected command: {args.command}")


if __name__ == "__main__":
    main()
