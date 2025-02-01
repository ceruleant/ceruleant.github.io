import sys
import json
import tomllib
from typing import Optional, List
from pathlib import Path
from typing import Dict, Any


def add_post_to_site(site: Dict[str, Any], post: Dict[str, Any], contents: str):
    posts = site.get("posts")
    if posts is None:
        posts = list()
        site["posts"] = posts

    # TODO: fill in post defaults
    # post.setdefault(...)
    posts.append(post)


def add_page_to_site(site: Dict[str, Any], page: Dict[str, Any], contents: str):
    pages = site.get("pages")
    if pages is None:
        pages = list()
        site["pages"] = pages

    # TODO: fill in page defaults
    # page.setdefault(...)
    pages.append(page)


def split_frontmatter(raw: str):
    fmraw, _, contents = raw.partition("\n---\n")
    return tomllib.loads(fmraw), contents


def add_path_to_site(site: Dict[str, Any], path: Path):
    with path.open() as stream:
        contents = stream.read()
    if path.name == "site.toml":
        with path.open("rb") as stream:
            site["site"] = tomllib.load(stream)
        return
    frontmatter, contents = split_frontmatter(contents)
    try:
        entry_type = frontmatter["type"]
    except KeyError as ke:
        raise RuntimeError(f"Entry at {path} does not have a type defined") from ke
    if entry_type == "post":
        add_post_to_site(site, frontmatter, contents)
    elif entry_type == "page":
        add_page_to_site(site, frontmatter, contents)
    else:
        raise ValueError(f"Unknown path/entry_type: {entry_type} in {path}")


def command_analyze(
    *,
    inputs: List[Path],
    output: Optional[Path],
):
    site = dict()
    for path in inputs:
        add_path_to_site(site, path)
    if output is None:
        json.dump(site, sys.stderr, indent=2)
    else:
        with output.open("w") as stream:
            json.dump(site, stream, indent=2, default=str)
