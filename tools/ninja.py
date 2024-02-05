from pathlib import Path
from typing import Dict, Any, IO, List
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
    name: str
    rule: str
    deps: List[str]
    overrides: Dict[str, str]

    def write(self, file: IO[str]):
        file.write(
            f"""\
build {self.name}: {self.rule} {' '.join(self.deps)}
"""
        )


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

    def build(self, *, name: str, rule: str, **kwargs):
        existing = self._targets.get(name)
        if existing is not None:
            raise RuntimeError(f"Duplicate target {name=}")
        self._targets[name] = Target(
            name=name,
            rule=rule,
            overrides=dict(),
            **kwargs,
        )

    def write(self, out: Path):
        with out.open("w") as file:
            for var, value in self._vars.items():
                file.write(f"{var} = {value}\n")
            for rule in self._rules.values():
                rule.write(file)
            for target in self._targets.values():
                target.write(file)
