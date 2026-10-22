# 完整历史与整理前快照

2026-10-22将阅读入口从长期累加日志改为统一生成的研究导航。历史没有删除：编号研究记录、机器原件、配置、实验脚本与Git提交均保留；以下11份被重建的入口和索引额外保存了原字节副本。

- [完整研究记录索引](../HISTORY_INDEX.md)：按编号回溯问题、实验、结果和失败/修复。
- [机器回执目录](../../reports/)：原始启动、观察、接受、分析与费用。
- [整理前清单与SHA256](20261022_before_navigation/manifest.json)：11份文件，共5,805,273字节。
- [当前状态](../../research/02_CURRENT_STATE.md)与[科学实验总表](../../paper/EXPERIMENT_MASTER_TABLE.md)：了解最新已观察进展。

## 入口快照

源commit：`ed07cea91f56aa3f27cddc765bad70a71c273b71`。原文中的“当前”均指当时，不能代替现行状态。副本保留原来的全部相对链接和原字节；要沿原路径阅读，使用下表“原commit阅读”链接。

| 原文件 | 原字节副本 | 原commit阅读 | 字节数 |
|---|---|---|---:|
| `README.md` | [原文](20261022_before_navigation/README.md) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/README.md) | 178,450 |
| `EXPERIMENT_REPORT.md` | [原文](20261022_before_navigation/EXPERIMENT_REPORT.md) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/EXPERIMENT_REPORT.md) | 761,030 |
| `research/02_CURRENT_STATE.md` | [原文](20261022_before_navigation/research/02_CURRENT_STATE.md) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/research/02_CURRENT_STATE.md) | 686,433 |
| `research/09_NEXT_ACTIONS.md` | [原文](20261022_before_navigation/research/09_NEXT_ACTIONS.md) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/research/09_NEXT_ACTIONS.md) | 715,149 |
| `memory/handoffs/LATEST.md` | [原文](20261022_before_navigation/memory/handoffs/LATEST.md) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/memory/handoffs/LATEST.md) | 811,907 |
| `AGENTS.md` | [原文](20261022_before_navigation/AGENTS.md) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/AGENTS.md) | 691,041 |
| `paper/README.md` | [原文](20261022_before_navigation/paper/README.md) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/paper/README.md) | 26,045 |
| `paper/EXPERIMENT_MASTER_TABLE.md` | [原文](20261022_before_navigation/paper/EXPERIMENT_MASTER_TABLE.md) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/paper/EXPERIMENT_MASTER_TABLE.md) | 193,989 |
| `paper/INTERNAL_TO_PAPER_MAPPING.md` | [原文](20261022_before_navigation/paper/INTERNAL_TO_PAPER_MAPPING.md) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/paper/INTERNAL_TO_PAPER_MAPPING.md) | 121,353 |
| `paper/experiment_master_table.json` | [原文](20261022_before_navigation/paper/experiment_master_table.json) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/paper/experiment_master_table.json) | 900,791 |
| `paper/internal_to_paper_mapping.json` | [原文](20261022_before_navigation/paper/internal_to_paper_mapping.json) | [按原路径阅读](https://github.com/kuangda-source/CARA-cache/blob/ed07cea91f56aa3f27cddc765bad70a71c273b71/paper/internal_to_paper_mapping.json) | 719,085 |

`manifest.json`还记录整理前src/scripts/tests/configs/manifests/reports/plans的Git树对象，用于核对本次整理没有改动实验执行层。归档文件校验包含在文档生成器的`--check`中。

[本次整理的独立校验](../navigation_validation_20261022.json)：54实验ID、1482条原证据引用和54方法身份保留；11份原文逐字节一致，919个本地链接有效。校验同时确认执行层七个目录未改，未连接实验服务器或提交GPU。
