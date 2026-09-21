"""Execution layer for PlantMR 2.x analyses."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..analysis import analyze_pair
from ..gxe import gxe_ivw, select_gxe_instruments
from ..harmonize import harmonize_summary
from ..report import write_report
from ..schema import read_summary, validate_summary
from .annotation import annotate_variants
from .contracts import read_table
from .causal import coloc_abf, run_mvmr
from .enrichment import go_enrichment
from .errors import ProjectManifestError
from .gwas import run_gwas
from .gwas_models import run_matrix_gwas
from .genotype import as_genotype_matrix, qc_genotype, read_genotype
from .network import build_mr_network, identify_network_modules, summarize_causal_network
from .phenotype import as_phenotype_matrix, merge_environments, qc_phenotype
from .plotting import plot_manhattan, plot_mr_forest, plot_network, plot_qq
from .project import ProjectManifest
from .provenance import input_receipts
from .qtl import run_qtl
from .sal import detect_sal
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
                "input_receipts": input_receipts(manifest),
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
    model: str = "ols",
    mlm_lambda: float = 1.0,
    qc_maf_threshold: float = 0.05,
    missing_threshold: float = 0.10,
    impute: str | None = None,
    transform: str = "none",
    module_min_nodes: int = 5,
    sal_p_lead: float = 5e-8,
    sal_p_secondary: float = 1e-5,
    sal_r2: float = 0.2,
    sal_window: int = 500_000,
    annotation_flank: int = 2_000,
    environment_method: str = "mean",
) -> Path:
    selected_analysis = analysis or (manifest.analyses[0] if manifest.analyses else "ordinary-mr")
    if selected_analysis not in {"ordinary-mr", "mr", "stratified-mr", "environment-heterogeneity", "gwas", "qtl", "smr", "coloc", "mvmr", "go", "network", "genotype-qc", "phenotype-qc", "environment-merge", "sal", "annotate"}:
        raise ProjectManifestError(
            f"analysis '{selected_analysis}' is not implemented yet; available: ordinary-mr, mr, stratified-mr, environment-heterogeneity, gwas, qtl, smr, coloc, mvmr, go, network, genotype-qc, phenotype-qc, environment-merge, sal, annotate"
        )
    required_inputs = required_inputs_for_analysis(
        selected_analysis,
        feature_role=feature_role,
    )
    validation = validate_project(
        manifest,
        required_inputs=required_inputs,
        allow_multi_exposure=selected_analysis == "mvmr",
        allow_environment_repeats=selected_analysis in {"stratified-mr", "environment-heterogeneity"},
    )
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

    if selected_analysis == "genotype-qc":
        genotype = read_genotype(manifest.resolve_input("genotype"))
        qc = qc_genotype(
            genotype,
            maf_threshold=qc_maf_threshold,
            variant_missing_threshold=missing_threshold,
            sample_missing_threshold=missing_threshold,
            impute=impute,
            ploidy=float((manifest.metadata or {}).get("ploidy", 2) or 2),
        )
        qc.matrix.to_csv(run_dir / "genotype_qc.tsv", sep="\t", index_label="sample_id")
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "genotype-qc",
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "maf_threshold": qc_maf_threshold,
            "missing_threshold": missing_threshold,
            "impute": impute or "none",
        }
        (run_dir / "results.json").write_text(json.dumps({"analysis": "genotype-qc", "audit": qc.audit}, indent=2) + "\n", encoding="utf-8")
        (run_dir / "report.md").write_text(
            "# PlantMR genotype QC report\n\n"
            + "\n".join(f"- {key}: {value}" for key, value in sorted(qc.audit.items()))
            + "\n",
            encoding="utf-8",
        )
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis == "phenotype-qc":
        phenotype = as_phenotype_matrix(read_table(manifest.resolve_input("phenotype")))
        qc = qc_phenotype(
            phenotype,
            missing_threshold=missing_threshold,
            impute=impute,
            transform=transform,
        )
        qc.matrix.to_csv(run_dir / "phenotype_qc.tsv", sep="\t", index_label="sample_id")
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "phenotype-qc",
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "missing_threshold": missing_threshold,
            "impute": impute or "none",
            "transform": transform,
        }
        (run_dir / "results.json").write_text(json.dumps({"analysis": "phenotype-qc", "audit": qc.audit}, indent=2) + "\n", encoding="utf-8")
        (run_dir / "report.md").write_text(
            "# PlantMR phenotype QC report\n\n"
            + "\n".join(f"- {key}: {value}" for key, value in sorted(qc.audit.items()))
            + "\n",
            encoding="utf-8",
        )
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis == "environment-merge":
        phenotype = read_table(manifest.resolve_input("phenotype"))
        merged = merge_environments(phenotype, method=environment_method)
        merged.to_csv(run_dir / "environment_merged.tsv", sep="\t", index=False)
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "environment-merge",
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "method": environment_method,
        }
        (run_dir / "results.json").write_text(json.dumps({"analysis": "environment-merge", "method": environment_method, "rows": int(len(merged))}, indent=2) + "\n", encoding="utf-8")
        (run_dir / "report.md").write_text("# PlantMR multi-environment phenotype merge\n\n" + merged.to_string(index=False) + "\n", encoding="utf-8")
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis in {"sal", "annotate"}:
        gwas = read_table(manifest.resolve_input("gwas"))
        if selected_analysis == "sal":
            ld = None
            if manifest.inputs.get("ld"):
                ld_table = read_table(manifest.resolve_input("ld"))
                if "variant_id" not in ld_table.columns:
                    raise ProjectManifestError("LD input must have variant_id as its first column")
                ld = ld_table.set_index("variant_id")
            sal = detect_sal(
                gwas,
                ld_matrix=ld,
                p_lead=sal_p_lead,
                p_secondary=sal_p_secondary,
                r2_threshold=sal_r2,
                window=sal_window,
            )
            sal.to_csv(run_dir / "sal.tsv", sep="\t", index=False)
            config = {
                "tool_version": "2.0.0.dev0",
                "analysis": "sal",
                "run_id": run_name,
                "manifest": str(manifest.manifest_path),
                "p_lead": sal_p_lead,
                "p_secondary": sal_p_secondary,
                "r2_threshold": sal_r2,
                "window": sal_window,
            }
            (run_dir / "results.json").write_text(json.dumps({"analysis": "sal", "n_sal": int(len(sal))}, indent=2) + "\n", encoding="utf-8")
            (run_dir / "report.md").write_text(
                "# PlantMR significantly associated loci report\n\n"
                "SALs are lead-SNP regions defined by the supplied p-value/window/LD thresholds; they are not automatically causal genes.\n\n"
                + sal.to_string(index=False)
                + "\n",
                encoding="utf-8",
            )
        else:
            genes = read_table(manifest.resolve_input("gene_annotation"))
            annotated = annotate_variants(gwas, genes, flank=annotation_flank)
            annotated.to_csv(run_dir / "variant_annotation.tsv", sep="\t", index=False)
            config = {
                "tool_version": "2.0.0.dev0",
                "analysis": "annotate",
                "run_id": run_name,
                "manifest": str(manifest.manifest_path),
                "flank": annotation_flank,
            }
            (run_dir / "results.json").write_text(json.dumps({"analysis": "annotate", "n_variants": int(len(annotated))}, indent=2) + "\n", encoding="utf-8")
            (run_dir / "report.md").write_text(
                "# PlantMR variant annotation report\n\n"
                "Annotation is positional prioritization and does not prove gene function or causality.\n\n"
                + annotated.to_string(index=False)
                + "\n",
                encoding="utf-8",
            )
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis == "stratified-mr":
        exposure = read_table(manifest.resolve_input("exposure"))
        outcome = read_table(manifest.resolve_input("outcome"))
        if "environment" not in exposure.columns or "environment" not in outcome.columns:
            raise ProjectManifestError("stratified-mr requires environment in exposure and outcome")
        environments = sorted(set(exposure["environment"].astype(str)) & set(outcome["environment"].astype(str)))
        if not environments:
            raise ProjectManifestError("stratified-mr found no shared environments")
        rows = []
        for environment in environments:
            exp = exposure.loc[exposure["environment"].astype(str) == environment].drop(columns=["environment"])
            out = outcome.loc[outcome["environment"].astype(str) == environment].drop(columns=["environment"])
            analysis_result = analyze_pair(
                validate_summary(exp, f"exposure[{environment}]").data,
                validate_summary(out, f"outcome[{environment}]").data,
                p_threshold=p_threshold,
                f_threshold=f_threshold,
                maf_threshold=maf_threshold,
            )
            rows.extend({"environment": environment, **method} for method in analysis_result.methods)
        result_table = pd.DataFrame(rows).sort_values(["environment", "method"], kind="mergesort")
        result_table.to_csv(run_dir / "environment_results.tsv", sep="\t", index=False)
        config = {"tool_version": "2.0.0.dev0", "analysis": "stratified-mr", "run_id": run_name, "manifest": str(manifest.manifest_path)}
        (run_dir / "results.json").write_text(json.dumps({"analysis": "stratified-mr", "environments": environments, "results": rows}, indent=2) + "\n", encoding="utf-8")
        (run_dir / "report.md").write_text("# PlantMR environment-stratified MR report\n\n" + result_table.to_string(index=False) + "\n", encoding="utf-8")
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis == "environment-heterogeneity":
        exposure = read_table(manifest.resolve_input("exposure"))
        outcome = read_table(manifest.resolve_input("outcome"))
        if not {"environment", "environment_value"}.issubset(exposure.columns) or "environment" not in outcome.columns:
            raise ProjectManifestError("environment-heterogeneity requires environment and environment_value in exposure")
        environments = sorted(set(exposure["environment"].astype(str)) & set(outcome["environment"].astype(str)))
        chunks = []
        for environment in environments:
            exp = exposure.loc[exposure["environment"].astype(str) == environment].drop(columns=["environment", "environment_value"])
            out = outcome.loc[outcome["environment"].astype(str) == environment].drop(columns=["environment"])
            harmonized = harmonize_summary(exp, out).data
            value = float(exposure.loc[exposure["environment"].astype(str) == environment, "environment_value"].iloc[0])
            harmonized["SNP"] = harmonized["SNP"].astype(str)
            harmonized["environment"] = environment
            harmonized["environment_value"] = value
            chunks.append(harmonized.rename(columns={"exposure_beta": "exposure_beta", "outcome_beta": "outcome_beta"}))
        table = pd.concat(chunks, ignore_index=True)
        table["exposure_pval"] = 1e-12
        table["eaf"] = table["eaf"].fillna(0.5)
        selected, audit = select_gxe_instruments(table, p_threshold=p_threshold, f_threshold=f_threshold, maf_threshold=maf_threshold)
        if selected.empty:
            raise ProjectManifestError("environment-heterogeneity found no complete-grid instruments")
        result = gxe_ivw(selected)
        config = {"tool_version": "2.0.0.dev0", "analysis": "environment-heterogeneity", "run_id": run_name, "manifest": str(manifest.manifest_path)}
        (run_dir / "gxe_results.json").write_text(json.dumps({"result": result.as_dict(), "audit": audit}, indent=2) + "\n", encoding="utf-8")
        (run_dir / "results.json").write_text(json.dumps({"analysis": "environment-heterogeneity", **result.as_dict()}, indent=2) + "\n", encoding="utf-8")
        (run_dir / "report.md").write_text("# PlantMR environment heterogeneity report\n\n" + "\n".join(f"- {k}: {v}" for k, v in result.as_dict().items()) + "\n", encoding="utf-8")
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

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
        covariates = read_table(manifest.resolve_input("covariates")) if manifest.inputs.get("covariates") else None
        kinship = None
        if manifest.inputs.get("kinship"):
            kinship_table = read_table(manifest.resolve_input("kinship"))
            if "sample_id" not in kinship_table.columns:
                raise ProjectManifestError("kinship input must have sample_id as its first column")
            kinship = kinship_table.set_index("sample_id")
        long_format = (
            {"sample_id", "variant_id", "dosage"}.issubset(genotype.columns)
            and {"sample_id", "trait", "value"}.issubset(phenotype.columns)
        )
        if model == "ols" and long_format and covariates is None and kinship is None:
            gwas = run_gwas(genotype, phenotype, trait=trait, ploidy=ploidy)
            gwas["model"] = "ols"
            gwas["n_covariates"] = 0
        else:
            gwas = run_matrix_gwas(
                as_genotype_matrix(genotype),
                as_phenotype_matrix(phenotype),
                trait=trait,
                covariates=covariates,
                kinship=kinship,
                model=model,
                mlm_lambda=mlm_lambda,
                ploidy=ploidy,
            )
        gwas.to_csv(run_dir / "gwas.tsv", sep="\t", index=False)
        plot_manhattan(gwas, run_dir / "manhattan")
        plot_qq(gwas, run_dir / "qq")
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "gwas",
            "trait": trait,
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "model": model,
            "covariates": sorted(covariates.columns.tolist()) if covariates is not None else [],
            "kinship": bool(kinship is not None),
            "mlm_lambda": mlm_lambda if model in {"mlm", "gemma_mlm"} else None,
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
                {"analysis": "gwas", "trait": trait, "model": model, "n_variants": int(len(gwas)), "top_hits": top},
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
            f"This run uses the {model} model.",
            "The mlm/gemma_mlm path is kinship-aware GLS with the supplied covariance and is not a wrapper around the GEMMA binary.",
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
        mr_network = build_mr_network(edges, p_threshold=network_p_threshold)
        modules = identify_network_modules(mr_network, min_nodes=module_min_nodes)
        network.to_csv(run_dir / "network.tsv", sep="\t", index=False)
        mr_network.to_csv(run_dir / "mr_network.tsv", sep="\t", index=False)
        modules.to_csv(run_dir / "network_modules.tsv", sep="\t", index=False)
        plot_network(mr_network.rename(columns={"node_a": "source", "node_b": "target"}), run_dir / "network")
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "network",
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "p_threshold": network_p_threshold,
            "interpretation": "edge-summary-not-causal-proof",
            "module_min_nodes": module_min_nodes,
        }
        (run_dir / "results.json").write_text(
            json.dumps(
                {
                    "analysis": "network",
                    "summary": summary,
                    "edges": network.to_dict(orient="records"),
                    "mr_network_edges": int(len(mr_network)),
                    "modules": modules.to_dict(orient="records"),
                },
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

    if selected_analysis == "coloc":
        exposure = read_summary(str(manifest.resolve_input("exposure")), "exposure").data.rename(columns={"SNP": "variant_id"})
        outcome = read_summary(str(manifest.resolve_input("outcome")), "outcome").data.rename(columns={"SNP": "variant_id"})
        result = coloc_abf(exposure, outcome)
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "coloc",
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "method": "Wakefield-ABF",
        }
        (run_dir / "results.json").write_text(json.dumps({"analysis": "coloc", **result}, indent=2) + "\n", encoding="utf-8")
        (run_dir / "coloc.tsv").write_text(
            "hypothesis\tposterior\n" + "\n".join(f"PP{i}\t{result[f'PP{i}']:.12g}" for i in range(5)) + "\n",
            encoding="utf-8",
        )
        (run_dir / "report.md").write_text(
            "# PlantMR colocalization report\n\n"
            "Wakefield approximate-BF posterior probabilities are reported for H0-H4. "
            "PP4 supports a shared variant under the supplied priors; it is not experimental validation.\n\n"
            + "\n".join(f"- {key}: {value}" for key, value in result.items())
            + "\n",
            encoding="utf-8",
        )
        _write_run_manifest(run_dir, manifest, validation, config)
        return run_dir

    if selected_analysis == "mvmr":
        exposure = read_table(manifest.resolve_input("exposure")).rename(columns={"SNP": "variant_id"})
        outcome = read_summary(str(manifest.resolve_input("outcome")), "outcome").data.rename(columns={"SNP": "variant_id"})
        if "exposure_id" not in exposure.columns:
            raise ProjectManifestError("mvmr requires exposure input column exposure_id")
        result = run_mvmr(exposure, outcome)
        result.to_csv(run_dir / "mvmr.tsv", sep="\t", index=False)
        config = {
            "tool_version": "2.0.0.dev0",
            "analysis": "mvmr",
            "run_id": run_name,
            "manifest": str(manifest.manifest_path),
            "method": "inverse-variance-weighted-mvmr",
        }
        (run_dir / "results.json").write_text(json.dumps({"analysis": "mvmr", "results": result.to_dict(orient="records")}, indent=2) + "\n", encoding="utf-8")
        (run_dir / "report.md").write_text(
            "# PlantMR multivariable MR report\n\n"
            "The model estimates conditional effects using the supplied exposure summary statistics. "
            "Exposure covariance and horizontal pleiotropy are not automatically resolved.\n\n"
            + result.to_string(index=False)
            + "\n",
            encoding="utf-8",
        )
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
    plot_mr_forest(pd.DataFrame(result.methods), run_dir / "mr_forest")
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "manifest": manifest.to_dict(),
                "validation": validation,
                "config": config,
                "input_receipts": input_receipts(manifest),
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
