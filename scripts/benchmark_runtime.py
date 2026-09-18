#!/usr/bin/env python3
"""Record wall time and peak RSS for reproducibility examples."""
import subprocess
import time
from pathlib import Path

import psutil

root = Path(__file__).resolve().parents[1]
plantmr = "/home/user/zhangzhishuai/.local/share/mamba/envs/rnaseq_tpm/bin/plantmr"
commands = [
    ("validate", [plantmr, "validate", "--exposure", "examples/synthetic/exposure.tsv", "--outcome", "examples/synthetic/outcome.tsv", "--metadata", "examples/synthetic/metadata.json"]),
    ("gxe_synthetic", [plantmr, "run-gxe", "--exposure", "examples/synthetic/environment_exposure.tsv", "--outcome", "examples/synthetic/environment_outcome.tsv", "--metadata", "examples/synthetic/environment_metadata.json", "--outdir", "/tmp/plantmr_runtime_gxe"]),
    ("gxe_arabidopsis", [plantmr, "run-gxe", "--exposure", "data/real/arabidopsis_baseline_AT1G11560/exposure.tsv", "--outcome", "data/real/arabidopsis_baseline_AT1G11560/outcome.tsv", "--metadata", "data/real/arabidopsis_baseline_AT1G11560/metadata.json", "--ld-correlation", "data/real/arabidopsis_baseline_AT1G11560/ld_correlation.tsv", "--outdir", "/tmp/plantmr_runtime_real"]),
]
rows = ["task\treal_seconds\tpeak_rss_kb\treturn_code"]
for name, command in commands:
    start = time.perf_counter()
    process = subprocess.Popen(command, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    peak = 0
    root_process = psutil.Process(process.pid)
    while process.poll() is None:
        processes = [root_process] + root_process.children(recursive=True)
        for item in processes:
            try:
                peak = max(peak, item.memory_info().rss // 1024)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(0.01)
    stdout, stderr = process.communicate()
    elapsed = time.perf_counter() - start
    rows.append("%s\t%.4f\t%d\t%d" % (name, elapsed, peak, process.returncode))
    if process.returncode:
        raise SystemExit("%s failed:\n%s\n%s" % (name, stdout, stderr))
(root / "results/benchmarks/runtime.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
print("\n".join(rows))
