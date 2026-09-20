"""Execution layer for PlantMR 2.x analyses."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from ..analysis import analyze_pair
from ..report import write_report
from ..schema import read_summary
from .contracts import read_table
from .enrichment import go_enrichment
from .errors import ProjectManifestError
from .gwas import run_gwas
from .network import summarize_causal_network
from .project import ProjectManifest
from .qtl import run_qtl
from .smr import run_smr_heidi
from .validate import required_inputs_for_analysis, validate_project


def _new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_run_manifest(
    run_dir: Path,
    manifest: ProjectManifest,
    validation: dict[str, Any],
    config: dict[str, Any],
) -> None:
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "manifest": manifest.to_dict(),
                "validation": validation,
                "config": config,
                "outputs": sorted(path.name for path in run_dir.iterdir()),
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def run_project(
    manifest: ProjectManifest,
    *,
    analysis: str | None = None,
    run_id: str | None = None,
    p_threshold: float = 5e-8,
    f_threshold: float = 10.0,
    maf_threshold: float = 0.01,
    trait: str | None = None,
    feature_role: str = "expression",
    feature_id: str | None = None,
    network_p_threshold: float = 0.05,
) -> Path:
    selected_analysis = analysis or (manifest.analyses[0] if manifest.analyses else "ordinary-mr")
    if selected_analysis not in {"ordinary-mr", "mr", "gwas", "qtl", "smr", "go", "network"}:
        raise ProjectManifestError(
            f"analysis '{selected_analysis}' is not implemented yet; available: ordinary-mr, mr, gwas, qtl, smr, go, network"
        )
    required_inputs = required_inputs_for_analysis(
        selected_analysis,
        feature_role=feature_role,
    )
    validation = validate_project(manifest, required_inputs=required_inputs)
    if not validation["valid"]:
        raise ProjectManifestError("project validation failed: " + "; ".join(validation["errors"]))

    if selected_analysis == "gwas":
        for role in ("genotype", "phenotype"):
            raw_path = manifest.inputs.get(role, "")
            if not raw_path:
                raise ProjectManifestError(f"gwas requires inputs.{role}")
            if not manifest.resolve_input(role).exists():
                raise ProjectManifestError(f"gwas input does not exist: {role}")
    if selected_analysis == "qtl":
        if feature_role not in {"expression", "metabolite", "protein"}:
            raise ProjectManifestError("qtl --feature-role must be expression, metabolite or protein")
        for role in ("genotype", feature_role):
            raw_path = manifest.inputs.get(role, "")
            if not raw_path:
                raise ProjectManifestError(f"qtl requires inputs.{role}")
            if not manifest.resolve_input(role).exists():
                raise ProjectManifestError(f"qtl input does not exist: {role}")
    if selected_analysis == "network":
        if not manifest.inputs.get("edges"):
            raise ProjectManifestError("network requires inputs.edges")
        if not manifest.resolve_input("edges").exists():
            raise ProjectManifestError("network input does not exist: edges")
    if selected_analysis == "go":
        for role in ("go_annotation", "selected_features"):
            if not manifest.inputs.get(role):
                raise ProjectManifestError(f"go requires inputs.{role}")
            if not manifest.resolve_input(role).exists():
                raise ProjectManifestError(f"go input does not exist: {role}")

    run_name = run_id or _new_run_id()
    if not run_name or Path(run_name).name != run_name or run_name in {".", ".."}:
        raise ProjectManifestError("run_id must be a simple non-empty directory name")
    run_dir = manifest.resolve_output_dir() / run_name
    if run_dir.exists():
        raise ProjectManifestError(f"run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    if selected_analysis == "gwas":
        genotype = read_table(manifest.resolve_input("genotype"))
        phenotype = read_table(manifest.resolve_input("phenotype"))
        if trait is None:
            traits = sorted(phenotype["trait"].dropna().astype(str).unique()) if "trait" in phenotype else []
            if len(traits) != 1:
                raise ProjectManifestError("gwas requires --trait when phenotype contains zero or multiple traits")
            trait = traits[0]
        ploidy_raw = (manifest.metadata or {}).get("ploidy", "2")
        try:
            ploidy = float(ploidy_raw or 2)
        except (TypeError, ValueError) as exc:
            raise ProjectManifestError("metadata.ploidy must be numeric for gwas") from exc
        gwas = run_gwas(genotype, phenotype, trait=trait, ploidy=ploidy)
        gwas.to_csv(run_dir / "gwas.tsv", sep="\t", index=False)
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "gwas",
            "trait": trait,
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "model": "ordinary-least-squares",
            "covariates": [],
        }
        metadata = {
            "project_name": manifest.project_name,
            "species": manifest.species,
            "assembly": manifest.assembly,
            **(manifest.metadata or {}),
        }
        top = gwas.head(20).to_dict(orient="records")
        (run_dir / "results.json").write_text(
            json.dumps(
                {"analysis": "gwas", "trait": trait, "n_variants": int(len(gwas)), "top_hits": top},
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        lines = [
            "# PlantMR GWAS report",
            "",
            f"- Species: {metadata['species']}",
            f"- Assembly: {metadata['assembly']}",
            f"- Trait: {trait}",
            f"- Variants tested: {len(gwas)}",
            "",
            "This run uses ordinary least squares without population-structure or other covariates.",
            "Treat it as a transparent baseline, not as a mixed-model GWAS.",
            "",
            "## Top associations",
            "",
            "| Variant | Beta | SE | P value | N | MAF |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for row in gwas.head(20).itertuples(index=False):
            lines.append(
                f"| {row.variant_id} | {row.beta:.8g} | {row.se:.8g} | {row.pval:.8g} | "
                f"{row.n} | {row.maf:.6g} |"
            )
        (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis == "qtl":
        genotype = read_table(manifest.resolve_input("genotype"))
        molecular = read_table(manifest.resolve_input(feature_role))
        if feature_id is None:
            features = sorted(molecular["feature_id"].dropna().astype(str).unique()) if "feature_id" in molecular else []
            if len(features) != 1:
                raise ProjectManifestError("qtl requires --feature-id when the input contains zero or multiple features")
            feature_id = features[0]
        ploidy_raw = (manifest.metadata or {}).get("ploidy", "2")
        try:
            ploidy = float(ploidy_raw or 2)
        except (TypeError, ValueError) as exc:
            raise ProjectManifestError("metadata.ploidy must be numeric for qtl") from exc
        qtl = run_qtl(
            genotype,
            molecular,
            feature_id=feature_id,
            molecular_type=feature_role,
            ploidy=ploidy,
        )
        qtl.to_csv(run_dir / "qtl.tsv", sep="\t", index=False)
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "qtl",
            "feature_role": feature_role,
            "feature_id": feature_id,
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "model": "ordinary-least-squares",
            "covariates": [],
        }
        metadata = {
            "project_name": manifest.project_name,
            "species": manifest.species,
            "assembly": manifest.assembly,
            **(manifest.metadata or {}),
        }
        top = qtl.head(20).to_dict(orient="records")
        (run_dir / "results.json").write_text(
            json.dumps(
                {
                    "analysis": "qtl",
                    "feature_role": feature_role,
                    "feature_id": feature_id,
                    "n_variants": int(len(qtl)),
                    "top_hits": top,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        lines = [
            "# PlantMR QTL report",
            "",
            f"- Species: {metadata['species']}",
            f"- Assembly: {metadata['assembly']}",
            f"- Molecular layer: {feature_role}",
            f"- Feature: {feature_id}",
            f"- Variants tested: {len(qtl)}",
            "",
            "This run uses ordinary least squares without population-structure or other covariates.",
            "",
            "## Top associations",
            "",
            "| Variant | Beta | SE | P value | N | MAF |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for row in qtl.head(20).itertuples(index=False):
            lines.append(
                f"| {row.variant_id} | {row.beta:.8g} | {row.se:.8g} | {row.pval:.8g} | "
                f"{row.n} | {row.maf:.6g} |"
            )
        (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis == "network":
        edges = read_table(manifest.resolve_input("edges"))
        network, summary = summarize_causal_network(edges, p_threshold=network_p_threshold)
        network.to_csv(run_dir / "network.tsv", sep="\t", index=False)
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "network",
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "p_threshold": network_p_threshold,
            "interpretation": "edge-summary-not-causal-proof",
        }
        (run_dir / "results.json").write_text(
            json.dumps(
                {"analysis": "network", "summary": summary, "edges": network.to_dict(orient="records")},
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        lines = [
            "# PlantMR causal-edge network report",
            "",
            "This report summarizes supplied edges; it does not infer causality from the edge table.",
            f"- Significant edges: {summary['n_significant_edges']}",
            f"- Nodes: {summary['n_nodes']}",
            f"- Cycle detected: {summary['has_cycle']}",
            "",
            "| Source | Target | Beta | SE | P value | Q value |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for row in network.itertuples(index=False):
            lines.append(
                f"| {row.source} | {row.target} | {row.beta:.8g} | {row.se:.8g} | "
                f"{row.pval:.8g} | {row.qval:.8g} |"
            )
        (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis == "go":
        annotation = read_table(manifest.resolve_input("go_annotation"))
        selected = read_table(manifest.resolve_input("selected_features"))
        enrichment = go_enrichment(selected["feature_id"].astype(str), annotation)
        enrichment.to_csv(run_dir / "go_enrichment.tsv", sep="\t", index=False)
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "go",
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "universe": "all annotated features",
            "multiple_testing": "Benjamini-Hochberg",
        }
        (run_dir / "results.json").write_text(
            json.dumps(
                {"analysis": "go", "n_terms": int(len(enrichment)), "terms": enrichment.to_dict(orient="records")},
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        lines = [
            "# PlantMR GO enrichment report",
            "",
            "The default universe is all features present in the GO annotation file.",
            "Provide a tested universe explicitly through the Python API when that default is not appropriate.",
            "",
            "| GO term | Name | Overlap | Fold enrichment | P value | Q value |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for row in enrichment.itertuples(index=False):
            lines.append(
                f"| {row.go_term} | {row.term_name} | {row.overlap} | {row.fold_enrichment:.6g} | "
                f"{row.pval:.8g} | {row.qval:.8g} |"
            )
        (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis == "smr":
        exposure = read_summary(str(manifest.resolve_input("exposure")), "exposure").data
        outcome = read_summary(str(manifest.resolve_input("outcome")), "outcome").data
        if "feature_id" not in exposure.columns:
            raise ProjectManifestError("smr requires exposure.summary to contain a feature_id column")
        smr = run_smr_heidi(exposure, outcome, exposure_p_threshold=p_threshold)
        smr.to_csv(run_dir / "smr.tsv", sep="\t", index=False)
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "smr",
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "exposure_p_threshold": p_threshold,
            "heidi_p_threshold": 0.01,
            "sample_overlap_covariance": "not modeled",
        }
        (run_dir / "results.json").write_text(
            json.dumps(
                {
                    "analysis": "smr",
                    "n_features": int(len(smr)),
                    "results": smr.to_dict(orient="records"),
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        lines = [
            "# PlantMR SMR/HEIDI report",
            "",
            "SMR uses the strongest exposure QTL for each feature.",
            "HEIDI is a summary-data heterogeneity diagnostic; it is not a proof of colocalization.",
            "Effect alleles were aligned by SNP, but LD and sample-overlap covariance were not modeled.",
            "",
            "| Feature | Top SNP | SMR beta | SE | P value | HEIDI P value | Status |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
        for row in smr.itertuples(index=False):
            lines.append(
                f"| {row.feature_id} | {row.top_snp} | {row.smr_beta:.8g} | {row.smr_se:.8g} | "
                f"{row.smr_pval:.8g} | {row.heidi_pval:.8g} | {row.status} |"
            )
        (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    exposure = read_summary(str(manifest.resolve_input("exposure")), "exposure").data
    outcome = read_summary(str(manifest.resolve_input("outcome")), "outcome").data
    result = analyze_pair(
        exposure,
        outcome,
        p_threshold=p_threshold,
        f_threshold=f_threshold,
        maf_threshold=maf_threshold,
    )

    result.harmonized.data.to_csv(run_dir / "harmonized.tsv", sep="\t", index=False)
    result.selected.to_csv(run_dir / "selected_instruments.tsv", sep="\t", index=False)
    if result.leave_one_out is not None:
        result.leave_one_out.to_csv(run_dir / "leave_one_out.tsv", sep="\t", index=False)

    config: dict[str, Any] = {
        "tool_version": "2.0.0.dev0",
        "analysis": selected_analysis,
        "run_id": run_name,
        "manifest": str(manifest.manifest_path),
        "p_threshold": p_threshold,
        "f_threshold": f_threshold,
        "maf_threshold": maf_threshold,
    }
    metadata = {
        "project_name": manifest.project_name,
        "species": manifest.species,
        "assembly": manifest.assembly,
        **(manifest.metadata or {}),
    }
    warnings = list(validation["warnings"])
    if "ld" not in manifest.inputs or not manifest.inputs.get("ld"):
        warnings.append("No LD matrix was supplied; instrument selection did not perform LD clumping")
    write_report(
        run_dir,
        metadata=metadata,
        audit=result.audit,
        dropped=result.harmonized.dropped,
        methods=result.methods,
        warnings=warnings,
        config=config,
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "manifest": manifest.to_dict(),
                "validation": validation,
                "config": config,
                "outputs": sorted(path.name for path in run_dir.iterdir()),
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return run_dir
