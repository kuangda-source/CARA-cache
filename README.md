# CARA-Cache

**面向终点误差的预算化缓存刷新规划。** 在视频扩散推理中，用经验终点敏感度和缓存复用期间的特征漂移构造区间代价，再用动态规划分配有限的完整计算。生成模型无需重新训练；校准完成后跨输入复用冻结布局。

当前主线是 **frozen generator v1 的 D / light-C 规划**。R18C 是主要工作点，R16C / R21C 展示预算取舍，F17-A2+lightC 是内部强对照。实际完整计算次数分别是 **16 / 18 / 21D**。早期 G17/G19/G22 是不同候选，不能混为同一条预算曲线。

| 阅读目的 | 入口 |
|---|---|
| 方法、校准来源与冻结边界 | [主线说明](docs/MAINLINE.md) · [原始冻结说明](plans/cara_next_stage_20261105/generator_v1_frozen/FROZEN.md) |
| 最新逐输入质量、双时钟与费用 | [primary11 完整报告](reports/cara_primary11_r1_20261106/REPORT.md) |
| 所有已完成有效数据与拒绝 | [实验概览](EXPERIMENT_REPORT.md) · [当前状态](research/02_CURRENT_STATE.md) |
| 复核代码、原件和布局完整性 | [复现指南](docs/REPRODUCIBILITY.md) |
| 后续待验证问题 | [下一步](research/09_NEXT_ACTIONS.md) |
| 旧方向和完整历史 | [backup](backup/README.md) · [归档索引](backup/INDEX.md) |

## 已观测结果

冻结后八个共同可评输入（C01–C04、C06、C08–C10，每输入 seed0、93 帧）上：

| 方法 | LPIPS-Alex ↓ | 去噪＋解码秒 | 完整请求秒 |
|---|---:|---:|---:|
| Native | 0（自身参照） | 252.760513 | 320.387546 |
| F17-A2+lightC | 0.249523 | 131.658731 | 196.041889 |
| R18C | **0.165358** | **130.203213** | **194.655688** |

R18C 相对 F17 的平均配对差为 −0.084166，八个输入均改善。LPIPS 衡量对同输入 Native 的保真度。该统计条件于护栏接受且配对完整的输入；固定九输入队列三臂均交付 8/9，C07 三臂视频拒绝。原九/十输入完整终点仍不可评价。范围、逐输入差异、重用关系及描述性区间见[原始报告](reports/cara_primary11_r1_20261106/REPORT.md)。

本轮 11 请求已全部终结（9 成功、2 视频拒绝），实际 0.765736264 GPUh 已唯一结算。以上是保存的终态，不是服务器实时状态。本次整理没有运行实验或新增 GPU 预算。

## 仓库结构

- `plans/cara_next_stage_20261104/`：敏感度测量和共享运行器。
- `plans/cara_next_stage_20261105/`：校准诊断、冻结生成器、G17/AVSLC 和 confirm10 原始协议。
- `plans/cara_next_stage_20261106/`：已结束的 primary11 队列与后处理。
- `reports/`：主线原始结果及必要依赖；`src/`、`scripts/`、`tests/`：保留的共享实现与验证资产。
- `docs/`、`research/`、`paper/`：当前主线导航、状态与证据组织。
- `backup/legacy_20261106/`：旧方向、旧导航、历史结果与未被当前依赖闭包使用的工具，按原目录保存。

旧路径中仍有少量历史名称，它们是冻结清单、源码哈希或导入所需的兼容依赖，不代表重启对应方向。详见[保留清单](docs/RETAINED_DEPENDENCIES.json)。Python 包 `wcomr` 和原项目名保持兼容。

仅检查本地文件、链接、Python 语法和归档完整性：

```bash
python3 tools/verify_repository_layout.py
```

仓库为公开仓库；凭据、权重、视频和私有传输日志不进入 Git。P/S/Q、完整伴随、新增模块和 ORR 暂停。后续实验尚未因本次整理获得执行授权。
