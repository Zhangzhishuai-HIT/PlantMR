#!/usr/bin/env python3
"""Extract one Arabidopsis target gene from GSE54680 processed files."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import gzip
import io
import json
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen


SAMPLE_PAGE = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={}&targ=self&form=text&view=quick"
UA = "PlantMR-data-audit/1.1"


def fetch(url, attempts=4):
    last = None
    for attempt in range(attempts):
        try:
            req = Request(url, headers={"User-Agent": UA})
            with urlopen(req, timeout=90) as response:
                return response.read()
        except Exception as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("failed %s: %s" % (url, last))


def field(text, name):
    match = re.search(r"^!Sample_%s = (.*)$" % re.escape(name), text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def all_fields(text, name):
    return re.findall(r"^!Sample_%s = (.*)$" % re.escape(name), text, flags=re.MULTILINE)


def parse_sample(gsm, target):
    page = fetch(SAMPLE_PAGE.format(gsm)).decode("utf-8", "replace")
    chars = {}
    for item in all_fields(page, "characteristics_ch1"):
        if ":" in item:
            key, value = item.split(":", 1)
            chars[key.strip()] = value.strip()
    supplement = field(page, "supplementary_file_1")
    if not supplement:
        supplement = field(page, "supplementary_file")
    if supplement.startswith("ftp://"):
        supplement = "https://" + supplement[6:]
    payload = fetch(supplement)
    target_row = None
    with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as handle:
        for raw in handle:
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if line.startswith(target + "\t"):
                target_row = line.split("\t")
                break
    if target_row is None:
        raise RuntimeError("target %s absent from %s" % (target, gsm))
    if len(target_row) < 3:
        raise RuntimeError("unexpected target row for %s: %r" % (gsm, target_row))
    return {
        "GSM": gsm,
        "sample_title": field(page, "title"),
        "accession_number": chars.get("accession number", ""),
        "accession_name": chars.get("accession name", ""),
        "growth_temperature": chars.get("growth temperature", ""),
        "tissue": chars.get("tissue", ""),
        "developmental_stage": chars.get("develomental stage", chars.get("developmental stage", "")),
        "target_gene": target,
        "raw_counts": target_row[1],
        "RPKM": target_row[2],
        "processed_file": supplement,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-metadata", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--target", default="AT1G11560")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    series_text = Path(args.series_metadata).read_text(encoding="utf-8", errors="replace")
    gsms = sorted(set(re.findall(r"^!Series_sample_id = (GSM\d+)$", series_text, flags=re.MULTILINE)))
    if not gsms:
        raise SystemExit("no GSM sample IDs in series metadata")
    rows = []
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(parse_sample, gsm, args.target): gsm for gsm in gsms}
        for index, future in enumerate(as_completed(futures), 1):
            gsm = futures[future]
            try:
                rows.append(future.result())
            except Exception as exc:
                failures.append({"GSM": gsm, "error": str(exc)})
            if index % 20 == 0 or index == len(gsms):
                print("processed %d/%d; successes=%d failures=%d" % (index, len(gsms), len(rows), len(failures)), flush=True)
    rows.sort(key=lambda row: row["GSM"])
    columns = ["GSM", "sample_title", "accession_number", "accession_name", "growth_temperature",
               "tissue", "developmental_stage", "target_gene", "raw_counts", "RPKM", "processed_file"]
    with (outdir / "GSE54680_AT1G11560_expression.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    (outdir / "GSE54680_extraction_failures.json").write_text(
        json.dumps(failures, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (outdir / "GSE54680_extraction_metadata.json").write_text(json.dumps({
        "series": "GSE54680",
        "target": args.target,
        "input_samples": len(gsms),
        "successes": len(rows),
        "failures": len(failures),
        "workers": args.workers,
        "source": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE54680",
    }, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("%d sample extractions failed; see failure JSON" % len(failures))


if __name__ == "__main__":
    main()
