import json
from pathlib import Path
from tools import repo
from collections import defaultdict
from typing import Dict, Set, List

import toml

from tools.model import SiteConfig, Page
from tools.ninja import Ninja


def load_build_file(cfg: SiteConfig, path: Path):
    with path.open() as file:
        data = toml.load(file)
    if includes := data.get("include"):
        assert isinstance(includes, list), f"includes must be a list of relative paths"
        for rel in includes:
            load_build_file(cfg, path.parent.joinpath(rel))

    if pages := data.get("page"):
        assert isinstance(
            pages, list
        ), f"pages must be a [[page]] (multiple entry) section"
        for page_info in pages:
            assert isinstance(page_info, dict)
            page = Page.from_obj(path, page_info)
            if existing := cfg.pages.get(page.name):
                raise ValueError(f"Page by path {page.name} already exists: {existing}")
            cfg.pages[page.name] = page

    tags: Dict[str, Set[str]] = defaultdict(set)
    for page in cfg.pages.values():
        for tag in page.tags:
            tags[tag].add(page.name)
    cfg.tags = {t: sorted(pages) for t, pages in tags.items()}
    return cfg


def load_site_config() -> SiteConfig:
    cfg = SiteConfig()
    load_build_file(cfg, repo.ROOT.joinpath("build.toml"))
    return cfg


def as_rel_paths(paths: List[Path], root: Path):
    for path in paths:
        yield f"$root/{path.relative_to(root).as_posix()}"


def generate_ninja_file(cfg: SiteConfig, out: Path):
    ninja = Ninja()
    root = out.parent
    ninja.var("root", root)
    ninja.rule(
        name="configure",
        command="python tools/build.py",
        generator=True,
    )
    ninja.build(
        target="$root/build.ninja",
        rule="configure",
        deps=as_rel_paths(cfg.buildfile_paths(), root=root),
    )

    ninja.write(out)


def main():
    cfg = load_site_config()
    # print(json.dumps(json.loads(cfg.json()), indent=2))
    generate_ninja_file(cfg, repo.ROOT.joinpath("build.ninja"))


if __name__ == "__main__":
    main()
