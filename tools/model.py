from pathlib import Path
from typing import Dict, Any, List

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
    buildfiles: List[Path] = Field(default=list())
