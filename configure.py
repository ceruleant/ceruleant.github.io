from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Union, Tuple, Dict, Any


ROOT = Path(__file__).resolve().parent

StringArray = Union[str, List[str], Tuple[str]]


def normalize_string_array(arr: StringArray) -> List[str]:
    if isinstance(arr, str):
        return arr.split()
    elif isinstance(arr, (list, tuple)):
        return [normalize_string_array(e) for e in arr]
    else:
        raise ValueError(f"StringArray input not recognized: '{arr}'")


def normalize_optional_string_array(arr: Optional[StringArray]) -> List[str]:
    if arr is None:
        return []
    return normalize_string_array(arr)


@dataclass
class Rule:
    name: str
    command: str
    description: Optional[str]
    depfile: Optional[str]
    variables: Dict[str, str]

    def serialize(self) -> List[str]:
        lines: List[str] = list()
        lines.append(f"rule {self.name}")
        lines.append(f"  command = {self.command}")
        if self.description is not None:
            lines.append(f"  description = {self.description}")
        if self.depfile is not None:
            lines.append(f"  depfile = {self.depfile}")
        for key, var in self.variables.items():
            lines.append(f"  {key} = {var}")
        return lines


@dataclass
class Build:
    outputs: List[str]
    rule: str
    inputs: List[str]
    implicit: List[str]
    variables: Dict[str, str]

    def serialize(self) -> List[str]:
        lines: List[str] = list()
        lines.append(
            f"build {' '.join(self.outputs)}: {self.rule} {' '.join(self.inputs)} {' '.join(self.implicit)}"
        )
        for key, var in self.variables.items():
            lines.append(f"  {key} = {var}")
        return lines


class NinjaBuilder:
    def __init__(self):
        self._variables: Dict[str, str] = dict()
        self._rules: Dict[str, Rule] = dict()
        self._builds: List[Build] = list()

        self.var(
            name="root",
            value=ROOT,
        )
        self.rule(
            name="configure",
            command="python $root/configure.py",
            generator=1,
        )
        self.build(
            outputs="$root/build.ninja",
            rule="configure",
            implicit="$root/configure.py",
        )

    def var(self, *, name: str, value: Any):
        self._variables[name] = str(value)

    def rule(
        self,
        *,
        name: str,
        command: str,
        description: Optional[str] = None,
        depfile: Optional[str] = None,
        generator: bool = False,
    ):
        variables: Dict[str, str] = dict()
        if generator:
            variables["generator"] = "1"
        self._rules[name] = Rule(
            name=name,
            command=command,
            description=description,
            depfile=depfile,
            variables=variables,
        )

    def build(
        self,
        *,
        outputs: StringArray,
        rule: str,
        inputs: Optional[StringArray] = None,
        implicit: Optional[StringArray] = None,
        **kwargs,
    ):
        self._builds.append(
            Build(
                outputs=normalize_string_array(outputs),
                rule=rule,
                inputs=normalize_optional_string_array(inputs),
                implicit=normalize_optional_string_array(implicit),
                variables={k: str(v) for k, v in kwargs.items()},
            )
        )

    def serialize(self) -> str:
        lines: List[str] = list()
        for key, value in self._variables.items():
            lines.append(f"{key} = {value}")
        lines.append("")
        for rule in self._rules.values():
            lines.extend(rule.serialize())
        lines.append("")
        for build in self._builds:
            lines.extend(build.serialize())
        lines.append("")
        return "\n".join(lines)


def build_site(ninja: NinjaBuilder):
    pass


def main():
    ninja = NinjaBuilder()
    build_site(ninja)
    with ROOT.joinpath("build.ninja").open("w") as fo:
        fo.write(ninja.serialize())


if __name__ == "__main__":
    main()
