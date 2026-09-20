#!/usr/bin/env python3
"""Plot the shared-input PlantMR versus summary-MR-GxE benchmark."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/figures'; OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'results/benchmarks/mr_gxe_head_to_head'
raw=pd.read_csv(BASE/'replicates.tsv',sep='\t',keep_default_na=False)
summary=pd.read_csv(BASE/'summary.tsv',sep='\t',keep_default_na=False)
labels={
 'constant_null_directional_pleiotropy':'Null causal\n+ pleiotropy',
 'constant_effect_no_pleiotropy':'Constant effect\n(no pleiotropy)',
 'constant_effect_directional_pleiotropy':'Constant effect\n+ pleiotropy',
 'environment_effect_heterogeneity':'Environment\neffect heterogeneity',
}
order=list(labels)
colors={'PlantMR':'#0F6B78','summary_MR_GxE':'#D95F02'}
pretty={'PlantMR':'PlantMR','summary_MR_GxE':'Summary-data MR-GxE'}
fig,axs=plt.subplots(1,2,figsize=(11.0,4.6),gridspec_kw={'width_ratios':[1.45,1]},constrained_layout=True)
# Target-defined calibration.
ax=axs[0]; x=np.arange(len(order)); offsets={'PlantMR':-.16,'summary_MR_GxE':.16}
for method in ['PlantMR','summary_MR_GxE']:
 for i,scenario in enumerate(order):
  s=summary[(summary.scenario==scenario)&(summary.method==method)].iloc[0]
  if str(s.target_defined).lower() not in ('true','1'):
   continue
  g=raw[(raw.scenario==scenario)&(raw.method==method)&(raw.failure=='')]
  mean=float(g.estimate.mean()); sem=float(g.estimate.std(ddof=1)/np.sqrt(len(g)))
  ax.errorbar(i+offsets[method],mean,yerr=1.96*sem,fmt='o',capsize=3,color=colors[method],ms=6)
  ax.text(i+offsets[method],mean+(0.025 if mean>=0 else -0.035),f'{mean:.3f}',ha='center',va='bottom' if mean>=0 else 'top',fontsize=7,color=colors[method])
 # no legend handles yet
for method in ['PlantMR','summary_MR_GxE']:
 ax.scatter([],[],color=colors[method],label=pretty[method])
# target lines only where defined, annotate below x labels via notes
ax.axhline(0,color='#777777',lw=.8)
ax.set_xticks(x); ax.set_xticklabels([labels[s] for s in order],fontsize=8)
ax.set_ylabel('Mean estimate (error bars: 95% CI of simulation mean)')
ax.set_title('A. Calibration at each method’s target')
ax.legend(frameon=False,fontsize=8,loc='upper left')
ax.text(.02,.02,'Only method/scenario pairs with a defined target are scored.',transform=ax.transAxes,fontsize=7,color='#555555')
# Out-of-target outputs.
ax=axs[1]; ax.set_facecolor('#F8F9FA')
out=[]
for _,s in summary.iterrows():
 if str(s.target_defined).lower() not in ('true','1'):
  out.append((f"{labels[s.scenario]}\n{pretty[s.method]}",float(s.mean_estimate),colors[s.method]))
y=np.arange(len(out))
ax.barh(y,[v for _,v,_ in out],color=[c for _,_,c in out],alpha=.85)
ax.axvline(0,color='#777777',lw=.8)
ax.set_yticks(y); ax.set_yticklabels([n for n,_,_ in out],fontsize=8)
ax.set_xlabel('Mean reported estimate')
ax.set_title('B. Out-of-target diagnostics\n(not scored as calibration)')
ax.set_xlim(-.18,1.38)
for i,(_,v,_) in enumerate(out): ax.text(v+(0.025 if v>=0 else -0.025),i,f'{v:.3f}',va='center',ha='left' if v>=0 else 'right',fontsize=8)
ax.text(.02,.03,'No defined target: no bias or coverage score.',transform=ax.transAxes,fontsize=7,color='#555555')
fig.suptitle('Shared-input comparison: PlantMR and summary-data MR-GxE',fontsize=13,fontweight='bold',color='#17365D')
fig.savefig(OUT/'mr_gxe_head_to_head.png',dpi=300); fig.savefig(OUT/'mr_gxe_head_to_head.pdf'); plt.close(fig)
print('generated',OUT/'mr_gxe_head_to_head.png',OUT/'mr_gxe_head_to_head.pdf')
