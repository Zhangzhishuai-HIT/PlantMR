import json
from pathlib import Path

import pandas as pd

from plant_mr.cli import main


def _write_inputs(tmp_path: Path):
    exposure = pd.DataFrame(
        {
            "SNP": ["s1", "s2", "s3"],
            "effect_allele": ["A", "C", "G"],
            "other_allele": ["G", "T", "A"],
            "beta": [0.5, 0.4, 0.3],
            "se": [0.05, 0.05, 0.05],
            "pval": [1e-10, 1e-9, 1e-8],
            "eaf": [0.4, 0.3, 0.6],
        }
    )
    outcome = pd.DataFrame(
        {
            "SNP": ["s1", "s2", "s3"],
            "effect_allele": ["G", "C", "G"],
            "other_allele": ["A", "T", "A"],
            "beta": [0.2, 0.16, 0.12],
            "se": [0.04, 0.04, 0.04],
            "pval": [1e-4, 1e-4, 1e-4],
            "eaf": [0.6, 0.3, 0.6],
        }
    )
    metadata = {"species": "Zea mays", "assembly": "Zm-B73-REFERENCE-NAM-5.0", "environment": "WW"}
    exposure_path = tmp_path / "exposure.tsv"
    outcome_path = tmp_path / "outcome.tsv"
    metadata_path = tmp_path / "metadata.json"
    exposure.to_csv(exposure_path, sep="\t", index=False)
    outcome.to_csv(outcome_path, sep="\t", index=False)
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    return exposure_path, outcome_path, metadata_path


def test_cli_run_creates_reproducible_outputs(tmp_path):
    exposure, outcome, metadata = _write_inputs(tmp_path)
    output = tmp_path / "result"
    code = main([
        "run", "--exposure", str(exposure), "--outcome", str(outcome),
        "--metadata", str(metadata), "--outdir", str(output),
    ])
    assert code == 0
    assert (output / "harmonized.tsv").exists()
    assert (output / "leave_one_out.tsv").exists()
    assert (output / "results.json").exists()
    report = (output / "report.md").read_text(encoding="utf-8")
    assert "Zea mays" in report
    assert "LD" in report
    results = json.loads((output / "results.json").read_text(encoding="utf-8"))
    assert results["tool_version"] == "1.0.0"
    assert results["audit"]["selected"] == 3
    assert results["methods"][0]["method"] == "ivw_fixed"
    assert {item["method"] for item in results["methods"]} == {"ivw_fixed", "ivw_random", "mr_egger"}


def test_cli_stratified_runs_each_environment(tmp_path):
    exposure, outcome, metadata = _write_inputs(tmp_path)
    exp = pd.read_csv(exposure, sep="\t")
    out = pd.read_csv(outcome, sep="\t")
    exp = pd.concat([exp.assign(environment="WW"), exp.assign(environment="DS")], ignore_index=True)
    out = pd.concat([out.assign(environment="WW"), out.assign(environment="DS")], ignore_index=True)
    exp.to_csv(exposure, sep="\t", index=False)
    out.to_csv(outcome, sep="\t", index=False)
    output = tmp_path / "stratified"
    code = main([
        "run-stratified", "--exposure", str(exposure), "--outcome", str(outcome),
        "--metadata", str(metadata), "--outdir", str(output),
    ])
    assert code == 0
    result = json.loads((output / "results.json").read_text(encoding="utf-8"))
    assert result["environments"] == ["DS", "WW"]
    assert len(result["results"]) == 6
    assert (output / "environment_results.tsv").exists()


def test_cli_ld_matrix_is_applied_and_audited(tmp_path):
    exposure, outcome, metadata = _write_inputs(tmp_path)
    ld = tmp_path / "ld.tsv"
    ld.write_text("SNP\ts1\ts2\ts3\ns1\t1\t0.9\t0\ns2\t0.9\t1\t0\ns3\t0\t0\t1\n", encoding="utf-8")
    output = tmp_path / "ld_result"
    assert main([
        "run", "--exposure", str(exposure), "--outcome", str(outcome),
        "--metadata", str(metadata), "--ld-matrix", str(ld), "--outdir", str(output),
    ]) == 0
    result = json.loads((output / "results.json").read_text(encoding="utf-8"))
    assert result["audit"]["excluded_ld"] == 1
    assert result["audit"]["selected"] == 2
