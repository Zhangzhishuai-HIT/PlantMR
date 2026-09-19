#!/usr/bin/env python3
"""Generate publication figures from frozen PlantMR results."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/figures'; OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
BLUE='#1f77b4'; ORANGE='#d95f02'; TEAL='#0F6B78'; GREY='#777777'; NAVY='#17365D'

# Figure 2: LD stress calibration.
ld=pd.read_csv(ROOT/'results/benchmarks/gxe_ld_stress/summary.tsv',sep='\t',keep_default_na=False)
fig,axs=plt.subplots(2,2,figsize=(7.5,5.7))
scenarios=['null','causal_gxe']; labels=['Null slope','True slope = 0.25']
colors=[TEAL,ORANGE]
for col,metric,title,ref,panel in [(0,'rejection_p05','Type-I error / power',0.05,'A'),(1,'coverage_95','95% CI coverage',0.95,'B')]:
 ax=axs[0,col]; x=np.arange(2); w=.34
 for i,cov in enumerate(['correct_ld_environment','diagonal_misspecified']):
  vals=[]
  for s in scenarios: vals.append(float(ld[(ld.scenario==s)&(ld.covariance==cov)][metric].iloc[0]))
  ax.bar(x+(i-.5)*w,vals,w,label='Correct covariance' if i==0 else 'Independence misspecified',color=colors[i],alpha=.85)
 ax.axhline(ref,color=GREY,ls='--',lw=1)
 ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0,1.08); ax.set_ylabel('Proportion'); ax.set_title(panel+'. '+title)
# causal bias and mean SE
ax=axs[1,0]; x=np.arange(2); w=.34
for i,cov in enumerate(['correct_ld_environment','diagonal_misspecified']):
 vals=[float(ld[(ld.scenario==s)&(ld.covariance==cov)].bias.iloc[0]) for s in scenarios]
 ax.bar(x+(i-.5)*w,vals,w,label='Correct covariance' if i==0 else 'Independence misspecified',color=colors[i],alpha=.85)
ax.axhline(0,color=GREY,lw=1); ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel('Slope bias'); ax.set_title('C. Bias under LD correlation')
ax=axs[1,1];
for i,cov in enumerate(['correct_ld_environment','diagonal_misspecified']):
 vals=[float(ld[(ld.scenario==s)&(ld.covariance==cov)].mean_se.iloc[0]) for s in scenarios]
 ax.bar(x+(i-.5)*w,vals,w,label='Correct covariance' if i==0 else 'Independence misspecified',color=colors[i],alpha=.85)
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylabel('Mean slope SE'); ax.set_title('D. Standard-error distortion')
handles=[plt.Rectangle((0,0),1,1,color=colors[0],alpha=.85),plt.Rectangle((0,0),1,1,color=colors[1],alpha=.85)]
fig.legend(handles,['Correct covariance','Independence misspecified'],loc='upper center',bbox_to_anchor=(.5,.985),ncol=2,frameon=False,fontsize=8)
fig.tight_layout(rect=[0,0,1,.90])
fig.savefig(OUT/'gxe_ld_stress.png',dpi=300); fig.savefig(OUT/'gxe_ld_stress.pdf'); plt.close(fig)

# Figure 3: real Arabidopsis case.
strat=pd.read_csv(ROOT/'results/real/arabidopsis_baseline_AT1G11560_stratified_all/environment_results.tsv',sep='\t')
fig,axs=plt.subplots(1,3,figsize=(10.5,3.5),gridspec_kw={'width_ratios':[1.35,1,1]},constrained_layout=True)
# A environment-specific estimates
ax=axs[0]
methods=[('ivw_fixed','Fixed IVW',BLUE),('ivw_random','Random IVW',ORANGE),('mr_egger','MR-Egger',TEAL)]
y=0
for env in ['10C','16C']:
 for method,label,color in methods:
  r=strat[(strat.environment==env)&(strat.method==method)].iloc[0]
  beta=float(r.beta); se=float(r.se)
  ax.errorbar(beta,y,xerr=1.96*se,fmt='o',color=color,capsize=3,label=label if env=='10C' else None)
  ax.text(-0.05,y,env,ha='right',va='center',fontsize=7)
  y+=1
 y+=.45
ax.axvline(0,color=GREY,lw=1); ax.set_yticks([]); ax.set_xlabel('Environment-specific MR estimate (95% CI)'); ax.set_title('A. Stratified comparator')
ax.legend(frameon=False,fontsize=7,loc='lower right')
# B GxE slope
ax=axs[1]
vals=[]
for name,path,color in [('Primary: LD only','results/real/arabidopsis_baseline_AT1G11560_diag/results.json',BLUE),('Sensitivity: proxy ENV corr','results/real/arabidopsis_baseline_AT1G11560_envproxy/results.json',ORANGE)]:
 d=json.loads((ROOT/path).read_text()); r=d['result']; vals.append((name,float(r['slope']),float(r['slope_se']),color))
for i,(name,b,se,color) in enumerate(vals):
 ax.errorbar(b,i,xerr=1.96*se,fmt='o',color=color,capsize=4); ax.text(0.01,i,name,transform=ax.get_yaxis_transform(),ha='left',va='center',fontsize=7)
ax.axvline(0,color=GREY,lw=1); ax.set_yticks([]); ax.set_xlabel('Environment slope (95% CI)'); ax.set_title('B. Covariance-aware slope')
# C audit
ax=axs[2]
counts={'Harmonized input':169,'P/F/MAF retained':48}
ax.bar(list(counts),list(counts.values()),color=[GREY,TEAL],alpha=.85)
ax.set_ylim(0,185); ax.set_ylabel('SNP count'); ax.set_title('C. Instrument audit'); ax.tick_params(axis='x',rotation=25)
for i,v in enumerate(counts.values()): ax.text(i,v+4,str(v),ha='center',fontsize=9)
fig.savefig(OUT/'arabidopsis_case.png',dpi=300); fig.savefig(OUT/'arabidopsis_case.pdf'); plt.close(fig)

# Figure 4: workflow schematic.
fig,ax=plt.subplots(figsize=(11,3.3)); ax.axis('off');
boxes=[('Plant inputs','Species • assembly\nTissue • stage\nEnvironment\nExposure + outcome stats'),('Harmonize','Effect alleles\nPalindromic variants\nGenome/trait metadata'),('QC + grid','p value • F • MAF\nComplete SNP ×\nenvironment grid\nLD provenance'),('Covariance-aware\nGLS','SNP + environment\ncorrelations\nDelta variance\nRank-aware Q'),('Audited outputs','IVW • Wald • Egger\nEnvironment slope\nJSON • TSV • Markdown')]
xs=np.linspace(.02,.82,len(boxes)); width=.15; y=.28; height=.42
for i,(title,body) in enumerate(boxes):
 x=xs[i]; patch=FancyBboxPatch((x,y),width,height,boxstyle='round,pad=0.015,rounding_size=0.02',facecolor='#EAF3F5' if i<4 else '#FFF2CC',edgecolor=TEAL if i<4 else ORANGE,linewidth=1.5,transform=ax.transAxes)
 ax.add_patch(patch); title_size=9 if i==3 else 10; body_size=7.5 if i in (0,2,3,4) else 8; body_y=y+.14 if i in (0,2,3,4) else y+.16; ax.text(x+width/2,y+height-.08,title,ha='center',va='center',fontweight='bold',color=NAVY,transform=ax.transAxes,fontsize=title_size,linespacing=1.05); ax.text(x+width/2,body_y,body,ha='center',va='center',transform=ax.transAxes,fontsize=body_size,linespacing=1.15)
 if i<len(boxes)-1:
  ax.add_patch(FancyArrowPatch((x+width+.01,y+height/2),(xs[i+1]-.01,y+height/2),arrowstyle='-|>',mutation_scale=14,color=GREY,transform=ax.transAxes))
ax.text(.5,.9,'PlantMR reproducible analysis workflow',ha='center',va='center',fontsize=14,fontweight='bold',color=NAVY,transform=ax.transAxes)
fig.savefig(OUT/'plantmr_workflow.png',dpi=300,bbox_inches='tight'); fig.savefig(OUT/'plantmr_workflow.pdf',bbox_inches='tight'); plt.close(fig)
print('generated',*[str(x) for x in [OUT/'gxe_ld_stress.png',OUT/'arabidopsis_case.png',OUT/'plantmr_workflow.png']])
