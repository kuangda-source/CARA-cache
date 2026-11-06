#!/usr/bin/env python3
"""Paper figure from all four accepted Window24 calibration scenes."""
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    source=ROOT/'reports/wc_drop1_window24_full24_complete_results_analysis_20261019.json'
    data=json.loads(source.read_text())
    assert data['status']=='WINDOW24_ACCEPTED_ALL16_FRAMES_AND_CONTRASTS_RECOMPUTED_OFFLINE'
    for name in ('capture','acceptance'):
        assert hashlib.sha256((ROOT/data[name+'_ref']).read_bytes()).hexdigest()==data[name+'_sha256']
    methods=('S25-C','S25-A1','S25-A3')
    scenes=list(dict.fromkeys(r['scene'] for r in data['rows']))
    assert len(scenes)==4
    values={m:[] for m in methods}
    for scene in scenes:
        for m in methods:
            row=[r for r in data['rows'] if r['scene']==scene and r['method']==m]
            assert len(row)==1 and row[0]['frames']==93 and row[0]['counts']['DD']==25
            values[m].append(row[0]['LPIPS'])
    means={m:math.fsum(v)/4 for m,v in values.items()}
    for m in methods:values[m].append(means[m])
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,ax=plt.subplots(figsize=(7.2,3.8),layout='constrained')
    colors=('#8c96a6','#d58a29','#277b82');labels=('Cache (C)','One correction (A1)','Continuous correction (A3)')
    for j,(m,color,label) in enumerate(zip(methods,colors,labels)):
        x=[i+(j-1)*.23 for i in range(5)]
        ax.bar(x,values[m],width=.21,color=color,label=label,zorder=3)
    ax.set_xticks(range(5),['AV28','Human199','Misc','AV51','Mean'])
    ax.set_ylabel('Endpoint LPIPS vs. Native (lower is better)')
    ax.set_ylim(0,.125);ax.set_yticks([0,.02,.04,.06,.08,.10,.12])
    ax.yaxis.grid(True,color='#e5e7eb',linewidth=.65,zorder=0)
    ax.spines[['top','right']].set_visible(False)
    ax.axvline(3.5,color='#c9cdd3',linestyle=':',linewidth=1)
    ax.legend(loc='upper center',ncol=3,frameon=False,bbox_to_anchor=(.5,1.13),fontsize=9)
    gain_c=100*(1-means['S25-A3']/means['S25-C']);gain_a=100*(1-means['S25-A3']/means['S25-A1'])
    ax.text(4,.105,f'A3 vs C: −{gain_c:.1f}%\nA3 vs A1: −{gain_a:.1f}%',ha='center',va='center',fontsize=9,color='#236b71')
    fig.supxlabel('Same 25 dense updates and refresh locations · 4 calibration scenes · seed 0',fontsize=9)
    out=ROOT/'paper/figures/cara_window24_mechanism_r1_20261022';out.mkdir(parents=True,exist_ok=True)
    for suffix in ('png','pdf','svg'):fig.savefig(out/('matched25D_readout.'+suffix),dpi=240,bbox_inches='tight')
    svg=out/'matched25D_readout.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)
    proof=dict(source_ref=str(source.relative_to(ROOT)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        methods=list(methods),scenes=scenes,prompt_equal_means=means,A3_vs_C_reduction_percent=gain_c,A3_vs_A1_reduction_percent=gain_a,
        all_four_scenes_included=True,independent_test=False,new_experiments=0,
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.suffix in ('.png','.pdf','.svg')})
    (out/'provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(dict(output=str(out),A3_vs_C_reduction_percent=gain_c,A3_vs_A1_reduction_percent=gain_a)))


if __name__=='__main__':main()
