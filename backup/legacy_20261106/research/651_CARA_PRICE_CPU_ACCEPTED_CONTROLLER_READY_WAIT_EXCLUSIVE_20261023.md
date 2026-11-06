# 完整价格CPU已接受，GPU控制器就绪，等待独占资源

原1624的误差标签、完整Native参照与6.900544 GPUh结算保持。独立价格补测的完整生产CPU现在已接受；一次性GPU提交/恢复/收件和独立终态接受控制器已补齐。新GPU提交仍为0，等待空闲卡验证硬件独占。

## 本次完整CPU验收

CPU仍绑定源码`cecba6647fcc626887761961fc7215c6fe1afa8b`、原stage和注册SHA`8b35974e725fa1fbb72fb5474f10c763edb998e4b59bd21f7775e44ed3c6a00b`。原容器实际于**09:46:34.233077**退出0，实际完整观察为**09:51:55.748323**，不是按预约时间回填。

- [09:45:39尚在运行的原回执](../reports/wc_policy_price_refresh_full1624_CPU_terminal_check_r1_20261023_0945.json)保留。
- [完整终态原件](../reports/wc_policy_price_refresh_full1624_CPU_terminal_check_r1_20261023_0955.json)与[独立CPU接受](../reports/wc_policy_price_refresh_full1624_CPU_accepted_r1_20261023.json)。终态文件名中的0955仅为标签；其`observed_unix`对应实际09:51:55。
- 两种flow完整48条CPU路径；新4060格、48720次价格读出；原4060格、26040次参照读出。全36步/最终状态/CPU RGB、原source/input/older-anchor、拒绝与清理、标签合并不变均通过。
- 实际Cosmos请求构造、NLTK、生产93帧writer/解码/ffprobe、继承FD/锁，以及14项单元检查均通过。原三命令bundle完整退出0。
- 同时绑定[六项生命周期CPU故障检查](../reports/wc_policy_price_refresh_lifecycle_CPU_capture_r1_20261023.json)。这些检查没有调用真实CUDA、sudo或GPU管理命令，不代替硬件独占验证。

这批CPU数值使用完整Toy流程验证实现，不增加真实视频实验样本。

## GPU控制器与独立接受

新增`scripts/wc_four_card_price_refresh_gpu_r1.py`及`src/wcomr/policy_price_terminal_r1.py`。它们操作已冻结stage，未修改其collector、runner、supervisor或host guardian。控制器以独立Git源码绑定本地执行/接受闭包；实际派发前要求该版本已推送，远端重新核对生产CPU文件、注册payload、runtime、旧参照、全卡报价及资源。

- `preflight`只读，不创建预约或获取凭据。`launch-gpu`再次准入后才写唯一intent并启动原host guardian。已有intent/launch只能recover，SSH UNKNOWN保留意图ID和原句柄，不重派。
- 密码只沿内存与stdin管道传给正常sudo，未进入参数、环境、Git或回执。只有选定UUID真正空闲才启用EXCLUSIVE_PROCESS。实际runner持有CUDA上下文后，核对唯一PID/start/UID，得到supervisor许可再加载权重。
- `capture`检查原进程、容器、当前UUID/进程、权威账本及锁；终态重新读取文件原始字节、SHA和全部93帧，并绑定原10路径。接受器重新核对2030格、24360次读出、原source/input/older-anchor和每格三轮，独立生成新bundle并确认旧标签不变。
- 费用必须与原账单SHA、实际墙钟和权威结算一致；整卡11.5 GPUh上限保持，cap226与旧16.5 GPUh未知责任保持。全部原进程及容器退出、UUID锁释放后才可接受。
- **运行前固定监测规则**：每次采样核对真实Exclusive_Process、无MPS、唯一原runner；监测记录之间及末次记录到GPU结算的间隔不得超过45秒。生产循环约2秒一次，单次驱动查询有15秒超时。缺口超过上限即不接受干净价格，保留原件与实际费用；不凭低CV补过。GPU结束后安全恢复模式，如外部进程已进入则延后恢复、不触碰对方。

[32项CPU检查回执](../reports/wc_policy_price_refresh_controller_terminal_CPU_20261023.json)覆盖完整合成终态、非最近格漏一轮、历史哈希变更、缺路径、错误上下文/MPS、监测缺口、账单未结算、原件修改和93帧缺失；也覆盖繁忙卡不取凭据、不提交，既有intent不重派，UNKNOWN回执不泄露凭据。合成计时只用于测试接受器，不作为实验结果。

## 资源、预算与后续顺序

[09:56:11–12四卡观测](../reports/wc_policy_price_refresh_fresh_resources_20261023_095612.json)中四卡均Default且有其他进程：GPU0 PID731146；GPU1/2/3分别PID848533/848534/848535。GPU3仍为UID1005（此前已核对为guanwenfei），13,408 MiB。

[完整只读准入](../reports/wc_policy_price_refresh_GPU3_full_preflight_20261023_1005.json)实际观察为**10:00:11.237415**，文件名1005不是观测时间。源码/CPU、原件绑定、完整预算、磁盘与内存核对均成功，唯一未满足项为`GPU_BUSY`。当时磁盘172,508,024,832字节、MemAvailable69,435,187,200字节。没有取sudo凭据、改模式、预留或启动GPU。

预算保持：已用125.646551890291 GPUh，旧未知责任预留16.5，可用83.853448109709，cap226。价格卡仍为4CAL/10路径/1624正式格/2030总格/24360读出/360pairs/720CFG/单load，预测9.500278、上限11.5 GPUh。

原CPU验收检查已完成；同一`cara-bank24-2`改为**10:30**检查独占资源与单次准入，不重复收原CPU或1624。若仍全占用则有界复查并保持安静；有空闲才fresh准入、合法sudo实测独占并单次启动，按实际返回安排半程/全程。若提交结果未知，先recover原句柄。

完整价格结束后先报告全1624格重复波动、顺序漂移和原聚合放大，再把新价格SHA与原标签SHA组成新bundle；保留旧bundle。随后依次推进PG-P1的CAL_SELECT曝光核查、合法mask生产CPU与全卡报价（B=.80、Q≤8）；策略冻结后小规模历史窗口shadow诊断不写回，PG-P2加入少步Native等实际时间对照，新增范围单独计费，不以DEV或部分结果调参。
