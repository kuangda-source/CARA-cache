import json,numpy as np
R=json.load(open('results.json')); V=R['meta']['variants']; K=list(R['own'])
L=[]
p=lambda *a:L.append(' '.join(str(x) for x in a))
p('# Flatness of 17D layouts under s*dv models (zero-GPU)\n')
p('Exact enumeration: all C(28,9)=6,906,900 free-D sets in steps 8..35 (1-7,36 fixed D), each with its optimal 10 A (top-10 per-step error among non-D; exact for both sum and RSS since A scales per-step error by alpha). C = remaining 9.')
p('Error model: e(t)=0 at D; drift form e(t)=s(t)*sum_{u=a+1..t} dv(u); age form (repo weight, analyze.py) e(t)=(t-a)*s(t)*dv(t); a=last D; A multiplies by alpha. Total = sum or RSS. s log-linear interpolated to odd steps, log-linear extrapolated to 35 (linear-interp/repo-style check in own_linear). dv = guided_delta_RMS (native_delta_v.csv). Primary = drift_a0.5_sum. repo_exact = repo analyze.py objective (interval age-mass, peak then sum-square, A ignored) - reproduced repo 17D layouts exactly for all 6 non-FIT inputs using FIT s.\n')
p('Random-layout baseline: expected free-D overlap of a random 9-set with a fixed 9-set = 81/28 = 2.9.\n')
p('## Flatness and overlap (primary drift_a0.5_sum)\n')
p('|input|opt free D|opt A|n<=1%|n<=2%|n<=5%|n<=10%|<=2%: D ovl opt med/min|<=2%: A ovl opt med/min|<=5%: D ovl opt med/min|<=5%: frac D ovl>=7|<=5%: A ovl opt med/min|<=5%: D ovl F17 med|F17 gap %|F17 rank|F17 D+optA gap %|')
p('|'+'---|'*16)
v='drift_a0.5_sum'
for k in K:
    d=R['own'][k][v];w=d['within'];o=d['overlap']
    p(f"|{k}|{d['opt_freeD']}|{d['opt_A']}|{w['1%']['n']}|{w['2%']['n']}|{w['5%']['n']}|{w['10%']['n']}|{o['2%']['freeD_vs_opt']['median']:g}/{o['2%']['freeD_vs_opt']['min']}|{o['2%']['A_vs_opt']['median']:g}/{o['2%']['A_vs_opt']['min']}|{o['5%']['freeD_vs_opt']['median']:g}/{o['5%']['freeD_vs_opt']['min']}|{o['5%']['freeD_vs_opt']['frac_ge7']:.2f}|{o['5%']['A_vs_opt']['median']:g}/{o['5%']['A_vs_opt']['min']}|{o['5%']['freeD_vs_F17']['median']:g}|{d['F17']['gap_pct']:.1f}|{d['F17']['rank']:,}|{d['F17_D_optA']['gap_pct']:.1f}|")
p('\n## Robustness across variants (median over 8 inputs)\n')
p('|variant|n<=2%|n<=5%|<=2% D ovl opt|<=5% D ovl opt|<=5% A ovl opt|<=5% frac D>=7|<=5% D ovl F17|F17 gap % (min-max)|opt D ovl F17 (median)|transfer gap % per-target (median,max)|transfer gap % universal (median,max)|F17 gap on 6 targets (median)|')
p('|'+'---|'*13)
agg={}
for v in V:
    g=lambda f:np.median([f(R['own'][k][v]) for k in K])
    gaps=[R['own'][k][v]['F17']['gap_pct'] for k in K]
    tp=[R['transfer'][t][v]['per_target'][t]['gap_pct'] for t in ['O3','O4','N1','N2','N3','N4']]
    tu=[x['gap_pct'] for x in R['transfer']['universal'][v]['per_target'].values()]
    tf=[R['own'][t][v]['F17']['gap_pct'] for t in ['O3','O4','N1','N2','N3','N4']]
    row=dict(n2=g(lambda d:d['within']['2%']['n']),n5=g(lambda d:d['within']['5%']['n']),o2=g(lambda d:d['overlap']['2%']['freeD_vs_opt']['median']),
      o5=g(lambda d:d['overlap']['5%']['freeD_vs_opt']['median']),a5=g(lambda d:d['overlap']['5%']['A_vs_opt']['median']),f7=g(lambda d:d['overlap']['5%']['freeD_vs_opt']['frac_ge7']),
      of=g(lambda d:d['overlap']['5%']['freeD_vs_F17']['median']),optF17=g(lambda d:d['F17']['freeD_overlap_opt']))
    agg[v]=row
    p(f"|{v}|{row['n2']:g}|{row['n5']:g}|{row['o2']:g}|{row['o5']:g}|{row['a5']:g}|{row['f7']:.2f}|{row['of']:g}|{np.median(gaps):.1f} ({min(gaps):.1f}-{max(gaps):.1f})|{row['optF17']:g}|{np.median(tp):.1f}, {max(tp):.1f}|{np.median(tu):.1f}, {max(tu):.1f}|{np.median(tf):.1f}|")
p('\n## repo_exact objective (A ignored; own s, linear interp)\n')
p('|input|opt free D|peak n<=2%/5%|peak <=5% D ovl opt med/min|sumsq n<=2%/5%|sumsq <=5% D ovl opt med/min|F17 gap peak %|F17 gap sumsq %|')
p('|'+'---|'*8)
for k,d in R['repo_exact'].items():
    p(f"|{k}|{d['opt_freeD']}|{d['peak']['2%']}/{d['peak']['5%']}|{d['peak_overlap5']['freeD_vs_opt']['median']:g}/{d['peak_overlap5']['freeD_vs_opt']['min']}|{d['sumsq']['2%']}/{d['sumsq']['5%']}|{d['sumsq_overlap5']['freeD_vs_opt']['median']:g}/{d['sumsq_overlap5']['freeD_vs_opt']['min']}|{d['peak_F17_gap_pct']:.0f}|{d['sumsq_F17_gap_pct']:.0f}|")
p('\n## Transfer (primary). FIT model = mean s(O1,O2) + target dv (repo protocol); universal = mean s + mean dv of O1/O2\n')
p('|target|FIT-layout gap % under own model|F17 gap %|FIT-layout D ovl own opt|universal-layout gap %|')
p('|---|---|---|---|---|')
v='drift_a0.5_sum'
for t in ['O3','O4','N1','N2','N3','N4']:
    a=R['transfer'][t][v]['per_target'][t]; u=R['transfer']['universal'][v]['per_target'][t]
    p(f"|{t}|{a['gap_pct']:.1f}|{a['F17_gap_pct']:.1f}|{a['freeD_overlap_ownopt']}|{u['gap_pct']:.1f}|")
p(f"\nuniversal layout free D {R['transfer']['universal'][v]['fit_layout_freeD']}, A {R['transfer']['universal'][v]['fit_layout_A']}")
p('\n## Sanity: predicted F17 - F19_A1 vs measured paired LPIPS\n')
m=R['sanity']['measured_F17_minus_F19A1']
p('measured: '+', '.join(f"{k} {m[k]:+.4f}" for k in ['O1','O2','O3','O4','N1','N2','N3','N4']))
p('\n|variant|pred N1/N2/N3/N4|Spearman new4|Spearman all8|Pearson all8|Spearman F16-F19 old4|N3 pred rank among 8 (1=largest)|')
p('|---|---|---|---|---|---|---|')
for v in V:
    d=R['sanity'][v]; pr=[d[k]['diff_F17_F19'] for k in K]; rk=sorted(K,key=lambda k:-d[k]['diff_F17_F19']).index('N3')+1
    p(f"|{v}|{'/'.join(f'{d[k][chr(100)+chr(105)+chr(102)+chr(102)+chr(95)+chr(70)+chr(49)+chr(55)+chr(95)+chr(70)+chr(49)+chr(57)]:.3f}' for k in ['N1','N2','N3','N4'])}|{d['spearman_new4_F17-F19']:.2f}|{d['spearman_all8_F17-F19']:.2f}|{d['pearson_all8_F17-F19']:.2f}|{d['spearman_old4_F16-F19']:.2f}|{rk}|")
json.dump(agg,open('agg.json','w'),indent=1)
open('tables.md','w').write('\n'.join(L)+'\n')
print('\n'.join(L))
