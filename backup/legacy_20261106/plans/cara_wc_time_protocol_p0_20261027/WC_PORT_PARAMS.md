# 配置到真实执行的映射

权威字段和值见 `CONTROL_IDENTITY_MATRIX.yaml.config_mapping/roles/schedule`，每个输入与schedule另有SHA；文件是合法JSON/YAML1.2子集。

| 项目 | 当前真实语义 | P0处理 |
|---|---|---|
| scheduler | UniPC/Karras，请求35、实际36次更新、72次CFG支路 | 绑定CAL66原sigma与timesteps，不改网格 |
| num_steps | generate_vid2world转为target_steps=35×2=70 | WC计数按CFG调用推进，70后reset，末2调用另记 |
| README tau / saliency / flow | .06 / 1 / 2 | 保留原始公开代码工作点 |
| PaperPort tau / saliency / flow | .08 / .12 / .5 | 通过apply_worldcache写入net实际字段 |
| README ATS | horizon70时原表达式产生base_mult=5 | 原样 |
| PaperPort ATS | base_mult=4，仍按cnt/70，保留分支奇偶/reset | 只替换该赋值，不声称Euler35语义相同 |
| Tuned | PaperPort上共享tau候选 .04、.06 | 两旧CAL有限搜索，不扩网格，不逐prompt选 |
| allD | 原wrapper所有probe、历史和head仍存在 | 仅skip predicate=False；不能用Native别名冒充 |
| RA | 本地clean_speed20 execute:RA | 阈值0.070744235098772；完整RA_spec与校准指纹入矩阵 |
| CARA | CAL66/DEV128完全相同Shared25-C policy | 指纹008d9fa12c7aad67e40440533a6e552147d79b82e44afebd8df55954f47b6e60，不改alpha/phase/layout |

RF源码SHA：c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87。
WC源码SHA：b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903。
适配在新模块 `src/wcomr/wc_time_protocol_p0.py`，不改上游。源码不匹配/AST位点非唯一直接失败，不静默套补丁。CPU已检查参数触达及编译AST指纹；CUDA实际行为仍待验证。

`WC_PAPER_PORT_U36`只能称论文参数的本地UniPC映射，不能称WorldCache Official/Euler35精确复现。RA本地适配同样单独命名。RA_spec里的D/C成本只供原动作排序，不能作为本轮端到端报价。
