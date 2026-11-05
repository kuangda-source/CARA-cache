# Flatness of 17D layouts under s*dv models (zero-GPU)

Exact enumeration: all C(28,9)=6,906,900 free-D sets in steps 8..35 (1-7,36 fixed D), each with its optimal 10 A (top-10 per-step error among non-D; exact for both sum and RSS since A scales per-step error by alpha). C = remaining 9.
Error model: e(t)=0 at D; drift form e(t)=s(t)*sum_{u=a+1..t} dv(u); age form (repo weight, analyze.py) e(t)=(t-a)*s(t)*dv(t); a=last D; A multiplies by alpha. Total = sum or RSS. s log-linear interpolated to odd steps, log-linear extrapolated to 35 (linear-interp/repo-style check in own_linear). dv = guided_delta_RMS (native_delta_v.csv). Primary = drift_a0.5_sum. repo_exact = repo analyze.py objective (interval age-mass, peak then sum-square, A ignored) - reproduced repo 17D layouts exactly for all 6 non-FIT inputs using FIT s.

Random-layout baseline: expected free-D overlap of a random 9-set with a fixed 9-set = 81/28 = 2.9.

## Flatness and overlap (primary drift_a0.5_sum)

|input|opt free D|opt A|n<=1%|n<=2%|n<=5%|n<=10%|<=2%: D ovl opt med/min|<=2%: A ovl opt med/min|<=5%: D ovl opt med/min|<=5%: frac D ovl>=7|<=5%: A ovl opt med/min|<=5%: D ovl F17 med|F17 gap %|F17 rank|F17 D+optA gap %|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|O1|[8, 10, 12, 14, 16, 18, 21, 24, 28]|[9, 11, 13, 15, 17, 19, 20, 23, 26, 27]|5|20|298|2251|7/0|7.5/1|5/0|0.15|5/1|5|21.1|29,201|16.3|
|O2|[8, 9, 11, 12, 14, 16, 19, 22, 27]|[10, 13, 15, 17, 18, 20, 21, 24, 25, 26]|5|12|102|865|7/4|8/4|6/3|0.33|6/2|5|23.3|17,619|20.3|
|O3|[8, 9, 10, 12, 14, 16, 19, 22, 27]|[11, 13, 15, 17, 18, 20, 21, 24, 25, 26]|3|8|50|705|7.5/6|8.5/6|6/2|0.38|7/2|5|20.0|10,078|17.2|
|O4|[8, 9, 10, 12, 14, 16, 19, 22, 27]|[11, 13, 15, 17, 18, 20, 21, 24, 25, 26]|3|4|17|162|8/7|9/8|7/5|0.82|8/6|5|26.8|15,258|23.7|
|N1|[8, 9, 11, 13, 15, 17, 20, 23, 27]|[10, 12, 14, 16, 18, 19, 21, 22, 25, 26]|6|24|263|2433|6.5/3|7/4|5/1|0.25|6/1|3|21.0|24,231|17.9|
|N2|[8, 9, 10, 12, 14, 16, 19, 22, 27]|[11, 13, 15, 17, 18, 20, 21, 24, 25, 26]|4|15|90|1148|7/5|8/4|6/2|0.37|6/1|5|22.2|21,850|18.9|
|N3|[8, 9, 11, 13, 15, 17, 19, 22, 26]|[10, 12, 14, 16, 18, 20, 21, 23, 24, 25]|4|19|211|1620|6/1|7/1|5/1|0.19|6/1|4|13.7|4,647|11.6|
|N4|[8, 9, 10, 12, 14, 16, 19, 23, 28]|[11, 13, 15, 17, 18, 20, 21, 22, 26, 27]|9|20|122|1088|6/5|7/6|6/3|0.36|7/4|6|20.9|18,158|15.6|

## Robustness across variants (median over 8 inputs)

|variant|n<=2%|n<=5%|<=2% D ovl opt|<=5% D ovl opt|<=5% A ovl opt|<=5% frac D>=7|<=5% D ovl F17|F17 gap % (min-max)|opt D ovl F17 (median)|transfer gap % per-target (median,max)|transfer gap % universal (median,max)|F17 gap on 6 targets (median)|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|drift_a0.3_sum|14.5|202.5|7|5|6|0.24|4.5|29.8 (21.3-34.6)|4.5|1.0, 3.1|4.2, 9.8|29.8|
|drift_a0.3_rss|10.5|62.5|7|6|7|0.36|5|34.4 (21.8-43.2)|5|0.3, 5.5|5.8, 9.9|33.0|
|drift_a0.5_sum|17|112|7|6|6|0.35|5|21.0 (13.7-26.8)|5|0.3, 7.8|6.5, 11.4|20.9|
|drift_a0.5_rss|6|47|7.25|6.25|6.75|0.46|5|25.6 (12.3-43.2)|5|1.3, 6.5|7.1, 15.4|25.6|
|age_a0.3_sum|27|306.5|6|5|6|0.16|4|46.4 (37.1-67.9)|4.5|0.7, 6.3|7.1, 13.5|45.0|
|age_a0.3_rss|14|80.5|7|6|6.5|0.38|4.5|50.9 (35.5-78.3)|5|3.2, 9.6|12.6, 27.0|48.8|
|age_a0.5_sum|15.5|112|7|5.5|6|0.33|4|32.6 (22.1-44.4)|5|0.8, 2.4|8.3, 11.9|32.6|
|age_a0.5_rss|10.5|58|7|6|6|0.39|5|35.3 (18.0-47.7)|4.5|0.3, 5.3|13.0, 21.2|35.3|

## repo_exact objective (A ignored; own s, linear interp)

|input|opt free D|peak n<=2%/5%|peak <=5% D ovl opt med/min|sumsq n<=2%/5%|sumsq <=5% D ovl opt med/min|F17 gap peak %|F17 gap sumsq %|
|---|---|---|---|---|---|---|---|
|O1|[8, 10, 12, 14, 16, 18, 21, 24, 28]|2/52|1/0|12/28|0.5/0|231|150|
|O2|[8, 9, 11, 12, 14, 16, 19, 22, 27]|6/6|7.5/7|3/5|7/3|85|93|
|O3|[8, 9, 10, 12, 14, 16, 19, 22, 27]|4/29|5/2|29/60|5/2|107|72|
|O4|[8, 9, 10, 12, 14, 16, 19, 22, 27]|1/1|9/9|1/3|8/7|121|104|
|N1|[8, 9, 11, 13, 15, 17, 20, 23, 28]|19/24|6.5/3|4/22|5/2|126|100|
|N2|[8, 9, 10, 12, 14, 16, 19, 23, 28]|2/2|8.5/8|14/36|6/2|157|122|
|N3|[8, 10, 12, 14, 16, 18, 20, 23, 28]|10/15|6/4|9/20|0.5/0|138|90|
|N4|[8, 10, 12, 14, 16, 18, 21, 25, 30]|23/28|5.5/1|1/7|7/5|240|240|

## Transfer (primary). FIT model = mean s(O1,O2) + target dv (repo protocol); universal = mean s + mean dv of O1/O2

|target|FIT-layout gap % under own model|F17 gap %|FIT-layout D ovl own opt|universal-layout gap %|
|---|---|---|---|---|
|O3|0.0|20.0|9|5.3|
|O4|-0.0|26.8|9|7.9|
|N1|1.1|21.0|8|2.7|
|N2|7.8|22.2|6|4.3|
|N3|0.5|13.7|6|7.6|
|N4|0.1|20.9|7|11.4|

universal layout free D [8, 9, 10, 11, 13, 15, 18, 21, 26], A [12, 14, 16, 17, 19, 20, 22, 23, 24, 25]

## Sanity: predicted F17 - F19_A1 vs measured paired LPIPS

measured: O1 +0.0103, O2 -0.0005, O3 +0.0190, O4 -0.0013, N1 +0.0067, N2 +0.0039, N3 +0.0707, N4 +0.0050

|variant|pred N1/N2/N3/N4|Spearman new4|Spearman all8|Pearson all8|Spearman F16-F19 old4|N3 pred rank among 8 (1=largest)|
|---|---|---|---|---|---|---|
|drift_a0.3_sum|0.208/0.176/0.155/0.166|-0.40|-0.14|-0.53|-0.40|8|
|drift_a0.3_rss|0.029/0.026/0.015/0.037|-0.40|-0.14|-0.59|-0.40|8|
|drift_a0.5_sum|0.249/0.213/0.200/0.189|0.00|0.10|-0.30|0.20|7|
|drift_a0.5_rss|0.023/0.022/0.015/0.031|-0.40|-0.10|-0.41|-0.40|8|
|age_a0.3_sum|0.333/0.332/0.279/0.320|-0.40|-0.60|-0.74|-0.40|8|
|age_a0.3_rss|0.060/0.070/0.048/0.086|-0.80|-0.38|-0.47|-0.40|8|
|age_a0.5_sum|0.374/0.368/0.323/0.343|-0.40|-0.67|-0.65|-0.40|8|
|age_a0.5_rss|0.045/0.055/0.040/0.072|-0.80|-0.21|-0.32|-0.40|6|

## N3 diagnosis
F17 and F19_A1 are identical through step 21, so every predicted F17-F19 difference comes from steps 22-35. Mostly it comes from 27-35: F17 is all C there, while F19 has D at 27 and 30. N3's predicted F17 total (1.11) sits in the middle of the pack. Its tail dv sum over 27-35 is 2.84, against 2.44-3.00 for the other inputs. Its measured single-C LPIPS at 26-34 is 0.018-0.025, about the same as O1 and O3. Where N3 does stand out is single-C sensitivity at 14-22, the highest of all inputs (for example 0.062 at t=22). Its +0.071 measured excess is therefore not explained by tail sensitivity in either the model or the single-step data. The most likely source is an interaction (non-additive compounding of mid-segment error through the 9-step C tail), which no additive per-step model can capture. This is a hypothesis; it would need a GPU check (F17 with D at 30, or F17 with mid A replaced by D).

## Verdict
In absolute terms, the model optimum is NOT flat. Only 4-24 layouts fall within 2% and 17-298 within 5% (primary), out of 6.9M. The near-optimal set is still structurally diverse: within 5%, the median free-D overlap with the input's own optimum is 5-7/9, the minimum is 0-3, and only 15-82% of those layouts (median about 35%) would pass a >=7/9 gate against their own optimum. Within 5%, the median overlap with F17 is 3-6/9, while random gives 2.9. F17 itself is 14-27% above the optimum (primary; 12-78% across variants). Under the model, FIT-transferred layouts reach 0-8% of each target's own optimum, while F17 is at 14-27%. Position overlap is a poor proxy for outcome. However, the model fails the outcome check: its predicted F17-F19 ordering has Spearman of 0.0 to -0.8 against the measured values, and it ranks N3 as the smallest or second-smallest rather than the outlier. So its layout optima should not be trusted either.

Replacement gates (outcome-based):
(1) Model-validity prerequisite: predicted vs measured paired LPIPS across >=3 layouts x 8 inputs must reach Spearman >=0.6.
(2) Regret: the transferred layout must be within 5% of the held-out input's own-model optimum.
(3) Final: paired measured LPIPS non-inferiority vs F17 at equal NFE (for example, mean delta <=0.005 with no single input >+0.02).
