# 文档维护规则

统一入口遵循“结果写一次，多个视图生成”。日常运行日志写到独立研究记录和机器回执，README、概览、状态与总表由规范数据生成，避免彼此出现不同的“当前进度”。

## 三类规范数据

| 内容 | 唯一维护位置 | 更新方式 |
|---|---|---|
| 当前观测、活动实验、原件指针、检查安排、首页结果 | `docs/project_status.json` | 实际新回执到达后更新观测时间与引用；不以文档生成时间冒充新观测 |
| 科学实验ID、范围、结论、后续、全部证据 | `paper/experiment_master_table.json` | 更新对应行；新增实验添加新ID；保留原ID和全部`evidence_refs` |
| 论文名、内部名、配置与源码对应 | `paper/internal_to_paper_mapping.json` | 保留版本身份；运营历史统一引用归档与当前状态 |
| 页面叙事与结构 | `docs/templates/*.md` | 修改模板；`__`映射路径层级 |

生成器从启动/观测原件提取运行身份、范围与完成量，校验同一launch/source/config/UUID；活动行及`operation_policy`一并同步。`status_counts`、最新映射SHA及已有导航文件hash绑定自动更新。旧证据绑定仍指向原来版本，不能当作所有历史文件当前内容相同的保证。

## 一次有意义的更新

1. 保存新的独立研究记录与唯一机器原件。失败原件、原费用、完整分母持续保留。
2. 更新规范状态和对应实验行的`reader`简明结论。`reader.evidence_refs`选1–3个最有帮助的阅读入口；完整`evidence_refs`仍保留全部。
3. 对首页关键数字或科学判断的修改，在`headline_results`中同时给出结果、范围与证据。当前快照字段只陈述已观察事实。
4. 执行生成与检查：

```bash
python3 docs/tools/render_repository_docs.py
python3 docs/tools/render_repository_docs.py --check
git diff --check
```

5. 检查差异：源码、运行配置、已有原件与正在执行stage不因文档变更而改变。明确暂存目标文件，排除私有transport日志、权重、视频、大张量与凭据，提交并同步GitHub。

生成器只读本地回执和Git文件列表，不连接服务器、不提交GPU、不写账本、不管理自动化。`--check`只读；会拒绝输出漂移、重复实验ID、错误跨run拼接、缺失证据、损坏归档或坏链接。它不是新的实验验收。

## 历史维护

2026-10-22整理前的11份长文档/索引按原字节保留，详见[归档清单](archive/20261022_before_navigation/manifest.json)。不要修改这些文件或修复其相对链接；使用归档入口的原commit永久链接按原路径阅读。编号研究记录、机器回执、配置及代码历史都保持。

新的研究记录先加入Git索引，生成器才会将其列入`docs/HISTORY_INDEX.md`。旧记录中的“当前/待执行”属于记录当时，不能覆盖规范状态。历史设计专用验证脚本仍绑定当时的计数与结构，例如v6的48行检查；它们不是新54行导航的验证器。
