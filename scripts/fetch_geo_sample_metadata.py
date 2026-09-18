#!/usr/bin/env python3
import argparse, csv, json, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

UA='PlantMR-data-audit/1.1'

def fetch(url):
    last=None
    for i in range(4):
        try:
            with urlopen(Request(url,headers={'User-Agent':UA}),timeout=90) as r: return r.read()
        except Exception as e:
            last=e; time.sleep(1.5*(i+1))
    raise RuntimeError(last)

def one(gsm):
    t=fetch('https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=%s&targ=self&form=text&view=quick'%gsm).decode('utf-8','replace')
    def onefield(k):
        m=re.search(r'^!Sample_%s = (.*)$'%re.escape(k),t,re.M); return m.group(1).strip() if m else ''
    chars={}
    for item in re.findall(r'^!Sample_characteristics_ch1 = (.*)$',t,re.M):
        if ':' in item: a,b=item.split(':',1); chars[a.strip()]=b.strip()
    return {'GSM':gsm,'sample_title':onefield('title'),'accession_id':chars.get('ecotype id',''),'cultivar':chars.get('cultivar',''),'tissue':chars.get('tissue',''),'developmental_stage':chars.get('developmental stage','')}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--series',required=True); ap.add_argument('--out',required=True); ap.add_argument('--workers',type=int,default=8); a=ap.parse_args()
 text=Path(a.series).read_text(errors='replace'); gsms=sorted(set(re.findall(r'^!Series_sample_id = (GSM\d+)$',text,re.M)))
 rows=[]; fails=[]
 with ThreadPoolExecutor(max_workers=a.workers) as pool:
  fs={pool.submit(one,g):g for g in gsms}
  for i,f in enumerate(as_completed(fs),1):
   try: rows.append(f.result())
   except Exception as e: fails.append({'GSM':fs[f],'error':str(e)})
   if i%50==0 or i==len(gsms): print('processed',i,'/',len(gsms),'ok',len(rows),'fail',len(fails),flush=True)
 rows.sort(key=lambda x:x['GSM'])
 with Path(a.out).open('w',encoding='utf-8',newline='') as h:
  w=csv.DictWriter(h,fieldnames=['GSM','sample_title','accession_id','cultivar','tissue','developmental_stage'],delimiter='\t'); w.writeheader(); w.writerows(rows)
 Path(str(a.out)+'.failures.json').write_text(json.dumps(fails,indent=2)+'\n')
 if fails: raise SystemExit('%d failures'%len(fails))
if __name__=='__main__': main()
