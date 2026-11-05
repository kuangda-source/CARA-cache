# sensitivity8 完整结果（2026-11-05）

Run `cara-native-sensitivity8-resume-r3-20261105`，launch `e829f230b9c44b2cbd63128d1e511a0e`，GPU source113dc7c8。2026-11-05T08:31:44.106848+08:00结束，116/116成功，OOMKilled=false/exit0；释放、原进程结束、Default恢复和中央唯一结算seq98均完成。六条r2科学/控制结果按hash继承；两旧warm只存档，新卡2fresh warm。另复用原r1五Native和F17 clean16，合计覆盖原143逻辑位置，不称143次新独立生成。

本run实耗 **7.566297455049GPUh**，累计 **228.350508821035GPUh**。27.5预留=本run11＋旧BANK24未知责任4.5＋旧FULL1624未知责任12；本次释放11，现保留16.5。旧hold未确认GPU提交，不伪结算为0。cap250/available5.149491179仅保留历史账本格式；当前不设累计政策上限，新单run报价>8须本人批准。失败卡原费用和结算保持。

技术：八Native、全部112个single-C/latentMSE/完整93帧Alex已收齐；五登记latent控制及额外warm桥均equal/max_abs_diff=0，解码RGB/PTS控制全通过。CPU评分CUDA_initialized=false，F17原12LPIPS/48质量位置只合并、不重算。未重启GPU、未降guardian门限、未建监控/automation。

## 预注册科学判定

F17新四输入速度1.919511×，平均T_DD=131.701259s，mean Alex=0.236186（旧组0.238368），六均值质量门全通过。原非配对n=4/组、δ0.027、70排列非劣p=0.300，NI_passed=false、compound confirmation_passed=false保持。结论为确认设计功效不足/非劣未证实，不解读为F17方法整体失败；下列同输入配对差仅作诊断，不替代原检验。misc和新AV都存在Alex>0.27的个案，0.27原为均值门。

|新输入|Native/F17 T_DD|F17 Alex|F19 Alex|配对差 F17−F19|
|---|---:|---:|---:|---:|
|av_cc90f226-5312-4e0f-959a-39cd4eb4d90d|1.919859|0.315271|0.308551|+0.006719|
|human_034|1.920085|0.154257|0.150400|+0.003856|
|misc_9699390-uhd_3840_2160_30fps|1.919522|0.346879|0.276193|+0.070686|
|physics_017|1.918576|0.128340|0.123312|+0.005028|

固定s·Δv重建只用O1/O2 FIT平均s，在其余六输入转移，不调系数、步位或函数。D自由位置重合中位 **5/9**（门≥7），A中位 **6/10**（门≥7），原理描述门 **未通过**。完整16/17/19/22/25D预测、各输入重合/Hamming/Jaccard见[原分析](complete_analysis.json)。未来R4不做16D不改变本卡原登记16D分析。

## s_i(t) 全表

原公式 `sqrt(terminal latent MSE) / max(local guided C−Native RMS, 1e-12)`。下表6有效位；全精度MSE、Alex、局部扰动和s见[sensitivity.csv](sensitivity.csv)。

- O1: `av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632` (FIT)
- O2: `human_199` (FIT)
- O3: `misc_13398218_3840_2160_60fps` (CHECK)
- O4: `av_51b45829-502e-4143-9c32-c026bd6ab191` (CHECK)
- N1: `av_cc90f226-5312-4e0f-959a-39cd4eb4d90d` (NEW_CONFIRM)
- N2: `human_034` (NEW_CONFIRM)
- N3: `misc_9699390-uhd_3840_2160_30fps` (NEW_CONFIRM)
- N4: `physics_017` (NEW_CONFIRM)

|t|O1|O2|O3|O4|N1|N2|N3|N4|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|8|0.486673|0.293445|0.461326|0.282223|0.393741|0.271582|0.448145|0.229286|
|10|0.643552|0.314858|0.554449|0.380636|0.431609|0.279239|0.588319|0.215413|
|12|0.465525|0.384318|0.464491|0.321755|0.750774|0.237474|0.445326|0.301933|
|14|0.336831|0.311213|0.291814|0.27865|0.474736|0.260448|0.41961|0.243009|
|16|0.373794|0.300368|0.27587|0.326099|0.375214|0.299328|0.443935|0.241921|
|18|0.189204|0.247406|0.249353|0.218801|0.280206|0.265047|0.315791|0.20616|
|20|0.266218|0.217665|0.190144|0.302698|0.227547|0.159842|0.300733|0.2523|
|22|0.208035|0.185091|0.192467|0.210737|0.21094|0.181368|0.234941|0.176931|
|24|0.16399|0.157594|0.163888|0.154448|0.159381|0.153055|0.16481|0.140902|
|26|0.121861|0.109363|0.107352|0.11489|0.121609|0.107379|0.112939|0.106254|
|28|0.0784928|0.0733115|0.0727045|0.0744766|0.0778945|0.0693059|0.0735691|0.0724163|
|30|0.0472432|0.0442701|0.0431508|0.0427527|0.0454406|0.0425491|0.0433729|0.0436872|
|32|0.0260021|0.025414|0.024973|0.0244101|0.0258507|0.0247409|0.0240858|0.0240787|
|34|0.0153046|0.0155042|0.0152198|0.0148551|0.0157336|0.0151255|0.014855|0.0144373|

## Δv 文件与内存

全部8×36步的三支RMS差分及first-block rel_l1在[native_delta_v.csv](native_delta_v.csv)；step1按协议为空。原服务器路径在[native_artifact_paths.json](native_artifact_paths.json)：O1–O4/N1位于`outputs/cara-native-sensitivity8-confirm4-r1-20261104/native_states/<member>/metrics.json`，N2–N4位于`outputs/cara-native-sensitivity8-resume-r3-20261105/native_states/<member>/metrics.json`，共同root为`/data20t/gaokuangda/worldcache_workspace`。同目录`guided_{08,10,...,34}.pt`是Native guided值，供局部扰动计算，不是已保存的完整Δv向量。未移动或删除这些复用产物。

GPU运行内存日志实际为output/host_memory.jsonl（[116行原件](host_memory.jsonl)）；stage/CPU-host-memory.jsonl只有CPU入口的一行，不用于GPU运行峰值。GC后RSS最高 **15.499306GiB**，suffix中位 **14.057072GiB**；这不是请求中瞬时RSS最大值。cgroup lifetime peak **38.435738/40GiB**，余量 **1.564262GiB**（96.089%已用）。峰值首次在PIPE_078达到，093/108未再抬高累计峰值；三record结束时current约23.00/21.56/21.74GiB、RSS约13.98/12.80/13.36GiB，每组14状态清理后current落至13.16/13.76/13.65GiB。与大量文件缓存参与一致，缺少峰值memory.stat分项，不能确认峰值全为page cache，也不能排除序列化瞬时分配。gc修复15bb3d39后跑完109次新恢复和3record，后缀RSS无3.33GB/请求持续累积，支持已识别的闭环滞留修复有效；40g及50GiB/90°C/4GiB门均未改。

原哈希绑定billing字节保持；stage/central-settlement.json和status显示pending=false。原唯一结算、GPU终态和CPU退出见[central_settlement.json](central_settlement.json)、[terminal_capture.json](terminal_capture.json)、[CPU_score_terminal.json](CPU_score_terminal.json)。科学结论、财务接受与未来R4设计分开；本次没有新后继GPU授权。
