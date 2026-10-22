# 复现与证据指南

本仓库同时保存研究叙事、冻结设计、实现代码和小型机器回执。可以先在普通电脑上核对“某个结论来自哪张卡、使用哪个版本、是否完整接受”；实际生成视频还需要已登记的模型、数据、运行环境与GPU资源。

## 从一个结果追到原件

1. 在[实验总表](../paper/EXPERIMENT_MASTER_TABLE.md)找到稳定ID，例如N12或X-S-GATE。
2. 阅读该行优先证据，确认比较方法、输入集合、正式/预热数量、拒绝与失败分母、统计口径。
3. 在[机器索引](../paper/experiment_master_table.json)中取该行全部`evidence_refs`；别名通过`source_refs`解析，直接路径原样使用。
4. 跟随报告进入launch → capture/terminal → independent acceptance → analysis/figure provenance。核对run、launch ID、source revision、config/registration SHA、原件哈希、Native参考和费用。
5. 需要重新生成时，使用该卡的注册表与实际生产入口；当前主分支是持续发展的仓库，不能替代历史卡绑定的source。

同一原件可被后续分析复用。例如CAL12四格引用N12/Window24已接受端点；这是有身份绑定的复算，不是新增独立样本。拒绝、技术失败、恢复和重试各有记录，成功的后处理不覆盖原始失败。

## 两个完整例子

**BANK24**：[644结果](../research/644_CARA_BANK24_COMPLETE_DEV6_RESULTS_20261022.md) → [启动](../reports/wc_four_card_BANK24_full24_GPU_retry2_actual_launch_20261022.json) → [恢复后的完整终态](../reports/wc_four_card_BANK24_retry2_recovered_terminal_20261022.json) → [独立接受](../reports/wc_four_card_BANK24_retry2_recovered_terminal_accepted_20261022.json) → [64组合门控分析](../reports/wc_four_card_BANK24_retry2_frozen_gate_analysis_20261022.json)与[X-R分析](../reports/wc_four_card_BANK24_retry2_XR_CPU_diagnostics_r2_20261022.json)。恢复的是CPU媒体库路径，GPU结果未重跑。

**完整1624资产**：[646记录](../research/646_CARA_FULL1624_CPU_ACCEPTED_GPU_LAUNCH_20261022.md) → [生产CPU接受](../reports/wc_policy_assets_full1624_fourcard_CPU_r2_accepted_20261022.json) → [唯一GPU启动](../reports/wc_policy_assets_full1624_fourcard_GPU_launch_20261022.json) → [观测快照](../reports/wc_policy_assets_full1624_fourcard_GPU_initial_sampling_20261022.json)。后续完整接受文件以[当前状态](../research/02_CURRENT_STATE.md)中的新证据指针为准；启动回执本身不代表采集接受。

## 本地阅读与校验

Python ≥3.9即可检查文档，使用标准库；无需安装Torch或获取模型：

```bash
python3 docs/tools/render_repository_docs.py --check
```

按ID查看全部证据引用：

```python
import json
from pathlib import Path
index = json.loads(Path('paper/experiment_master_table.json').read_text())
row = next(r for r in index['rows'] if r['id'] == 'N12')
for ref in row['evidence_refs']:
    print(index['source_refs'].get(ref, ref))
```

图表来源位于`paper/figures/`各批次目录；论文数字应从原分析数据取值，不从图上估读，也不将不同计时模式合并。

## 实际实验环境和入口

当前四卡执行使用已接受的独立stage与原生Python 3.10 / Torch 2.7.1+cu128包装器；历史主机Python 3.8与旧入口不等价。确切上游版本、资源路径、哈希、注册文件及CPU证明由对应launch/registration绑定。普通`pip install`本项目不是完整Cosmos生产环境的复现步骤。

- 配置与资产：`configs/`、`manifests/`、`plans/`，保留各卡固定source与角色。
- 完整1624控制器：[wc_four_card_policy_assets_r1.py](../scripts/wc_four_card_policy_assets_r1.py)。半程`capture --mode gpu-halfway`；终态`capture --mode gpu-terminal`后`accept --kind gpu`。两者都绑定同一`--launch-ref`，输出新原件。
- BANK24控制器：[wc_four_card_bank24_native_transport_r4.py](../scripts/wc_four_card_bank24_native_transport_r4.py)。已完成的BANK24不因阅读、制图或同步仓库而再次提交。
- 新自动生成器：[计划](../plans/cara_policy_generator_20261020/README.md)及[登记](../plans/cara_policy_generator_20261020/TASK_REGISTRY.json)。真实标签、动作价格和任意合法mask生产CPU分别接受。

模型权重、视频、原始大张量以及私有服务器连接不放入Git；其实际路径/哈希保存在回执和清单中。拥有仓库读取权限可以审查完整实验链；重新生成还需取得相应资产和服务器授权。报告中的服务器路径用于定位原件，不是可匿名下载的链接。
