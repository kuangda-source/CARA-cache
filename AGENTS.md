# CARA-Cache 当前仓库规则

## 主线与导航

当前主线为 frozen generator v1 的终点敏感度 / 漂移区间代价 / 预算化 D-light-C 动态规划。R18C 为主要工作点，R16C/R21C 为辅助预算点；F17-A2+lightC 为强对照。先读 README.md、docs/MAINLINE.md、research/02_CURRENT_STATE.md、research/09_NEXT_ACTIONS.md 与 memory/handoffs/LATEST.md。

P/S/Q、完整伴随、ORR 和其他新增模块暂停。backup 中的旧优先级、待执行安排、完成过的授权均是历史快照，不是当前执行队列。保留的历史名称代码仅作为共享兼容依赖；不因此晋级旧方法。

## 数据和执行边界

- 冻结布局、原始 manifest、源码身份、回执和原分数不可回写。新版本另立身份，重用原产物时核对哈希，失败、拒绝、缺失及费用完整保留。
- 不以终结的实验授权重跑 GPU、评分或结算。UNKNOWN 先恢复原句柄；运行中源/config 不修改。不得擅动其他用户的进程、驱动或任务。
- 新实验必须有当轮明确范围、完整报价、资源准入和既有授权。本次仓库整理不授予实验、训练、GPU、预算、PR 批准或合并权限。
- 保留单 run 硬限、唯一预留和含失败费用的唯一实际结算；维护 running cumulative actual GPUh，原 16.5 GPUh 未知责任保留。单 run 报价 >8 GPUh 仍须用户明确批准，≤8 GPUh 也必须处于已授权范围。
- 保留 50 GiB 宿主内存、90°C 自动停止、4 GiB 磁盘低水位、真实 GPU 独占、GPU UUID/进程/锁/ledger 校验及原护栏。四卡维护禁令未被本次整理解除。
- 不创建 heartbeat、cron、automation 或持续监控。CPU 单元控制只证明实现，不证明视频质量、速度或方法有效。
- 固定队列交付率与共同可评质量分别报告；不填补拒绝质量、不替换分母、不把重用视频作为新样本，不把描述性 bootstrap 充当原完整优效/非劣门通过。

## 文件与维护

- 仓库公开。连接凭据留在 Git 外；不提交密钥、token、私有 transport 日志、权重、视频或大张量。
- 当前运行器与依赖保留原路径、原字节；不要为整理命名而改动运行逻辑。旧源码/manifest 哈希指向其原提交，不因树重排改写历史身份。
- backup/ARCHIVE_MANIFEST.json 映射整理前的全部 14084 个 tracked 文件。归档文件按原字节保留；回溯运行环境请用原提交建立独立 checkout，不能直接运行移动后的旧入口。
- 本次整理前的 README、AGENTS、导航生成器、规范数据及模板在 backup/legacy_20261106/ 中。该生成器属于旧导航体系，不再管理当前首页。当前维护方法见 docs/MAINTENANCE.md。
- 运行 `python3 tools/verify_repository_layout.py` 与 `git diff --check`。验证必须无服务器连接、无模型加载、无实验派发。只暂存本次确切修改，保留其他工作。
- Git 历史、旧分支和 PR 保留。不得强推、不可恢复删除或擅自批准 PR。

实现遵循既有 Python 接口和运行时，保持逻辑直接、命名明确；不为目录整理引入额外抽象、依赖或行为变化。报告只包含实际完成的验证与已知限制。
