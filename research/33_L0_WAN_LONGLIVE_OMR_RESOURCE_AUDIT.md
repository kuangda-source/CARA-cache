# L0资源审计：历史Wan5B资产可复用、适配器头结构匹配，OMR仍缺公开资源

2026-10-01；L0_PARTIAL_BASE_HASH_AND_HEADER_STRUCTURE_VERIFIED_NOT_ADAPTER_PAYLOAD_OR_GPU_READY。主线继续WorldCache成本/质量缺口，不自动切换Wan或OMR；新4GPUh计时窗口仍待用户决定。

## 实测资源与官方锁定

现有服务器Wan2.2-TI2V-5B ModelScope目录不凭目录名认版本；[新官方完整性manifest](../manifests/l0_wan5b_integrity_20261001.json)锁定HF revision 921dbaf3f1674a56f47e83fb80a34bac8a8f203e。[CPU完整核验](../reports/l0_wan5b_asset_integrity_20261001.json)重新hash全部11个实际推理文件：3 DiT shards、Wan2.2 VAE、UMT5 encoder、4 tokenizer文件、config和index，共34201521169字节（31.853GiB），全部官方LFS SHA256/Git-blob SHA1通过。监督CPU timeout2491891/runner2491892已退出，实耗207.093538秒，无GPU任务/账本不变。[终态观察](../reports/l0_wan5b_asset_audit_observation_20261001.json)。资产可复用，不代表本项目新前向或质量结果；不继承旧PhysCache实验结论。

[官方源码对比](../reports/l0_native_source_public_comparison_20261001.json)：现有独立Wan2.2 runtime入口generate.py、wan_ti2v_5B.py、requirements.txt与官方commit42bf4cfaa384bc21833865abc2f9e6c0e67233dc逐文件SHA一致（只证明这3文件，不宣称整个runtime清洁或已兼容LongLive）。旧顶层Wan工作区有其他未提交改动，后续用独立新路径，不修改它。

[官方LongLive源码/资源锁](../manifests/l0_public_resources_20261001.json)：NVlabs/LongLive commit fb16a879f46e604df4a0ca48ce2bf45adfa90352，README/merge_lora/inference/配置/相关wrapper9个源码逐Gitblob通过。两套公开模型分别固定：

| 适配器 | HF revision | safetensors字节 | rank / alpha | header结构匹配 |
|---|---|---:|---:|---|
| Wan5B CFG | 195c8c100e145d5b18068d506f8f2b4498dcaaa4 | 644949288 | 64 / 64 | 600张量/300 A-B目标全匹配 |
| Wan5B few-step | 38a6ec4e8f5b644749d3072bfe1ac383d00951c0 | 1289824400 | 128 / 128 | 600张量/300 A-B目标全匹配 |

仅取得官方HTTP Range的JSON headers（75040/75912字节），没有适配器完整payload或SHA验收。825个已有base tensor headers与完整index/shard覆盖一致，600×2 LoRA张量offset/字节量、key前缀/A-B pairing/target set/rank/dtype/shape/alpha-r逐目标通过。[可重放结构审计](../reports/l0_lora_header_structural_audit_20261001.json)/[输入锁](../manifests/l0_lora_header_audit_20261001.json)/[工具](../scripts/audit_l0_lora_headers.py)。结构相符不证明tensor finite/数值效果/完整payload/真实融合或GPU能运行。

本次配置普通linear LoRA、非rsLoRA/DoRA/rank pattern、alpha/r都1，官方联合配方few-step权重1.0/CFG权重0.5、sampler guidance1.0。CFG-only发布配置为50步/weight1.0；不能把CFG LoRA缩放与外部guidance混为一谈，或宣称与联合配方的有效guidance严格相等。发布few-step checkpoint metadata与训练README窗口亦不当作从头训练授权，使用实际冻结release。

## CPU实现与环境边界

[本地16项](../reports/l0_local_cpu_20261001.json)/[Linux16项](../reports/l0_linux_cpu_20261001.json)同范围通过，不合计为32。验证不匹配key/shape/rank、非普通LoRA、缺失pair、错误offset/payload长度或index覆盖不能误判兼容；真实两个headers在Linux重放完全一致。官方固定merge_lora脚本仅用小CPU tensor测试alpha/r非1、加法结果、辅助conditioning权重保留与shape错误先拒绝/不改base，CUDA未初始化；不是600完整适配器或真5B融合验证。

[环境盘点](../reports/l0_native_model_headers_environment_20261001.json)：历史Wan为Python3.11.15/torch2.4.1+cu121，当前Cosmos为Python3.10/torch2.7.1+cu128；官方LongLive README推荐Python3.12/torch2.9.1，requirements peft0.17.1/safetensors0.8.0等。已安装版本不等于支持；下一应新隔离环境/CPU import与加载适配验证，不升级共享环境。数据盘余约672GiB只代表存储，不是GPU准入；最新GPU1 24MiB/noapps也不代表L1已提交或显存够用。

## OMR当前状态与下一动作

2026-10-01实际匿名取回[OMR官方页](https://itruonghai.github.io/omr/)；release仍明确Coming soon，page SHA09a6ce6bfc3d834d9ca39c4178523222f527cb3ac2f9690225a977ac22082aae与旧记录一致。没有从此公开入口得到代码/配置/prompt IDs/官方adapter，因此PUBLIC_RESOURCE_BLOCKED，不写科研方法失败；也不推断用户私下资源或其他机器一定不存在。Wan5B LoRA兼容不代表WanA14B/CogVideoX OMR adapter可用，Cosmos也不是这些LoRA的匹配主干。

下一L0剩余具体工作：匿名获取锁定的两套完整适配器safetensors及JSON（合约[CPU3600秒获取](../manifests/l0_adapter_acquisition_20261001.json)/[全部SHA锁](../manifests/l0_adapter_integrity_20261001.json)），在新cache逐文件验证；CPU真实目标融合/新输出检查（不覆写底座）与独立环境/任务及scheduler接口验收。两适配器payload总1934773688字节，约1.802GiB，不下载重复generator_lora.pt。资源完整也不能自动开展L1；原4h只余1255.511794秒，2GPUh L1额度不能额外叠加；新GPU范围需其独立实测/方案与当前重大决策。

保留WorldCache primary、原机制only/代理无收益结论；无人评/付费/训练。GPU ledger仍3.6512467238638138/4h，未新生成。下一CPU资源获取可以独立推进，不把这份部分L0审计当完整准备或实验结果。

## 后续同日CPU获取启动

协议/source68afc3e与审计同步后，唯一CPU l0-adapter-assets-r1已提交，3600秒上限/匿名官方/固定release/新project cache；supervisor2493078/timeout2493079/downloader2493080都proc verified live，CPU lock held。CFG73400320字节partial/3JSON，few-step未开始，尚未完整SHA/真实融合。[启动](../reports/l0_adapter_assets_r1_launch_20261001.json)/[实时观察](../reports/l0_adapter_assets_r1_live_observation.json)。使用专用owned temporary loopback forward，仅CPU终态后按ignored本机PID identity关闭它；共享路线未改。继续同handles，GPU账本未变，不重复提交/修改在跑源码。

## 后续终态与真实CFG资源进展

L0 CPU获取r1因连接中断exit1/1218.181533秒终态，原3PIDs退出/CPU锁释放/账本不变；仅关闭本任务owned临时转发。CFG4文件完整官方hash、真实600tensor finite/300pair alpha-r通过，独立核验PIDs2495417/2495418退出；few-step保留167772160字节（160MiB），非完整payload。两配方分片CPU融合程序已实现，本地/Linux22同范围检查通过，尚未真实Wan5B融合/模型任务load/GPU。下一同固定release/cache/3600秒的新r2续传，不重启旧identity或改共享路线。

见[完整CPU融合准备与CFG验收](34_L0_CPU_FUSION_PREPARATION_AND_CFG_PAYLOAD.md)。早先header-only/live段落是历史快照，当前以r1终态审计与此新检查为准。
