from pathlib import Path
from typing import Dict, Any, IO, List, Set
from dataclasses import dataclass


@dataclass
class Rule:
    name: str
    command: str
    overrides: Dict[str, str]
    generator: bool = False

    def write(self, file: IO[str]):
        file.write(
            f"""\
rule {self.name}
    command = {self.command}
    generator = {int(self.generator)}
"""
        )


@dataclass
class Target:
    names: List[str]
    rule: str
    deps: List[str]
    implicit_deps: List[str]
    overrides: Dict[str, str]

    def __hash__(self):
        return hash(tuple(self.names))

    def __eq__(self, other: "Target"):
        return sorted(self.names) == sorted(other.names)

    def __lt__(self, other: "Target"):
        return sorted(self.names) < sorted(other.names)

    def write(self, file: IO[str]):
        name_expr = " ".join(sorted(self.names))
        file.write(
            f"""\
build {name_expr}: {self.rule} {' '.join(self.deps)} | {' '.join(self.implicit_deps)}
"""
        )
        for key, value in self.overrides.items():
            file.write(f"  {key} = {value}\n")


class Ninja:
    def __init__(self):
        self._vars: Dict[str, str] = dict()
        self._rules: Dict[str, Rule] = dict()
        self._targets: Dict[str, Target] = dict()

    def var(self, name: str, value: Any):
        self._vars[name] = str(value)

    def rule(self, *, name: str, **kwargs):
        existing = self._rules.get(name)
        if existing is not None:
            raise RuntimeError(f"Duplicate rule {name=}")
        self._rules[name] = Rule(
            name=name,
            overrides=dict(),
            **kwargs,
        )

    def build(self, *, names: List[str], rule: str, **kwargs):
        for name in names:
            existing = self._targets.get(name)
            if existing is not None:
                raise RuntimeError(f"Duplicate target {name=}")
        kwargs.setdefault("overrides", {})
        kwargs.setdefault("implicit_deps", [])

        target = Target(
            names=names,
            rule=rule,
            **kwargs,
        )
        for name in names:
            self._targets[name] = target

    def write(self, out: Path):
        with out.open("w") as file:
            for var, value in self._vars.items():
                file.write(f"{var} = {value}\n")
            for rule in self._rules.values():
                rule.write(file)

            unique_targets: Set[Target] = set()
            for target in self._targets.values():
                unique_targets.add(target)
            print(unique_targets)
            for target in sorted(unique_targets):
                print(f"writing {target}")
                target.write(file)
