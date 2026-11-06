# W3完整执行草案与原件只读复审

2026-10-04。接续[114完整核心与LPIPS CPU](114_WC_RV0_FULL_CAUSAL_CORE_LPIPS_CPU_AND_13H_GATE.md)。本轮完成本地生产入口、监督与费用结算、独立终态审计和全视频CPU评分接口；旧CPU原件及资源已通过服务器原生哈希复读。在实际服务器验证这些新入口、冻结部署及fresh准入之前，仍不提交GPU。原[104点r4](75_WC_FULL104_R4_CARD_AND_RESULTS.md)已独立完成1153.547616秒/单次1800秒，不能再次使用这个执行身份。

## 完整范围和实现

[当前未选执行草案](../configs/wc_rv0_causal_r1_draft.json)绑定62份payload和9份官方源，固定两曝光CAL、两CFG槽位、8个完整父轨迹、24条14更新/28CFG完整后缀、18个编码输出。父轨迹保留Native、cache-off Native、原WC/router absent、WC/router OFF；每场景保留OFF1/OFF2、C/C、D/D及交换执行顺序控制，新增的两条OFF完整解码桥也在输出分母内。v1/v2/v3未选草案与R1合同回执保留各自源码身份，没有实际执行或追认旧源码。

- [执行入口](../scripts/run_wc_rv0_causal.py)：继续调用已验证的完整核心；独立源码/资产/模式/输入检查，actual CUDA、模型/attention结构、原WC配置、完整失败分母及退出回执。旧profile仅复用资产检查函数，不调用其GPU入口。
- [监督器](../scripts/supervise_wc_rv0_causal.py)/[执行合同](../src/wcomr/rv0_execution.py)：共享f1锁、fresh UUID/sm86/显存/compute/磁盘/无inflight检查、唯一run/PID/log，6900秒全wall预付、6870秒child、kill5及30秒释放余量；按实际失败/退出/释放费用结算，超限费用也原样记录，不裁成预算上限。
- [独立终态审计](../scripts/audit_wc_rv0_causal_terminal.py)：检查完整输入/输出/deep/solver/状态轨迹、C/D同输入与真full历史、父恢复、五pipeline事件、18个原视频、源码、费用、原PIDs/锁/GPU释放；成功才允许评分。真实模型deep为26，CPU夹具的2层不能替代它。
- [视频读取](../src/wcomr/rv0_video_reader.py)/[评分计划](../src/wcomr/rv0_evaluation_plan.py)/[LPIPS评分入口](../scripts/analyze_wc_rv0_causal_lpips_cpu.py)：18文件SHA/长度前后检查，严格93帧432×768 RGB及源PTS/timebase，8份C/D分别对匹配Native、两OFF编码/时间戳桥、4份有符号J_C−J_D。评分在GPU释放后用隔离LPIPS CPU；模型初始化失败也保存评分分母。保留负值，不产出正式预算训练标签。

读取命令采用`-fps_mode passthrough`，对应官方保留源帧/时间戳的模式；ffprobe逐帧检查使用`-show_frames`。[FFmpeg文档](https://ffmpeg.org/ffmpeg.html)、[ffprobe文档](https://ffmpeg.org/ffprobe.html)。本地没有Torch/LPIPS/ffmpeg/ffprobe，这些新的实际解码与模型导入命令尚未执行，不能用文档或RGB流夹具冒充实际主机兼容性。

## 原件复审已经完成，私有代码没有发送到服务器

114记录的两次自动审批拒绝针对向现有服务器发送私有审计脚本，拒绝原件保留。[本轮原生只读回执](../reports/wc_rv0_native_readonly_hash_audit_20261004.json)采用服务器已有`sha256sum`复读固定文件、`cat`读取公开PyPI发布元数据；没有上传、远端执行本地私有代码或修改共享环境。自动审批批准此不同的只读操作。

[本地证据审计器](../scripts/audit_wc_rv0_returned_native_hashes.py)从实际返回CPU原件重建canonical SHA，独立核对62文件集合及每个观察SHA：R3原件、40阶段文件、9官方源、旧R4原件、LPIPS原件/协议/wheel/四package源/两权重、权威预算及直接授权。官方PyPI公开metadata另读且SHA与首次返回相同；published wheel SHA/53763 bytes与原件和远端wheel SHA一致。wheel长度依据发布元数据和完全相同的文件SHA，没有冒称又做了远端stat。

[完整CPU原件审计](../reports/wc_rv0_causal_cpu_native_audit_r3_20261004.json)重新检查全部16父/48后缀/36 mock输出及两个失败恢复控制，绑定274.090秒的实际R3 CPU和完整源码；[LPIPS资源原件审计](../reports/wc_rv0_lpips_resource_native_audit_v2_20261004.json)核对7.315秒实际预训练CPU回执、归一化/重复/四拒绝和隔离权重。判断在本地执行，`remote_original_and_stage_files_rechecked=true`仅指既有原件的原生哈希复读；不指新生产入口部署或真实C/D视频验收。

两份审计现以本地仓库报告绑定到未选草案，服务器项目里尚未同步这些新报告/入口；实际stage门仍会检查每一文件。旧传输拒绝不再阻碍既有原件复审；**新私有生产代码的服务器同步仍需明确许可，不能用这次原生只读批准替代**。[审批问题的分项解决记录](../reports/wc_rv0_readonly_audit_resolution_20261004.json)。

## 本地CPU合同与科学边界

[R2合同回执](../reports/wc_rv0_execution_cpu_contract_r2_20261004.json)：35个范围/费用/回执/完整轨迹/视频流拒绝控制通过，另6个缺文件/错哈希/错公开metadata/误称上传或GPU的原生证据拒绝通过。两flow的完整mock评分计划各18文件/8 C-D对/2桥；93帧原尺寸RGB流完整、短流/多帧/错PTS/尺寸/fps拒绝通过；62源码SHA、10新Python文件语法、draft CLI均通过。实际费用账本字节未变，Torch和实际FFmpeg未执行、GPU提交0。

这些是CPU合同与资源证据。Native父使用原类主体加观察器，仍未证明无观察器的真实Native GPU parity；当前没有真实新C/D分叉/LPIPS视频分数、同预算RV标签、Head、CONF或质量/物理结论。107的稀疏刷新净收益未成立判断保持；W3固定WC近似器和dense路径，复杂稀疏路由/训练后置。

## 预算和下一门

[直接13h授权](../manifests/budget_authorization_20261004_wc_13gpuh.json)及原锁变更回执保持，现used11.022315686839217、45jobs、无inflight，余额7119.663527秒；本轮没有修改cap、费用或任务数。原104执行时仍按其12h/1800秒卡结算，后续预算变更不倒改该次历史。

[完整成本R3](../reports/wc_rv0_causal_scope_cost_r3_20261004.json)条件估6765.585233秒，拟6900秒全wall加15秒准入需6915，算术余204.663527秒。真实新C/D成本和峰值仍UNKNOWN，估算不是完成保证。草案`gpu_execution_selected=false`、UUID为空、预付/提交0；本轮不以旧104授权启动6900秒卡。

下一先在明确私有代码同步许可下冻结部署，实际CPU验证生产导入/源资产门和原分辨率93帧reader/PTS/隔离LPIPS评分接口；通过后才选单卡执行身份及fresh资源/锁/完整余额门，最多一次。任何失败保留8/24/18完整分母及实费，不自动重提；终态独立复读源码/费用/释放后再做8视频对的CPU评分。结果形成后再讨论同预算标签或方向决策；不追加训练、付费或人评。科学goal仍active，当前为实现进度。
