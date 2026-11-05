# confirm10 — frozen-generator paired confirmation (approved five-arm Phase A)

计划run `cara-generator-v1-confirm10-r1-20261105`。本文件预先登记科学协议；2026-11-05用户批准：「批准 confirm10：先去掉 Native-k18 上卡，k18 接线验收后单独补跑；硬限按重报的数」。本卡执行五臂，k18及次要比较(c)为deferred supplement，补卡不继承本次启动许可。使用Cosmos CAL35/F17/AVSLC相同checkpoint、bf16/wan-fp32策略、guardrails、seed0、guidance7、432×768、93帧及T_DD边界。冻结模型为 [generator_v1](../generator_v1_frozen/FROZEN.md)，M0A_all、MEAN features；不再拟合/调参或用位置重叠评价。

10个输入为6 av、common_sense/human/misc/physics各1，名单、完整prompt原文、seed0及源JSON字节hash在 `manifest.json` 的 inputs/input_provenance。从1044源目录按固定salt `CARA_CONFIRM10_V1_20261105:` 的SHA256顺序、预定类别配额取source groups，不看输出质量。原2026-10-25曝光排除集加本次本地7184份JSON/gzip/YAML（4032份原字节复用）、research/src/tests中的身份提及，共排除114身份；原48保留池全部排除，含受保护final/backup32。所选10组不与CAL35、sensitivity8或历次calibration/minitest相交。经relay只读查本项目输出路径和316份结果元数据无命中；没有同prompt+seed可复用Native。范围、时间、inventory hash及未记录/外部job的限制均在 `input_exclusion_check`；未来首次执行前仍需增量检查，不凭本次快照派发。

每输入五臂：Native-36（仓库名NATIVE35，请求35/实际36更新）、F17-A2+lightC、R18C、R16C、R21C。新mask来自冻结文件，均36字符，D/A/C分别18/0/18、16/0/20、21/0/15，首尾D，无A；F17严格复用原17/10/9及A25/26=0.5、其余A=1的定义。light C及partial_updates=[]不变。每输入循环轮换五角色的顺序；一条warm在首输入上跑F17，排除统计。共50正式+1warm；生成十个同run Native-36参考，CPU仅评分其余40个完整93帧Alex pair，Native参考自比为0无需重算。

**Deferred supplement：** Native-k18从本次角色和请求矩阵中移除。接线验收后单独补跑C01–C10；requested18按仓库固定网格实际19次全D更新，不暗改requested17。次要比较(c) R18C与k18的配对Alex/T_DD推迟至补卡完成，本次不计算。原预计T_DD136.90s是19D假设，不能预称与R18C130.09s严格等时。

主终点：每prompt的 ΔAlex = LPIPS(R18C, 同seed Native36) − LPIPS(F17, 同seed Native36)，10prompt等权均值、prompt-level paired percentile bootstrap95% CI（100000次，固定seed20261105）及逐输入方向。**better成功：mean<0且CI上界<0**。未达到时，另报预写的次要非劣界限+0.01，CI上界<0.01才标SECONDARY_NONINFERIOR；否则INCONCLUSIVE，不把它改判为主终点成功。不进行布局/阈值重选。

次要完整报告：(a) mean LPIPS是否R16C≥R18C≥R21C；(b) **先完整列冻结预测与测量误差，再给判定**，预测0.932/0.825/0.652是旧四输入mean ratio，原样转移为十输入的固定预测，报告新mean paired ratio及绝对偏差、逐prompt绝对误差均值；不冒充新prompt专属预测；(c) R18C与k18配对Alex/T_DD（deferred supplement）；(d) 所有角色逐输入和均值T_DD。只在实测时间可比时作同预算解释。

报价固定为T_request=70.734852+6.772260·nD+0.993956·nA+0.637948·nC（本卡全light C，C项0）。Native36按36D，k18不计本卡。中心=1.1×请求合计+1200s；范围0.9×–1.2×合计+1200s。51请求正式报价 **3.739050004222224GPUh**、工程范围 **3.119828791333335–4.048660610666668**，上界向上取0.1后的硬限 **4.1GPUh**，按上述用户批准执行。CPU评分另在释放/唯一结算后进行，不计GPUh。

未来仅一次实际预留/启动及含失败费用的唯一结算；拒绝/失败不换输入、不缩分母、不自动重跑。50GiB宿主内存、90°C、4GiB磁盘门限和40g容器保持；预计16GiB私有输出卷足够51份MP4/终点latent，不保存Native逐步状态。只安排人工半程与最终验收，不持续监控、不建例程。
