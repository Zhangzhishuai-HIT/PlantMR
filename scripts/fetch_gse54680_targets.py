#!/usr/bin/env python3
"""Extract several target genes from GSE54680 processed expression files."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv, gzip, io, json, re, time
from pathlib import Path
from urllib.request import Request, urlopen

SAMPLE_PAGE = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={}&targ=self&form=text&view=quick"
UA = "PlantMR-data-audit/1.1"

def fetch(url, attempts=4):
    last = None
    for attempt in range(attempts):
        try:
            with urlopen(Request(url, headers={"User-Agent": UA}), timeout=90) as r:
                return r.read()
        except Exception as exc:
            last = exc; time.sleep(1.5*(attempt+1))
    raise RuntimeError("failed %s: %s" % (url,last))

def fields(text, key):
    return re.findall(r"^!Sample_%s = (.*)$" % re.escape(key), text, flags=re.MULTILINE)

def parse(gsm, targets):
    page=fetch(SAMPLE_PAGE.format(gsm)).decode('utf-8','replace')
    chars={}
    for item in fields(page,'characteristics_ch1'):
        if ':' in item:
            k,v=item.split(':',1); chars[k.strip()]=v.strip()
    files=fields(page,'supplementary_file_1') or fields(page,'supplementary_file')
    url=files[0]
    if url.startswith('ftp://'): url='https://'+url[6:]
    payload=fetch(url)
    values={t:('', '') for t in targets}
    wanted=set(targets)
    with gzip.GzipFile(fileobj=io.BytesIO(payload),mode='rb') as h:
        for raw in h:
            line=raw.decode('utf-8','replace').rstrip('\r\n')
            gene=line.split('\t',1)[0]
            if gene in wanted:
                f=line.split('\t')
                if len(f)>=3: values[gene]=(f[1],f[2])
                if all(values[t][0] != '' for t in targets): break
    if any(values[t][0] == '' for t in targets):
        missing=[t for t in targets if values[t][0]=='']
        raise RuntimeError('%s missing %s'%(gsm,','.join(missing)))
    base={"GSM":gsm,"sample_title":fields(page,'title')[0] if fields(page,'title') else '',
          "accession_number":chars.get('accession number',''),"accession_name":chars.get('accession name',''),
          "growth_temperature":chars.get('growth temperature',''),"tissue":chars.get('tissue',''),
          "developmental_stage":chars.get('develomental stage',chars.get('developmental stage','')),
          "processed_file":url}
    for t in targets:
        base[t+'_raw_counts'],base[t+'_RPKM']=values[t]
    return base

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--series-metadata',required=True); ap.add_argument('--outdir',required=True); ap.add_argument('--targets',required=True); ap.add_argument('--workers',type=int,default=8); a=ap.parse_args()
    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    text=Path(a.series_metadata).read_text(encoding='utf-8',errors='replace')
    gsms=sorted(set(re.findall(r'^!Series_sample_id = (GSM\d+)$',text,re.MULTILINE)))
    targets=[x.strip() for x in a.targets.split(',') if x.strip()]
    rows=[]; failures=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        fs={pool.submit(parse,g,targets):g for g in gsms}
        for i,f in enumerate(as_completed(fs),1):
            g=fs[f]
            try: rows.append(f.result())
            except Exception as e: failures.append({'GSM':g,'error':str(e)})
            if i%20==0 or i==len(gsms): print('processed %d/%d successes=%d failures=%d'%(i,len(gsms),len(rows),len(failures)),flush=True)
    rows.sort(key=lambda x:x['GSM'])
    cols=['GSM','sample_title','accession_number','accession_name','growth_temperature','tissue','developmental_stage','processed_file']
    for t in targets: cols += [t+'_raw_counts',t+'_RPKM']
    with (out/'GSE54680_target_expression.tsv').open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=cols,delimiter='\t'); w.writeheader(); w.writerows(rows)
    (out/'GSE54680_target_extraction_failures.json').write_text(json.dumps(failures,indent=2)+'\n',encoding='utf-8')
    if failures: raise SystemExit('%d failures'%len(failures))

if __name__=='__main__': main()
