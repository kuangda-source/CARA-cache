# confirm10 — frozen-generator paired confirmation (prepare/quote only)

计划run `cara-generator-v1-confirm10-r1-20261105`。本文件预先登记科学协议；本轮不授权GPU、预留、sync或启动。所有run均等待用户新的go-ahead。使用Cosmos CAL35/F17/AVSLC相同checkpoint、bf16/wan-fp32策略、guardrails、seed0、guidance7、432×768、93帧及T_DD边界。冻结模型为 [generator_v1](../generator_v1_frozen/FROZEN.md)，M0A_all、MEAN features；不再拟合/调参或用位置重叠评价。

10个输入为6 av、common_sense/human/misc/physics各1，名单、完整prompt原文、seed0及源JSON字节hash在 `manifest.json` 的 inputs/input_provenance。从1044源目录按固定salt `CARA_CONFIRM10_V1_20261105:` 的SHA256顺序、预定类别配额取source groups，不看输出质量。原2026-10-25曝光排除集加本次本地7184份JSON/gzip/YAML（4032份原字节复用）、research/src/tests中的身份提及，共排除114身份；原48保留池全部排除，含受保护final/backup32。所选10组不与CAL35、sensitivity8或历次calibration/minitest相交。经relay只读查本项目输出路径和316份结果元数据无命中；没有同prompt+seed可复用Native。范围、时间、inventory hash及未记录/外部job的限制均在 `input_exclusion_check`；未来首次执行前仍需增量检查，不凭本次快照派发。

每输入六臂：Native-36（仓库名NATIVE35，请求35/实际36更新）、F17-A2+lightC、R18C、R16C、R21C、Native-k18。新mask来自冻结文件，均36字符，D/A/C分别18/0/18、16/0/20、21/0/15，首尾D，无A；F17严格复用原17/10/9及A25/26=0.5、其余A=1的定义。light C及partial_updates=[]不变。每输入循环轮换六角色的顺序；两warm在首输入上跑F17和k18，排除统计。共60正式+2warm；生成十个同run Native-36参考，CPU仅评分其余50个完整93帧Alex pair，Native参考自比为0无需重算。

**Native-k18可用性差异：** 已有 `p2_native_sampling.execute` 支持requested18，其已冻结UniPC网格实际是19更新，19个全D；不是“恰好18更新”。`cara_f19_speed190_requests_r1.Requests` 当前硬编码num_steps35、全卡schedule及expected_updates36，尚未完成此卡的k18接线。启动前最小改动是从role读取requested_steps、native schedule、expected_updates，再以同一T_DD wrapper路由；保留现有36步默认，补一个18/19实际网格的tiny请求，并做Linux生产入口证明。不重构sampler，不改vendor。若要求恰好18个实际更新，则需要requested17和独立协议决定；当前底层拒绝17，本manifest没有暗改为17。故本卡技术就绪/执行权限均false。报价按现有k18语义的19D计；预计T_DD136.90s较R18C130.09s高约5.2%，不能预称严格同预算。完整报告实测T_DD差，不从结果再选k。

主终点：每prompt的 ΔAlex = LPIPS(R18C, 同seed Native36) − LPIPS(F17, 同seed Native36)，10prompt等权均值、prompt-level paired percentile bootstrap95% CI（100000次，固定seed20261105）及逐输入方向。**better成功：mean<0且CI上界<0**。未达到时，另报预写的次要非劣界限+0.01，CI上界<0.01才标SECONDARY_NONINFERIOR；否则INCONCLUSIVE，不把它改判为主终点成功。不进行布局/阈值重选。

次要完整报告：(a) mean LPIPS是否R16C≥R18C≥R21C；(b) **先完整列冻结预测与测量误差，再给判定**，预测0.932/0.825/0.652是旧四输入mean ratio，原样转移为十输入的固定预测，报告新mean paired ratio及绝对偏差、逐prompt绝对误差均值；不冒充新prompt专属预测；(c) R18C与k18配对Alex/T_DD；(d) 所有角色逐输入和均值T_DD。只在实测时间可比时作同预算解释。

报价固定为T_request=70.734852+6.772260·nD+0.993956·nA+0.637948·nC（本卡全light C，C项0）。Native36按36D，k18按实际19D；旧N05的Native18 mean_seconds=167.938s未绑定当前CAL35完整请求时钟，不作为同协议锚。中心=1.1×请求合计+1200s；范围0.9×–1.2×合计+1200s。62请求正式报价 **4.409281749555557GPUh**、工程范围 **3.6682002193333347–4.779822514666669**，建议硬限 **5.0GPUh**，尚未获执行批准。CPU评分另在释放/唯一结算后进行，不计GPUh。

未来仅一次实际预留/启动及含失败费用的唯一结算；拒绝/失败不换输入、不缩分母、不自动重跑。50GiB宿主内存、90°C、4GiB磁盘门限和40g容器保持；预计16GiB私有输出卷足够62份MP4/终点latent，不保存Native逐步状态。只安排人工半程与最终验收，不持续监控、不建例程。
