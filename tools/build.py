from pathlib import Path
from tools import repo
from typing import Dict, Set, Any

import toml
from pydantic import BaseModel, Field


class Page(BaseModel):
    name: str
    title: str
    tags: Set[str]
    local_path: Path
    url: str

    @staticmethod
    def from_obj(path: Path, obj: Dict[str, Any]):
        local_path = path.joinpath(obj["source"])
        name = obj.get("name")
        if name is None:
            name = local_path.stem
        if not name.endswith(".html"):
            name += ".html"
        return Page(
            name=name,
            title=obj["title"],
            tags=set(obj.get("tags", [])),
            local_path=local_path,
            url="",
        )


class SiteConfig(BaseModel):
    pages: Dict[str, Page] = Field(default=dict())


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

    print(f"{path=} {data=}")


def load_site_config() -> SiteConfig:
    cfg = SiteConfig()
    load_build_file(cfg, repo.ROOT.joinpath("build.toml"))
    return cfg


def main():
    cfg = load_site_config()
    print(cfg)


if __name__ == "__main__":
    main()
