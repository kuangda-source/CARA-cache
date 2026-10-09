# P0 四CAL真实整组完整卡与生产CPU（2026-10-10）

真正部分MLP已通过[完整原管线CPU](225_WC_P0_COMPLETE_GROUP_PIPELINE_CPU_PREPARATION_20261010.md)，接下来在真实Cosmos-Predict2.5-2B上验证中间刷新动作。完整卡`WC-MF-P0-REAL-GROUP-R1-20261010-A`／`wc-mf-p0-real-group-r1`保留四原seed0曝光CAL、采集OFF/ON八完整36步父、八视频槽与8同状态起点12/30。真实过去D7／25缓存四层4／10／16／22两CFG未gate投影；完整deep attention与当前gate保持。原输出＋六模式、共同128块，0.5／0.75实际活跃15488／23296，随机／轮换同配额。

每起点全部六模式一次warmup与三次完整整组测量，共192双CFG score-only整组、384深层branch／9984 Block／384head；保存112 post-RF诊断分支与288父guided／八latent，16完整tensor文件。观测两Linear实际行数，dense原参考／dense+P0逐值相同，全部外部与额外projection实际恢复；teacher/P不更新WC锚点、不自动成为RA零风险来源。整组计时支付掩码、索引传输、gather/scatter／缓存/provenance、全attention／head／RF；完整诊断wall支付所有状态复制、哈希和写盘。不是P视频、在线选择或干净速度。

[完整费用预测](../reports/wc_p0_real_group_r1_complete_cost_forecast_20261010.json)从最近全部八父最大219.918秒加50% P0维护、八真实起点最大3.324958秒deep教师与额外head诊断的三倍作为每整组预测，并给全部256完整恢复各10秒、原慢load620.284秒、父／112分支写盘和清理独立费用，再全卡30%余量：**3.171450188 GPUh**。是可核查的经验预测，不是硬时间上界；旧慢loading来源保留，不能把最新单场景最快值代表全部，也不删warmup／重复／场景来满足4h。

245源码／资产／完整CPU原件和新登记均绑定。新生产runner、监督器／锁／账本、CPU-only审计与部署源已写，本地AST通过；实际生产源资产／请求／27拒绝CPU与选定绑定仍待，然后fresh GPU UUID／VRAM／compute进程／共享锁／账本准入，只派发完整卡一次。旧A冻结运行不改，全部原件已终态验收。当前仍无新GPU。

实费33.19208302866151／77.89524658965853，追加48窗口余44.70316356099702GPUh、71 GPU提交；单次完整≤4自主、>4具体确认。旧6.704／16路未批，不追认。下一真实整组→BASE-R＋A／P0与来源感知联合选择，原W1正负、RA工作点和稀疏条件保持，非必要无人评，goal active。

## 生产CPU与源绑定选择

source aad7b47的245完整源实际生产CPU32.712577秒退出0，3896046／3896047消失；真实guardrail cache／Blocklist／四原CAL请求、原模型／源码／资产与完整27拒绝通过。预算SHA保持，CUDA未初始化、GPU0。选定配置只加入同源CPU回执SHA和目标GPU UUID，static config binding不变；实际选定CPU与fresh资源仍待，不把选择配置称为GPU启动。

## 最终选定引用失败与独立配置R2

R1最终选定CPU32.905929秒退出1，3896321／3896322消失，原回执全部保持、GPU0。配置production_cpu_stage误留旧A目录，selected验证发现目录原件SHA与P0的CPU回执SHA不匹配并拒绝。生产CPU本身通过与完整P0 sampler科学边界保持；不跳过该绑定门。独立production／selected配置R2引用新的P0生产CPU R2目录，新增五个版本化部署／捕获／选定／启动／终态工具，payload250。P0算法、真实runner／supervisor／audit源码、实验范围、GPU run R1身份与3.171450188全cost不改。重新完成同源生产／selected CPU与fresh准入后才启动GPU；R1配置与全部原件不覆盖。

独立R2 source7ef8e6d的250源实际生产CPU32.386399秒退出0，3896685／3896686消失；27拒绝、真实源资产与完整四请求均通过，budget SHA不变。修复后的新静态binding为df45b7feeabf757bbb3a413ad8c54a0876c34afa26d27105ae59d2bf5e15a561，R1错引用／原成功均不改。R2选定配置只添加目标UUID与R2实际CPU原件SHA；最终实际选定CPU和fresh准入待，GPU仍未提交。
