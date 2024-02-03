from pathlib import Path
from tools import repo
from typing import Dict

import toml
from pydantic import BaseModel, Field


class Page(BaseModel):
    pass


class SiteConfig(BaseModel):
    pages: Dict[str, Page] = Field(default=dict())


def load_build_file(cfg: SiteConfig, path: Path):
    with path.open() as file:
        data = toml.load(file)
    if includes := data.get("include"):
        assert isinstance(includes, list), f"includes must be a list of relative paths"
        for rel in includes:
            load_build_file(cfg, path.parent.joinpath(rel))
    print(f"{path=} {data=}")


def load_site_config() -> SiteConfig:
    cfg = SiteConfig()
    load_build_file(cfg, repo.ROOT.joinpath("build.toml"))
    return cfg


def main():
    cfg = load_site_config()


if __name__ == "__main__":
    main()
