# GPU资源等待期间：N10固定资源单次SCP在途

2026-10-18。N09完整40的实际CPU已接受，但两张服务器GPU被其他账号占用，未启动生成或产生费用（[567](567_WC_N09_REAL_CPU_ACCEPTED_EXTERNAL_GPU_OCCUPANCY_AND_NO_CHARGE_20261018.md)）。当前继续完成N10多维自动质量评价的资源前置条件，不以准备工作代替质量结果。

## 本次实际进展

已重新恢复本机iCloud占位的原ViCLIP文件；原完整R4资源在新launch中按完整文件重新验证大小及SHA。没有另换模型版本或修改原权重。本地Git冷对象亦经物化恢复，原提交 `f06ca5a` 已正常推送；没有重置或改写Git历史。

**原固定资源SCP已于北京时间01:01:29.445038单次启动，原本机worker81517，lstart为01:01:29。** [本机初始身份观察](../reports/wc_paper_N10_original_SCP_R1_initial_local_identity_20261018.json)确认原PID／lstart／命令仍一致且活跃，原server-prepared回执存在。未提前执行最终collector或查询方法质量。

| 身份 | 值 |
|---|---|
| source | `f06ca5a5ce31c87579f09e1c602a4bb0d847fcf0` |
| 本机及服务器独立相对目录 | `.sync/wc-N10-viclip-relay-r1-20261018` |
| 权重 | `ViClip-InternVid-10M-FLT.pth` |
| 完整字节 | 1,710,545,812 |
| 固定SHA | `7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56` |
| worker SHA | `76c9e79e5c4d4c15eaffa0835c390e12c4b8dd65fa1287a1300a82345bae3643` |
| local registration SHA | `dca306cbc9a494a339b89a40262cc91898b34368df14e31bbd03f72deadc8b14` |

[原启动回执](../reports/wc_paper_N10_ViCLIP_original_SCP_R1_launch_20261018.json)保留全部范围、单次producer身份和源。原SCP仅写自己的新服务器目录及 `.part`；传完由原worker做全SHA再改为正式名。不写模型runtime、GPU锁或账本，不操作其他账号进程。

## 两次离散查收

预计完整传送与验证10–30分钟，已创建同一聊天的两个一次性查收：

| 项目 | 最早原时刻 | 实际安排 | 内容 |
|---|---|---|---|
| 半程 | 01:16:29.445038 | **01:17** | 原Mac身份、两源码SHA、技术退出及一次远端注册／part大小；不做大权重SHA或模型加载 |
| 最终 | 01:31:29.445038 | **01:32** | 原句柄／SCP／relay终态，独立服务端完整大小及固定SHA |

自动化ID分别 `worldcache-n10-scp`、`worldcache-n10-scp-2`。半程入口有[三项本地安全控制](../reports/wc_N10_relay_midpoint_local_safety_controls_20261018.json)，仅验证早于时刻／源码失配不查询及技术快照不接受资源，不冒充真实传输测试。每次查收后删除相应自动化；若最终仍在执行，按实际剩余字节另约一次，立即结束当轮，不循环等待或重复SCP。

原N09未准入任务的02:56／05:31自动化已删除，不与本资源任务混用。当前服务器全文件独立接受仍待；partial字节、producer摘要或SCP退出0不能替代完整接受。

## 接续完整五模型CPU

原资源全部接受后，使用真实server资源capture调用 `launch_wc_N10_models_cpu_r1.py`，在新独立目录验证全部五角色：DINO、AMT_S、RAFT_THINGS、ViCLIP、MUSIQ_SPAQ。使用固定源码和完整权重、FP32／eval／CPU、离线、两线程，分别验证真实输入及有限输出；全部模型都尝试，保留失败，不缩成四模型。

实际长CPU从真正派发安排一次半程和约15分钟后的完整验收，不循环监听。N09实际GPU部署诊断期间不运行重模型CPU或评分；目前N09没有在途GPU，其他账号GPU不动。

质量范围保持N07 R2全部160正式×6维＝960位置：645待评分（全部129个接受视频×5维）、155视频不可用、160静态N/A。实际五模型CPU全部接受后才重建可生产评分身份和完整报价，不把资源或CPU通过写成自动质量分数。当前新质量分数仍0。

本任务GPUh为0，同一累计账本仍110.869061155/cap226、预留0、可用115.130938845；历史和origin不变。N12原正负结果保持，连续A完整24仅设计／静态计划，F/B关闭，P和历史网络后置，无训练、人评或OMR。
