from pathlib import Path
import json
from typing import Iterable, Mapping


def write_report(outdir: Path, metadata: Mapping, audit: Mapping, dropped: Mapping,
                 methods: Iterable[Mapping], warnings: Iterable[str], config: Mapping) -> None:
    payload = {
        "tool_version": str(config.get("tool_version", "1.1.0")),
        "metadata": dict(metadata),
        "audit": dict(audit),
        "harmonization_dropped": dict(dropped),
        "methods": [dict(item) for item in methods],
        "warnings": list(warnings),
        "config": dict(config),
    }
    (outdir / "results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# PlantMR report",
        "",
        "## Plant metadata",
        "",
    ]
    for key in sorted(metadata):
        lines.append(f"- {key}: {metadata[key]}")
    lines += ["", "## Instrument audit", ""]
    for key in sorted(audit):
        lines.append(f"- {key}: {audit[key]}")
    lines += ["", "## Harmonization exclusions", ""]
    for key in sorted(dropped):
        lines.append(f"- {key}: {dropped[key]}")
    lines += ["", "## MR results", "", "| Method | Beta | SE | P value | SNPs |", "|---|---:|---:|---:|---:|"]
    for result in methods:
        lines.append(
            f"| {result['method']} | {result['beta']:.8g} | {result['se']:.8g} | "
            f"{result['pval']:.8g} | {result['nsnp']} |"
        )
    lines += ["", "## Warnings", ""]
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None")
    lines += ["", "## Reproducibility", "", "```json", json.dumps(dict(config), sort_keys=True), "```", ""]
    (outdir / "report.md").write_text("\n".join(lines), encoding="utf-8")
