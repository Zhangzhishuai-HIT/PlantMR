#!/usr/bin/env python3
"""Build a baseline-exposure, multi-environment Arabidopsis case study."""
import argparse, gzip, json
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm


def assoc(g, y, pcs):
    frame=pd.DataFrame({'g':g,'y':y}).join(pcs,how='inner').dropna()
    if len(frame)<50 or frame.g.nunique()<2 or frame.y.nunique()<2: return None
    x=sm.add_constant(frame[['g','PC1','PC2','PC3','PC4','PC5']],has_constant='add')
    fit=sm.OLS(frame.y.to_numpy(float),x.to_numpy(float)).fit()
    b=float(fit.params[1]); se=float(fit.bse[1])
    return {'beta':b,'se':se,'pval':float(fit.pvalues[1]),'n':int(len(frame)),'eaf':float(frame.g.mean())}

def allele_map(path, positions):
    out={}; want=set(map(int,positions))
    with gzip.open(path,'rt',errors='replace') as h:
        for line in h:
            if line.startswith('#'): continue
            f=line.rstrip().split('\t')
            if f[0]!='1': continue
            p=int(f[1])
            if p in want and len(f[3])==1 and len(f[4])==1 and f[3] in 'ACGT' and f[4] in 'ACGT': out[p]=(f[4],f[3])
    return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--gene',default='AT1G11560'); ap.add_argument('--outdir',default='data/real/arabidopsis_baseline_AT1G11560'); a=ap.parse_args(); root=Path(a.root).resolve(); out=root/a.outdir; out.mkdir(parents=True,exist_ok=True)
 z=np.load(root/'data/external/arabidopsis_1001genomes/AT1G11560_region_genotypes.npz'); pos=z['positions'].astype(int); G=z['genotypes'].astype(float); acc=z['accessions'].astype(str); idx={x:i for i,x in enumerate(acc)}
 pc=pd.read_csv(root/'data/external/arabidopsis_1001genomes/1001genomes_PC5.tsv',sep='\t',dtype={'accession_id':str}).set_index('accession_id').reindex(acc)
 amap=allele_map(root/'data/external/arabidopsis_1001genomes/alleles/intersection_991.vcf.gz',pos)
 expr=pd.read_csv(root/'data/external/arabidopsis_gse80744/GSE80744_AT1G11560_expression.tsv',sep='\t',dtype={'accession_id':str}).drop_duplicates('accession_id').set_index('accession_id')
 expr['value']=np.log1p(pd.to_numeric(expr['normalized_count'],errors='coerce')); expr=expr.join(pc,how='inner').dropna(subset=['value'])
 e_stats={}
 for r,p in enumerate(pos):
  p=int(p)
  if p not in amap: continue
  ids=[x for x in expr.index if x in idx]
  g=pd.Series(G[r,[idx[x] for x in ids]],index=ids)
  maf=min(float(g.mean()),1-float(g.mean()))
  if maf<0.05: continue
  s=assoc(g,expr.loc[ids,'value'],expr.loc[ids,['PC1','PC2','PC3','PC4','PC5']])
  if s is not None: e_stats[p]=s
  
 outcomes={}
 for env,fn,zv in [('10C','FT10_values.csv',-3.0),('16C','FT16_values.csv',3.0)]:
  ph=pd.read_csv(root/'data/external/arabidopsis_arapheno'/fn,dtype={'accession_id':str}); ph['accession_id']=ph.accession_id.astype(str); ph['phenotype_value']=pd.to_numeric(ph.phenotype_value,errors='coerce'); ph=ph.dropna(subset=['phenotype_value']).drop_duplicates('accession_id').set_index('accession_id').join(pc,how='inner').dropna(subset=['phenotype_value'])
  rows=[]
  for r,p in enumerate(pos):
   p=int(p)
   if p not in amap or p not in e_stats: continue
   ids=[x for x in ph.index if x in idx]; g=pd.Series(G[r,[idx[x] for x in ids]],index=ids); s=assoc(g,ph.loc[ids,'phenotype_value'],ph.loc[ids,['PC1','PC2','PC3','PC4','PC5']])
   if s is not None: outcomes.setdefault(env,{})[p]=(s,zv)
 exposure_rows=[]; outcome_rows=[]
 for env,zv in [('10C',-3.0),('16C',3.0)]:
  for p,s in e_stats.items():
   if env not in outcomes or p not in outcomes[env]: continue
   alt,ref=amap[p]; o,_=outcomes[env][p]; base={'SNP':'Chr1:%d'%p,'effect_allele':alt,'other_allele':ref,'environment':env,'environment_value':zv,'eaf':s['eaf'],'n':s['n']}
   exposure_rows.append({**base,'beta':s['beta'],'se':s['se'],'pval':s['pval'],'trait':'log1p(AT1G11560_normalized_count)'})
   outcome_rows.append({**base,'beta':o['beta'],'se':o['se'],'pval':o['pval'],'trait':'flowering_time_days'})
 ex=pd.DataFrame(exposure_rows).sort_values(['environment','SNP']); oy=pd.DataFrame(outcome_rows).sort_values(['environment','SNP']); complete=ex.groupby('SNP').environment.nunique(); keep=complete.index[complete==2]; ex=ex[ex.SNP.isin(keep)].reset_index(drop=True);oy=oy[oy.SNP.isin(keep)].reset_index(drop=True); ex.to_csv(out/'exposure.tsv',sep='\t',index=False);oy.to_csv(out/'outcome.tsv',sep='\t',index=False)
 meta={'species':'Arabidopsis thaliana','assembly':'TAIR10-compatible 1001 Genomes v3.1','gene':a.gene,'exposure':'GSE80744 normalized expression, log1p, local OLS adjusted for PC1-PC5; same baseline exposure copied to both outcome environments','outcome':'AraPheno FT10 and FT16, local OLS adjusted for PC1-PC5','environment_values':{'10C':-3.0,'16C':3.0},'expression_accessions':int(len(expr)),'complete_grid_snps':int(len(keep)),'allele_mapped_snps':int(len(amap)),'limitations':['Application/data-contract demonstration, not independent causal validation.','Expression and flowering phenotypes share accessions; sample-overlap covariance is not estimated.','This local OLS re-analysis is not a replacement for published LMM/SMR/HEIDI results.','Baseline exposure is not an environment-specific eQTL; the GxE slope refers to heterogeneity of the outcome MR relation across FT10/FT16.']}
 (out/'metadata.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'exposure_rows':len(ex),'outcome_rows':len(oy),'complete_snps':len(keep),'expression_accessions':len(expr),'p_min':float(ex.pval.min()) if len(ex) else None},indent=2))
if __name__=='__main__': main()
