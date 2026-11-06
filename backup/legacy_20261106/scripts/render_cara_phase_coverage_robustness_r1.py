#!/usr/bin/env python3
"""Render the actual36 geometric-optimum masks; never load a model or metric."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle,Patch


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();raw=Path(args.audit).read_bytes();audit=json.loads(raw)
    output=Path(args.output);output.mkdir(parents=True,exist_ok=False)
    card_path=next(p for p in audit['input_sha256'] if p.endswith('/C1_MANIFEST_R1.json'))
    card_raw=Path(card_path).read_bytes()
    if hashlib.sha256(card_raw).hexdigest()!=audit['input_sha256'][card_path]:
        raise ValueError('Original F19 reference card SHA differs')
    card=json.loads(card_raw)
    f19=[i for i,a in enumerate(card['roles']['F19_C']['policy']['actions'],1) if a=='D']
    rows=[dict(label='F19-C',D=19,tilt=None,dense_steps=f19,hamming_to_F19=0,
        D_8_to_16=sum(8<=t<=16 for t in f19),max_C_run=max(b-a-1 for a,b in zip(f19,f19[1:]+[37])))]
    order={19:0,22:1,16:2,17:3}
    rows.extend(dict(r,label=f"{r['D']}D  lambda={int(r['tilt'])}")
        for r in sorted(audit['geometric_optima'],key=lambda r:(order[r['D']],r['tilt'])))
    plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42})
    figure,(axes,info)=plt.subplots(1,2,figsize=(13.8,4.9),gridspec_kw={'width_ratios':[36,13]})
    matrix=[[int(t in r['dense_steps']) for t in range(1,37)] for r in rows]
    axes.imshow(matrix,aspect='auto',interpolation='nearest',cmap=ListedColormap(['#f8f9fc','#225ea8']),
        vmin=0,vmax=1,extent=(.5,36.5,len(rows)-.5,-.5))
    axes.set_yticks(range(len(rows)),[r['label'] for r in rows])
    axes.set_xticks([1,4,8,12,16,20,24,28,32,36]);axes.set_xlabel('Actual update index (1-based)')
    axes.set_xticks([i+.5 for i in range(37)],minor=True)
    axes.set_yticks([i+.5 for i in range(len(rows))],minor=True)
    axes.grid(which='minor',color='#d7dce4',linewidth=.6)
    axes.tick_params(which='minor',length=0)
    axes.add_patch(Rectangle((7.5,-.5),9,len(rows),fill=False,edgecolor='#d39a17',linewidth=1.8))
    info.set_xlim(0,1);info.set_ylim(len(rows)-.5,-.5);info.axis('off')
    for x,label in ((.12,'dH to F19'),(.50,'D[8,16]'),(.86,'max C run')):
        info.text(x,-.85,label,ha='center',fontsize=9)
    for i,row in enumerate(rows):
        for x,key in ((.12,'hamming_to_F19'),(.50,'D_8_to_16'),(.86,'max_C_run')):
            info.text(x,i,str(row[key]),ha='center',va='center',fontsize=10)
    figure.suptitle('Single-source geometric optima before new video evaluation',y=.98,fontsize=13)
    figure.legend(handles=[Patch(facecolor='#225ea8',label='D'),Patch(facecolor='#f8f9fc',edgecolor='#aaa',label='C')],
        loc='lower center',ncol=2,frameon=False,bbox_to_anchor=(.50,-.015))
    figure.text(.02,.013,'dH is a bitwise mask distance; unequal D budgets are not equal-swap comparisons.',fontsize=8,color='#555')
    figure.tight_layout(rect=(0,.05,1,.94))
    figure.savefig(output/'optimal-layouts.png',dpi=160,bbox_inches='tight')
    figure.savefig(output/'optimal-layouts.pdf',bbox_inches='tight');plt.close(figure)
    with (output/'optimal-layouts.csv').open('x',newline='') as target:
        writer=csv.DictWriter(target,fieldnames=['label','D','tilt','hamming_to_F19','D_8_to_16','max_C_run','dense_steps'],lineterminator='\n')
        writer.writeheader()
        for row in rows:writer.writerow({k:(' '.join(map(str,row[k])) if k=='dense_steps' else row[k]) for k in writer.fieldnames})
    proof=dict(status='GEOMETRIC_MASK_PLOT_RENDERED_NO_NEW_VIDEO',
        input_sha256=hashlib.sha256(raw).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reference_card_sha256=hashlib.sha256(card_raw).hexdigest(),
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()},GPU_submissions=0)
    with (output/'figure.json').open('x') as target:target.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(dict(rows=len(rows),output=str(output)),indent=2))


if __name__=='__main__':main()
