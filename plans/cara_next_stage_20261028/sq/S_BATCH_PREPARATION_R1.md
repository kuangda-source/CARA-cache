# S 整卡上限编排与 CPU 接续

2026-10-29。单路径 S 采集及存储的双端原 CPU 接受保持。新增整批入口把原上限 2 warm + 4 OFF + 4 ON 接到同一生产采样器，当前仅准备受限 CPU 验证；新 S GPU 卡、预约和真实标签仍为零。Q1 的固定源包与待回答授权问题保持。

## 固定上限与实际执行分母

[新入口](../../../src/wcomr/sq_s_batch_r1.py)枚举两个旧 FIT、两个固定父策略 Shared25-C/F19-C；正式四组 OFF/ON 的先后次序预先交错，两次 warm 均关闭采集。每请求完整 36 pair，不增加 Dense-hidden head 重放或 Q25 raw。

| 上限矩阵项 | pair 数 |
|---|---:|
| 10 条父轨迹的 D | 220 |
| 10 条父轨迹的 C | 140 |
| ON 的独立 Dense teacher | 56 |
| 实际 D 的 pre-D C shadow | 52 |
| 合计 | 468 |

上限共 936 次分支读出，产生 108 行矩、八个 F19 raw、24 个去重锚点。各项包含两次 warm；组件内部的 shadow 事务、恢复、哈希、CPU 传输和流式 I/O 仍须另计墙钟费用。真正 GPU 报价前必须完成相容 OFF/预热原件复用审计，再冻结去重后的实际矩阵；本文件不直接授权跑满十条。

## 新接口边界

每请求立即将全 36 guided 与最终 latent 转为完整字节摘要，保留原实际动作；完整批次元数据不长驻全部轨迹张量。四组 OFF/ON 核对全部 93 帧解码 RGB，采用 pinned `save_img_or_video` 的 float/BF16/uint8 像素转换；编码文件 SHA 独立记录。七项本地控制覆盖真实 writer 源码转换、完整矩阵/分母、RGB 失配、资源预检失败、缺行/短 guided/错误 CPU 身份、禁止复跑，以及 Q1 权限不能进入真实 S 入口。

批次第一次尝试即消费本 adapter；资源预检或任何请求失败均保留状态与片段，禁止从中间重试或续跑。108/56/52、十路径、四 OFF/ON、八 raw/24 锚点全部齐备后，才发布 data-only 完成元数据；GPU 释放/财务/独立终态接受与后续 S 掩码选择仍属外层流程。真实 S 入口要求单独 source/scope/launch/GPU 绑定的 S 权限上下文，不继承 Q1。

[CPU 范围](S_BATCH_CPU_R1.json)为两个 flow 设置各十条完整路径，共 20 条；小权重、真实 pinned WC/RF/UniPC 与占位 decoder/writer，GPU 隐藏、禁网、2 核/8 GiB、1800 秒、64 MiB 文件限制。每 flow 用原流式存储上限 16 MiB/8 MiB，重载 140 文件，双 flow 合计 80 次 tiny tensor 读取。原 owner/采集/存储阶段不重派，真实权重与外部 tensor 读取禁止。

同一源码 `6035fe2f` 的[双端整批 CPU 接受](../../../reports/cara_sq_s_batch_dual_cpu_accepted_r1_20261029.json)已完成：每端七项控制、两个 flow 共 20 完整路径；每 flow 实际 head 936、深层 block 552、四组完整 OFF/ON，140 文件重载，两 flow 合计 280 文件、80 次 tiny tensor 读取。独立接受器每端另拒绝十二类缺项/篡改/越界回执。全部实际 S 标签和 GPU 提交仍为零。

两卡 worker 墙钟 162.34 秒、父进程 CPU 156.32 秒、父峰值 RSS 0.890 GiB；容器墙钟 168.71 秒。四卡 worker 墙钟 762.71 秒、父进程 CPU 206.45 秒、父峰值 RSS 0.823 GiB；容器墙钟 894.86 秒。四卡结果写出后约 130.65 秒才完成进程退出，原 Inductor 子进程、读盘与退出状态均保留；直到容器退出 0 后才接受。编译子进程 CPU 未完整计量，按容器 2 CPU × 实际墙钟保留全部子进程分配上界，不能把父 CPU 当总 CPU。两卡一次读取断开后仅恢复原容器，未重派。

[复用候选审计](../../../reports/cara_sq_s_collection_reuse_candidates_r1_20261029.json)已找到旧 DEV128 的 `DIAGNOSTIC_SHARED25_C_0_1`：AV28 的完整 36 guided、latent 与 93 帧已接受 RGB 控制。它仍待源/模型/输入/策略/精度、实际文件身份、主机及摘要协议匹配；旧解码文件 RGB SHA 与新入口的编码前像素 SHA 不能直接混用。B1 的完整 OFF/ON 布尔接受不等于保存了全 36 guided；A32 F19-C 预热关闭 guided 审计；CAL66 Shared25-C 属于 QUALITY。当前不据这些较弱元数据自动减少路径，也不提前断言没有可复用原件。

下一步先完成该候选资格审查和实际矩阵去重，再按[真实几何解析下界](../../../reports/cara_sq_s_resource_analytical_floor_r1_20261029.json)补齐字段清单、物理峰值边界与双端完整工程报价。CPU fixture 限额不用于真实卡；GPU 外层权限/独占/费用/终态入口仍须继续接齐，双端整批 CPU 接受不代表完整 S GPU 卡已就绪。
