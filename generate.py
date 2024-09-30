import os
import tomllib
import itertools
from functools import lru_cache
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent
BUILD = ROOT.joinpath("build")
TEMPLATES = ROOT.joinpath("templates")


class Page(BaseModel):
    title: str
    rel: str
    description: str
    modified: datetime
    source: str
    template: str
    html: Optional[str] = None


class Article(Page):
    pass


class Site(BaseModel):
    pages: list[Page]
    articles: list[Article]


def _load_pages(root: Path, site: Site):
    for entry in root.iterdir():
        try:
            with entry.joinpath("metadata.toml").open("rb") as fo:
                metadata = tomllib.load(fo)
                stat = os.fstat(fo.fileno())
        except FileNotFoundError:
            continue
        with entry.joinpath("source.md").open() as fo:
            mdsource = fo.read()
        page = Page(
            title=metadata["title"],
            modified=datetime.fromtimestamp(stat.st_mtime),
            source=mdsource,
            rel=metadata["rel"],
            description=metadata.get("description", ""),
            template=metadata["template"],
        )
        site.pages.append(page)


def _load_articles(root: Path, site: Site):
    pass


def analyze_site(root: Path) -> Site:
    site = Site(
        pages=list(),
        articles=list(),
    )
    _load_pages(root.joinpath("pages"), site)
    _load_articles(root.joinpath("articles"), site)
    return site


@lru_cache
def get_jinja_env():
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        undefined=StrictUndefined,
    )
    return env


def render_page(
    *,
    build_root: Path,
    site: Site,
    page: Page,
):
    j2 = get_jinja_env()
    target = build_root.joinpath(page.rel)
    template = j2.get_template(page.template)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w") as fo:
        fo.write(
            template.render(
                this=page,
                site=site,
            )
        )


def main():
    site = analyze_site(ROOT)
    for page in itertools.chain(site.pages, site.articles):
        render_page(
            build_root=BUILD,
            site=site,
            page=page,
        )


if __name__ == "__main__":
    main()
