# G17 mini-test 预注册

2026-11-05用户批准with-nonfast方案：28正式＋2warm＝30请求，中心2.225452351GPUh、硬限2.5GPUh。仅manifest_with_nonfast.json获执行/唯一预留权限；base manifest仍为quote only。四输入依manifest固定为O1/O3/N1/N3，seed0，已用于模型拟合，检验的是新layout，不能称新输入独立泛化。

主终点为每输入ΔAlex=LPIPS(G17,既有Native)−LPIPS(同批F17-A2+lightC,同一Native)。按四输入等权报告均值、全部逐输入差及改善/持平/退化方向数。质量比较的共同预算为各臂四输入mean T_DD≤132.98s；同时完整报告配对T_DD差，不做事后时间插值或换mask。G17-tail同样报告相对F17及相对G17的效应。位置重叠不作为判据，F17只是手搜参考。

95% CI使用paired-input bootstrap：穷举4^4=256个有放回、有序输入重采样，均值分布取线性插值2.5%/97.5%分位。帧不作独立样本；只报告效应与描述性CI，不做n=4非劣、显著性或方向一致性p检验，不临时增加新quality gate。该小卡不预先把CI当作泛化保证。

T_DD沿用原execute_with_timing/paper_denoise_decode_seconds（完整去噪＋decode）；T_request独立计费用。四条F17同批正式对照已计费；历史F17代码/seed/协议/同一A6000兼容，但分属不同批次，因此不把历史计时替代同批对照。不新增Native计时：本卡用绝对T_DD上限，无新的同批Native速度比分母。旧clean Native视频按既有SHA复用作完整93帧LPIPS-Alex0.1基准，不重算旧指标。

读出使用既有SpeedOwner/A校正实现与原F17 light C定义（当前embedding＋最近true-D残差，不做C probe/OSI/flow），partial_updates全为空。新生成G17/G17-tail/G19/G22按gen.py的所有A取α=1；历史F17保持A25/26 α=0.5、其余A α=1。F19 late4保留原6个early A，再加22/23 α=1、25/26 α=0.5；不是条件单支D的F19_DELTA4_LIGHT_C。original-C臂仅关闭light_C，A2不变。

|arm|mask（1-based第t步为mask[t−1]）|D/A/C|
|---|---|---|
|F17_A2_LIGHT_C|DDDDDDDDADADADADADADDAADAACCCCCCCCCD|17/10/9|
|F19_A1_LIGHT_C|DDDDDDDDADADADADADADDCCDCCDCCDCCCCCD|19/6/11|
|G17|DDDDDDDDDDDDDADADAADAAAAAAACCCCCCCCD|17/11/8|
|G17_TAIL|DDDDDDDDDDDDAADADAADAAAAAADCCCCCCCCD|17/11/8|
|G19|DDDDDDDDDDDDDDDDADADAAAAAAAAAAAAAAAD|19/17/0|
|G22|DDDDDDDDDDDDDDDDDDDDADAAAAAAAAAAAAAD|22/14/0|
|F17_ORIGINAL_C|DDDDDDDDADADADADADADDAADAACCCCCCCCCD|17/10/9|
|F19_A2_LATE4_LIGHT_C|DDDDDDDDADADADADADADDAADAADCCDCCCCCD|19/10/7|
|F17_D27_LIGHT_C|DDDDDDDDADADADADADADDAADAADCCCCCCCCD|18/10/8|

G17-tail唯一采用D13→A、A27→D。0-based13本来就是A、27为C，会得到18D/11A/7C，违反同nD交换定义，明确排除。F17恢复D27是18D，作为次臂，不伪称17D。19D/22D可选臂没有C，light_C开关在这两臂上无实际C调用；它们不适用132.98s快档门，只报告质量—时间效应。

N1/N3两输入次臂：F19-A1-lightC对历史F19-A1（同Native SHA，LPIPS可配对，历史时间不作同批时间）；F17-original-C对同批F17-lightC；F19-late4对同批F19-A1-lightC；F17-D27对同批F17。各报告两输入方向与效应；n=2 CI同样仅描述，不作推断。可选G19/G22各四输入对同批F17报告效应与时间，不以更慢臂宣称同预算获益。

所有formal请求均clean、audit=false、无逐步state saves；两warm为O1上的F17-lightC与F17-original-C，覆盖两条C链，不进入统计。矩阵固定，不用拒绝/失败替换输入或增加请求。GPU释放、唯一实际结算后才能CPU评分；实际mask偏离标为技术无效并保留输出，不调整布局或阈值。配置、角色轮转顺序、引用视频、共享alpha与CI实现均在manifest/prepare.py/postprocess.py中。
