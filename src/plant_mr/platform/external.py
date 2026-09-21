"""Safe adapters for optional external genomics executables."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import subprocess
from typing import Sequence


@dataclass(frozen=True)
class ExternalCommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    outputs: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


def run_external_command(
    command: Sequence[str],
    *,
    cwd: str | Path,
    expected_outputs: Sequence[str | Path] = (),
    timeout: int | None = None,
) -> ExternalCommandResult:
    """Run a user-specified executable without a shell and verify outputs."""
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("external command must be a non-empty sequence of strings")
    cwd = Path(cwd).resolve()
    if not cwd.is_dir():
        raise ValueError(f"external command cwd does not exist: {cwd}")
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd),
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"external executable not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"external command timed out after {timeout}s: {command[0]}") from exc
    if completed.returncode != 0:
        raise RuntimeError(
            f"external command failed with exit code {completed.returncode}: {completed.stderr.strip()}"
        )
    outputs = []
    for raw in expected_outputs:
        path = Path(raw)
        if not path.is_absolute():
            path = cwd / path
        path = path.resolve()
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"external command did not produce expected output: {path}")
        outputs.append(str(path))
    return ExternalCommandResult(tuple(command), completed.returncode, completed.stdout, completed.stderr, tuple(outputs))


def gemma_mlm_command(
    executable: str,
    *,
    bfile: str,
    phenotype: str,
    kinship: str,
    output_prefix: str,
    covariates: str | None = None,
) -> list[str]:
    command = [executable, "-bfile", bfile, "-k", kinship, "-p", phenotype, "-lmm", "4", "-o", output_prefix]
    if covariates:
        command.extend(["-c", covariates])
    return command
