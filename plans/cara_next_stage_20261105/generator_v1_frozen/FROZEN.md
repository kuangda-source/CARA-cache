# Generator v1 — frozen, 2026-11-05

采用 **M0A full-data / M0A_all**：κ_A=0.2915722788395509，β_L=0.514056728071378，ρ=0.10472664684826208，γ=0.3759502318511064。参数与 `refit_models.json` 的 M0A.params_all/gamma_all 完全一致；选择依据为已完成的 [AVSLC](../../../reports/cara_avslc_minitest_r1_20261105/complete_analysis.json) 两主臂冻结预测比较，不重新拟合。

MEAN features 使用原八输入的 sensitivity 几何均值及 Δv 算术均值。DP 固定首七步和第36步为 D；允许 A 时仍未选择 A，`frozen_gen_v1.json` 的 DC/DAC14–25 成对相同且 nA=0。**v1 只用 D/light-C**，不以新确认输入的结果改模型、features、预算映射或布局。

|角色|源key|冻结mask（1-based `mask[t-1]`）|D/A/C|预测T_DD(s)|旧四输入预测LPIPS/F17均值|
|---|---|---|---|---:|---:|
|R16C|DC16|`DDDDDDDDDCDCDCDCDCCDCCCDCCCCCCCCCCCD`|16/0/20|116.47|0.932|
|R18C|DC18|`DDDDDDDDDDDDCDCDCCDCCDCCCDCCCCCCCCCD`|18/0/18|130.09|0.825|
|R21C|DC21|`DDDDDDDDDDDDDDDCDCDCDCCDCCCDCCCCCCCD`|21/0/15|150.52|0.652|

核验通过：三mask长度36、D数16/18/21、首尾D、与上述DC项逐字相同；对应DAC项也相同；现有 interval_grammar 编译后actions及计数一致，flow on/off共六条完整36步tiny CPU路径通过（另含F17两条），CUDA=false。预测T_DD模型是7.51+6.81·nD+0.85·nA，不是GPU账单的完整T_request模型。

机器可读冻结为 [frozen_masks_r16_r18_r21.json](frozen_masks_r16_r18_r21.json)，保留原 `frozen_gen_v1.json` 并记录五份原始资产的SHA256。原生成脚本按提供字节归档，仍依赖原 `/workspace/flat_opt` 等数据路径；本次核验冻结输出、参数和执行grammar，没有重跑DP或重拟合。未来需要可移植重生成时须绑定相同原数据；当前确认卡直接消费冻结mask。

**冻结后不得修改v1。** 后续任何参数、feature、生成器或mask变动另起版本；不以本次确认结果倒改冻结预测。
