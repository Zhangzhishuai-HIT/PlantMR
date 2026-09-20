"""Project manifest model for the PlantMR 2.x platform."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import copy
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 compatibility
    import tomli as tomllib

from .errors import ProjectManifestError

_ALLOWED_TOP_LEVEL = {
    "project_name",
    "species",
    "assembly",
    "inputs",
    "analyses",
    "output_dir",
    "metadata",
    "extensions",
}
_REQUIRED = ("project_name", "species", "assembly", "inputs")


def _as_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectManifestError(f"{field} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class ProjectManifest:
    """Validated project configuration with manifest-relative path resolution."""

    manifest_path: Path
    project_name: str
    species: str
    assembly: str
    inputs: dict[str, str]
    analyses: tuple[str, ...] = ()
    output_dir: str = "runs"
    metadata: dict[str, Any] | None = None
    extensions: dict[str, Any] | None = None

    @classmethod
    def from_file(cls, path: str | Path) -> "ProjectManifest":
        manifest_path = Path(path).expanduser().resolve()
        if not manifest_path.exists():
            raise ProjectManifestError(f"manifest does not exist: {manifest_path}")
        try:
            data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ProjectManifestError(f"invalid TOML manifest {manifest_path}: {exc}") from exc
        return cls.from_dict(data, source_path=manifest_path)

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any], *, source_path: str | Path
    ) -> "ProjectManifest":
        if not isinstance(data, Mapping):
            raise ProjectManifestError("manifest must be a mapping")
        unknown = sorted(set(data) - _ALLOWED_TOP_LEVEL)
        if unknown:
            raise ProjectManifestError(f"unknown top-level manifest field(s): {', '.join(unknown)}")
        for field in _REQUIRED:
            if field not in data:
                raise ProjectManifestError(f"missing required manifest field: {field}")
        inputs = data["inputs"]
        if not isinstance(inputs, Mapping):
            raise ProjectManifestError("inputs must be a table/mapping")
        normalized_inputs: dict[str, str] = {}
        for role, value in inputs.items():
            role_name = _as_nonempty_string(role, "input role")
            if not isinstance(value, str):
                raise ProjectManifestError(f"inputs.{role_name} must be a string path")
            normalized_inputs[role_name] = value
        analyses = data.get("analyses", [])
        if not isinstance(analyses, list) or not all(isinstance(item, str) and item.strip() for item in analyses):
            raise ProjectManifestError("analyses must be a list of non-empty strings")
        output_dir = data.get("output_dir", "runs")
        output_dir = _as_nonempty_string(output_dir, "output_dir")
        metadata = data.get("metadata", {})
        extensions = data.get("extensions", {})
        if not isinstance(metadata, Mapping):
            raise ProjectManifestError("metadata must be a table/mapping")
        if not isinstance(extensions, Mapping):
            raise ProjectManifestError("extensions must be a table/mapping")
        return cls(
            manifest_path=Path(source_path).expanduser().resolve(),
            project_name=_as_nonempty_string(data["project_name"], "project_name"),
            species=_as_nonempty_string(data["species"], "species"),
            assembly=_as_nonempty_string(data["assembly"], "assembly"),
            inputs=normalized_inputs,
            analyses=tuple(item.strip() for item in analyses),
            output_dir=output_dir,
            metadata=copy.deepcopy(dict(metadata)),
            extensions=copy.deepcopy(dict(extensions)),
        )

    def resolve_input(self, role: str) -> Path:
        if role not in self.inputs:
            raise ProjectManifestError(f"input role is not declared: {role}")
        value = self.inputs[role]
        if not value:
            raise ProjectManifestError(f"input role has no path: {role}")
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = self.manifest_path.parent / path
        return path.resolve()

    def resolve_output_dir(self) -> Path:
        path = Path(self.output_dir).expanduser()
        if not path.is_absolute():
            path = self.manifest_path.parent / path
        return path.resolve()

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "species": self.species,
            "assembly": self.assembly,
            "inputs": dict(sorted(self.inputs.items())),
            "analyses": list(self.analyses),
            "output_dir": self.output_dir,
            "metadata": copy.deepcopy(self.metadata or {}),
            "extensions": copy.deepcopy(self.extensions or {}),
        }
