import json
from pathlib import Path
from tools import repo
from collections import defaultdict
from typing import Dict, Any, List, Set

import toml
from pydantic import BaseModel, Field


class Page(BaseModel):
    name: str
    title: str
    tags: List[str]
    local_path: Path
    url: str
    description: str = ""

    @staticmethod
    def from_obj(path: Path, obj: Dict[str, Any]):
        local_path = path.parent.joinpath(obj["source"])
        if not local_path.exists():
            raise RuntimeError(f"Page path {path} does not exist")
        name = obj.get("name")
        if name is None:
            name = local_path.stem
        if not name.endswith(".html"):
            name += ".html"
        return Page(
            name=name,
            title=obj["title"],
            tags=sorted(set(map(lambda t: t.lower(), obj.get("tags", [])))),
            local_path=local_path,
            url=f"<root>/{name}",
        )


class SiteConfig(BaseModel):
    pages: Dict[str, Page] = Field(default=dict())
    tags: Dict[str, List[str]] = Field(default=dict())


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


def main():
    cfg = load_site_config()
    print(json.dumps(json.loads(cfg.json()), indent=2))


if __name__ == "__main__":
    main()
