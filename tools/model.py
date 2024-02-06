from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict

import toml

from pydantic import BaseModel, Field


class Page(BaseModel):
    name: str
    title: str
    tags: List[str]
    local_path: Path
    url: str
    description: str = ""

    def rewrite_relative_paths(self, root: Path):
        self.local_path = Path(f"$root/{self.local_path.relative_to(root).as_posix()}")

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
            url=f"$root/{name}",
        )


class SiteConfig(BaseModel):
    pages: Dict[str, Page] = Field(default=dict())
    tags: Dict[str, List[str]] = Field(default=dict())
    buildfiles: List[Path] = Field(default=list(), exclude=True)

    def rewrite_relative_paths(self, root: Path):
        for page in self.pages.values():
            page.rewrite_relative_paths(root)
        for i, path in enumerate(self.buildfiles):
            self.buildfiles[i] = Path(f"$root/{path.relative_to(root).as_posix()}")


def load_build_file(cfg: SiteConfig, path: Path):
    cfg.buildfiles.append(path)
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
