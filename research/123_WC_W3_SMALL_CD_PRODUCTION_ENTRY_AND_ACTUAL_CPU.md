# W3 小 C/D：生产入口、结算、独立终态与全帧评分

2026-10-04；状态：LOCAL_AND_ACTUAL_HOST_CPU_PASS / INDEPENDENT133_HASH_AUDIT_PASS / GPU_NOT_SELECTED。

本窗口按[更新后的研究计划](../plans/WORLD_CACHE_W3_NEXT_WINDOW_20261004.md)推进。保留119的已有视频评分、121固定mask、122小C/D核心和原full RV0；不重跑未受影响的控制，不新增W1/W2/稀疏/Head/LoRA/专家训练或人评。

## 执行范围与来源

独立卡 WC-W3-SMALL-CD-R1-20261004-A / wc-w3-small-cd-r1：common call45/CFG0、human call46/CFG1，均由真实step22状态续推14次更新/28CFG至终点。每场景OFF1/OFF2/C_first/D_second/D_first/C_second，完整2父/12后缀/8新输出，使用2个严格兼容历史Native参考。

[V1核心配置](../configs/wc_w3_small_cd_r1_draft.json)和实际CPU67文件保持；新增[V2生产草案](../configs/wc_w3_small_cd_production_r1_draft.json)及[80文件CPU来源](../manifests/wc_w3_small_cd_production_cpu_r1_20261004.json)，没有覆盖V1或原8父/24后缀/18输出身份。历史FAIR源为1a22ac6ef5c31c3cf15998ee868d96fcc6ba6b54，当前GPU父必须逐项匹配历史WC的context/settings/36步网格及编码SHA，才可复用Native；CPU Toy不得绕过生产桥。

## 本轮完成的代码与本地验证

四个独立入口：run_wc_w3_small_cd.py、supervise_wc_w3_small_cd.py、audit_wc_w3_small_cd_terminal.py、analyze_wc_w3_small_cd_lpips_cpu.py。生产源使用真实项目根账本与锁，冻结stage/assets/source/CPU原件及LPIPS资源；原官方代码不改。

监督器保留fresh UUID/VRAM/compute检查、全局f1锁、3900秒预付、3870秒child/5秒kill、失败/加载/flush/退出的实际结算与释放回执。终态审计独立核对完整raw轨迹、同输入Cdeep0/Dfull、重复与交换顺序、完整pipeline/编码桥、三句柄退出/锁释放/监控/费用；从原before账本重建预付状态，避免拿已结算status冒充原reservation。

评分在GPU释放及终态通过后用既有隔离LPIPS/Alex，对4条C/D视频分别计算相对Native的全93帧损失，形成2个有符号C−D诊断。报告各CFG full次数、所有后缀实际成本、父采样含控制成本及编码时间；负收益不删。这是自适应首动作诊断，不是同配额位置交换、同秒数/干净速度、物理正确性、正式Head标签或完整RV0。

[本地CPU结果](../reports/wc_w3_small_cd_production_local_cpu_r1_20261004.json)：80文件SHA/旧67保持、32项错误输入拒绝、原raw4父24后缀独立审计、完整评分清单8新+2旧/4对/2诊断、预算预付与实费重建/失败费用/并发账本拒绝、四CLI帮助与草案检查通过。没有Torch、模型、CUDA或真实视频生成；合成参考桥仅测试清单结构，默认GPU通路拒绝它。

## 实际服务器 CPU 与独立回读

已同步source **8ce97cd6f4c647cd0fbe9e86d7f9bd6291b26237**的80文件至现有服务器独立 `.sync/wc-w3-small-cd-production-cpu-r1-20261004`。实际[CPU回执](../reports/wc_w3_small_cd_production_actual_cpu_r1_20261004.json) exit0，总 **39.817510秒**：草案/32拒绝/raw完整轨迹合同、真实项目根13资产绑定及模型/guardrail文件身份、真实冻结Video2WorldCondition恢复与导入、新模块origin、四CLI帮助等7步骤通过。旧CPU适配仅在退出的检查进程中，官方GPU路径不改；未加载模型权重或创建CUDA context。

服务器原始回执SHA **af7bb5f2b8a34b7f639258db10f6e7d9b8da9f84c80a560a782d58e287c47e30**。随后仅用原生cat/sha256sum完成[133项独立审计](../reports/wc_w3_small_cd_production_actual_cpu_r1_audit_20261004.json)：80stage/9官方源/14日志/原件、旧core与metric CPU原件、真实根资产、LPIPS代码/linear/backbone、四旧Native/WC视频与账本SHA逐项一致；回读原件和实际import日志核对七步骤exit0、禁用CUDA/未加载权重。审计器没有向服务器发送私有代码。

本轮不重跑旧core、固定mask或旧GPU工作。这里完成的是实际来源/资产/接口准备，不是生产GPU监督器timeout/费用释放的实际演练，也不是当前GPU父历史编码桥、C/D视频或收益。

## 预算和下一科学门

13h累计账本used11.022315686839217、45jobs、无inflight，余额7119.663527秒，字节SHA597fa09593f75c89b191b3f94f45e9d26e048ddc63779e4c52aa4e94464f86e5保持。本卡3900+15准入包络在余额内；若花满剩3204.663527秒。名义2811.502秒、压力6109.684秒都是代理而非硬上界，压力超过cap，保留超时/拒绝/未成对分母，不承诺后续交换与确认共同完成。

生产CPU通过仍不等于真实GPU桥、C/D终点收益或方法有效。下一科学顺序仍为极小真实自适应C/D→最多四组合法同CFG刷新配额交换→有信号才冻结无训练规则和新seed/场景确认。沿用当前CPU限定范围，本轮不启动GPU、修改账本或新增人工评价。此前104点≤1800秒单次授权已经执行结清，不能将它复用到这张3900秒新C/D卡。下一实际卡须完成当前CPU阶段后的执行范围确认，再fresh选择A6000及VRAM/compute/锁/账本准入；无需重做已通过且来源相同的CPU控制。
