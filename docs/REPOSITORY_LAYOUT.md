# 目录整理与保留范围

本次在成功发布结果快照后，以正常 Git 提交整理当前主线；没有改写历史或实验运行逻辑。

| 类别 | 保留原位置 | 移入 backup |
|---|---:|---:|
| `.gitignore` | 1 | 0 |
| `AGENTS.md` | 0 | 1 |
| `EXPERIMENT_REPORT.md` | 0 | 1 |
| `README.md` | 0 | 1 |
| `cards` | 0 | 4 |
| `configs` | 23 | 133 |
| `docs` | 0 | 56 |
| `figures` | 0 | 21 |
| `inputs` | 8 | 0 |
| `manifests` | 19 | 519 |
| `memory` | 0 | 21 |
| `paper` | 0 | 35 |
| `plans` | 112 | 523 |
| `pyproject.toml` | 1 | 0 |
| `reports` | 387 | 7679 |
| `research` | 0 | 1056 |
| `scripts` | 64 | 1993 |
| `src` | 256 | 436 |
| `tests` | 22 | 712 |

合计：893 个原文件保留、13191 个原文件归档。旧导航文件的原字节在 backup 中，新主线导航另行创建。

保留范围来自当前主线 plans、校准/验证报告、源码导入和显式本地路径的保守闭包。部分历史名称 helper、配置和 tiny 控制因此保留；它们不是当前研究队列。详见 [保留依据](RETAINED_DEPENDENCIES.json)。

完整恢复关系见 [归档清单](../backup/ARCHIVE_MANIFEST.json)，历史阅读入口见 [归档索引](../backup/INDEX.md)。源码、冻结配置、评分、账本、护栏拒绝和失败回执原字节均可核验。

旧导航体系整体归档；后续使用 [维护方法](MAINTENANCE.md) 和 [本地核验](REPRODUCIBILITY.md)。当前外部模型、固定上游与原生成工作区限制仍保留，不因目录验证而视为齐备。
