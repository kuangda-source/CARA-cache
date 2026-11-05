# AVSLC mini-test 预注册

用户批准缩减为以下四臂，重新报价中心≤1.5GPUh即可启动，硬限仍为1.5。正式中心1.389370089GPUh（工程范围1.197363407–1.485373431），保留2warm；仅manifest.json获执行权限，phase=USER_APPROVED_PENDING_FRESH_ADMISSION，仍须Linux生产CPU及fresh资源准入。

四输入O1/O3/N1/N3，Cosmos原35 requested/36实际updates、seed0、原T_DD去噪＋decode协议不变。以下mask为定义，1-based第t步对应mask[t−1]。所有新A为α=1.0，light_C=true，partial_updates=[]；不做state saves。

|arm|mask|D/A/C|预测T_DD(s)|
|---|---|---|---:|
|G17_CALL|DDDDDDDDDDDDDCDCDCCDCCCCCCCCCCCCCCCD|17/0/19|123.28|
|G17_A21_24|DDDDDDDDDDDDDADADAADAAAACCCCCCCCCCCD|17/8/11|130.08|
|R18C|DDDDDDDDDDDDCDCDCCDCCDCCCDCCCCCCCCCD|18/0/18|130.09|
|R17A|DDDDDDDDADADADADADADAADAAADCCCCCCCCD|17/11/8|132.63|

16正式请求（四臂各四输入）＋2warm（O1 G17_CALL、G17_A21_24），正式清洁计时、audit=false。warm不进入统计；不新增Native计时，不重跑或重算F17/G17。输入内四臂按manifest固定轮转。

复用reports/cara_g17_minitest_nonfast_r1_20261105/的scores.json及complete_analysis.json，八个F17/G17 LPIPS/T_DD以原scope和源文件SHA绑定，属于同协议H批次前一卡，明确不是本run新同时计时。Native视频沿用同SHA；仅16个新视频在释放/唯一结算后做原完整93帧LPIPS-Alex0.1 CPU评分。

主终点：G17_CALL与R18C分别对四输入计算LPIPS/F17配对ratio及等权均值，原样对照prereg_next.json冻结的M0A_all/M0A_exclG：G17_CALL=0.969701/1.238312，R18C=0.824932/1.051839。两主臂mean ratio相对两个冻结预测的平均绝对误差（MAE）作为描述性的最近参数集，不重新拟合β_L、κ或ρ，不把最近预测当作统计接受。报告逐输入ratio与方向；两参数集β_L背景见principle_refit_report.md，不新增第三组预测。

次终点：每个新臂对复用F17和G17的配对ΔAlex、ΔT_DD；R17A−R18C、G17_CALL−R18C，共10对比。均报告四输入均值、逐输入方向和描述性95% CI；CI使用原4^4=256有序配对bootstrap及线性2.5/97.5百分位。帧不当独立样本，不做n=4非劣/显著性检验，不用D/A位置重叠门。T_DD不同则原样报告，不事后插值、换mask或加请求。

这些输入已参与前期拟合；本卡测试A/light-C结构及冻结预测，不称独立新输入泛化。技术mask偏离保留原结果并标注，不补跑替换。guardian门保持50GiB host memory、90°C、4GiB disk；容器40g、私有输出16GiB，无自动检查/heartbeat/cron/automation。
