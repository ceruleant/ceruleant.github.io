import os
import json
from pathlib import Path
from tools import repo
from typing import Iterable, List

from tools.model import SiteConfig, load_build_file
from tools.ninja import Ninja


def python_tool_sources():
    for root, _, filenames in os.walk(repo.ROOT.joinpath("tools")):
        for fname in filenames:
            full = Path(root).joinpath(fname)
            if full.suffix == ".py":
                yield full


def load_site_config() -> SiteConfig:
    cfg = SiteConfig()
    load_build_file(cfg, repo.ROOT.joinpath("build.toml"))
    return cfg


def as_rel_paths(paths: Iterable[Path], root: Path):
    for path in paths:
        yield f"$root/{path.relative_to(root).as_posix()}"


def build_configure(ninja: Ninja, cfg: SiteConfig, root: Path):
    ninja.var("tools", "$root/tools")
    ninja.var("python", "PYTHONPATH=$root python")
    ninja.rule(
        name="configure",
        command="$python $root/tools/build.py",
        generator=True,
    )

    index_deps = list(as_rel_paths(python_tool_sources(), root=root)) + list(
        map(str, cfg.buildfiles)
    )

    index_path = "$builddir/site.json"

    ninja.build(
        names=[
            "$root/build.ninja",
            index_path,
        ],
        rule="configure",
        deps=index_deps,
    )

    return index_path


def build_pages(ninja: Ninja, cfg: SiteConfig, index: str):
    ninja.rule(
        name="page",
        command=f"$python $tools/page.py --name $pagename --source $in --output $out --index {index}",
    )
    for page in cfg.pages.values():
        ninja.build(
            names=[f"$builddir/{page.name}"],
            rule="page",
            deps=[page.local_path.as_posix()],
            implicit_deps=[index],
            overrides={"pagename": page.name},
        )


def generate_ninja_file(cfg: SiteConfig, out: Path):
    ninja = Ninja()
    root = out.parent
    ninja.var("root", root)
    ninja.var("builddir", "$root/build")
    index_path = build_configure(ninja, cfg, root)
    build_pages(ninja, cfg, index_path)
    ninja.write(out)


def generate_index(cfg: SiteConfig, path: Path):
    path.parent.mkdir(exist_ok=True, parents=True)
    with path.open("w") as file:
        # absurd, find something less silly to pretty print
        file.write(json.dumps(json.loads(cfg.json()), indent=2))
        file.write("\n")


def main():
    cfg = load_site_config()
    cfg.rewrite_relative_paths(repo.ROOT)
    generate_ninja_file(cfg, repo.ROOT.joinpath("build.ninja"))
    generate_index(cfg, repo.ROOT.joinpath("build", "site.json"))


if __name__ == "__main__":
    main()
