# B36完整验收后的图表导出

当前为CPU准备完成状态。[最终双端CPU接受](../../../../reports/cara_fast_B36_figures_CPU_acceptance_r2_20261029.json)与[图面检查](../../../../reports/cara_fast_B36_figures_visual_QA_r1_20261029.json)均仅针对显式CPU夹具；B36仍待[预计5.0215/硬5.5GPUh的单次批准](B36_GPU_REVIEW_R2.md)。原执行52文件和已接受汇总4文件均未改动，没有GPU派发、B指标或正式B图表。

## 完整结果的入口

先按[汇总交接](B36_ANALYSIS_READINESS.md)对五份显式原件生成完整分析JSON。全部B终态、唯一结算、释放、26新评分及六份原A评分组合成完整32位置并接受后，使用：

```sh
python3 scripts/render_cara_fast_b36_figures_r1.py --analysis /absolute/path/to/complete-analysis.json --output-dir /absolute/path/to/new-report
```

入口根据分析JSON记录的五份原件及SHA重建完整接受链，再逐字段核对分析值和原CPU接受源码，之后才创建新的输出目录。相对原件路径默认以仓库根目录解析；若最初使用其它工作目录，可显式指定 `--receipt-root`。已有目录、部分数据、改动的汇总、原件或源码均拒绝；公共CLI没有CPU夹具开关。

## 输出与原协议

- 四组图各输出PNG和PDF：`T_DD_speed_fidelity`、`T_request_speed_fidelity`、`Alex_frame_curves`、`temporal_detail`。每输入的方法编号按固定角色映射，保持登记的轮转顺序；WC/RA明确标注原FIT的UNMATCHED，Native22标FIT MATCHED。
- 四张CSV：`per_member.csv`为32位置，`frame_curves.csv`为32×93＝2976行，`prompt_equal.csv`为ALL/FIT/CHECK三组共24行，`FIT_A_only.csv`为三基线×两FIT共6行。原PSNR的 `+inf` 与未定义梯度比保留，不丢弃输入或改分母。
- 组计时沿用先输入内平均正式和登记重复、再输入等权。速度区间复用未改的 `scripts/analyze_cara_fast_r1.py` 与原报表登记的20,000次prompt簇bootstrap、seed20261028、higher分位及两侧95%探索区间；没有新的显著性或质量门。所有图保留旧CAL及CHECK角色说明。
- `report.json`绑定完整分析、导出源码及全部12个输出文件SHA。绘图只使用已接受元数据，不解码视频、不运行度量网络、不调用预算或GPU操作，也不重新选择基线。

## CPU验证与修订历史

最终R27在两端各6项控制通过，均1CPU/4GiB、禁swap、core27、无GPU/网络、root只读、180秒工作及30秒退出边界，容器退出0且无OOM。沿用两端现有Matplotlib3.10.9，未安装新包或修改生产环境。检查覆盖五原件重建、篡改/部分拒绝、实际四组图与四CSV、固定角色编号、未定义梯度绘图路径及禁止覆盖。

R26的自动控制通过后，图面检查发现散点编号错误地跟随每输入轮转顺序。原目录、自动接受回执与图片全部保留；R27改为固定角色编号，实际捕获所有64个散点注释并核对，同时绘制零参考梯度夹具。当前使用上方最终接受回执，不采用R26图面。

CPU夹具的每张图带有 `CPU LAYOUT ONLY / NO B36 RESULTS` 水印，每张CSV均有CPU标记，公开入口拒绝将它们导出为正式结果。四份最终PNG已经按源SHA取回并直接检查布局；这些文件保存在忽略的本地预览目录和原远端CPU stage。
