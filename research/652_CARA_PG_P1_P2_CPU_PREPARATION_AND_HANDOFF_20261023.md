# PG-P1/P2的等待期准备已推进

**本轮完成CAL_SELECT曝光核查、可信价格到生成器的转换接口、历史失配诊断规则和少步Native计时选择规则。** 新增27项CPU控制通过，实际UniPC调度器的18–35请求步CPU网格也已保存。没有启动GPU、修改原价格stage、改变GPU模式或预算。

完整接续说明及机器规则：

- [P1/P2接续设计与命令](../plans/cara_policy_generator_20261020/P1_P2_CPU_HANDOFF_R1_20261023.md)
- [机器规则与分母](../plans/cara_policy_generator_20261020/P1_P2_CPU_HANDOFF_R1_20261023.json)
- [61项相关CPU检查（新增27项）](../reports/cara_PG_continuation_CPU_preparation_final_20261023.json)

## SELECT输入核查

在已提交的代码`b710be90`下，检查3127份本地JSON/gzip报告和四卡项目42份输出元数据，读错误0、未分类身份命中0、两个SELECT的远端输出命中0。[原核查回执](../reports/cara_CAL_SELECT_exposure_committed_20261023.json)保留每个已读文件的SHA及实际观察时间。

本地5个命中文件中：2个是完整数据目录/原请求字节检查，2个仅保存后续执行的自动化文字，另1个是本轮首次身份核查原件。没有发现`av_animal_dear_1_0`或`industry_057`的实际模型执行记录。原清单、来源组、prompt SHA与七份冻结曝光清单未变。

这是“现有本地记录＋四卡项目输出”范围内的无执行证据；没有重连两卡，也没有声称覆盖项目之外的未记录执行。第一次SELECT端点前检查新增执行元数据。SELECT只承担一次开发选择，不转称最终TEST。首次检查与提交后复查均保留，未回填时间。

## 接口已经补齐的具体问题

原资产bundle不能直接输入现有生成器CLI：它使用target/fit_members字段，还包含额外profile和成本描述字段。新增转换明确映射字段、验证1624唯一格和完整合法图，将原标签SHA、新价格bundle SHA及独立接受绑定。原资产的generator_input_ready不能覆盖已知价格竞争。

B仍为0.80×同profile干净Native。原计时受干扰，因此P1完整64路径卡内先测四CAL Native，再固定预算；SELECT Native在finalists冻结后运行。新比较同时保存core和完整请求计时，决策使用安装、普通guarded生成、写出、清理的统一完整请求口径。原component价格到完整请求的额外开销只在新消费文件中加一次，实际可行性由完整路径重新验证，原价格聚合与bundle不改。

## 历史失配诊断

固定WC源码确认C的OSI/启发式gamma和residual外推都使用两个真实锚点。因此在同一自身状态、同一个最近锚点下，将较早锚点从真实p换成邻接shadow s−1，能够单独检验历史因素。

规则已落实为矩阵生成函数：冻结最终CARA及强简单控制；原前两CAL、seed0；按刷新间隔2–4、5–8、≥9各取最早合法跳步，没有位置就保留空组。最多4正式＋2warm、36额外shadow D pairs、108 paired readouts；含普通路径共≤252 pairs/504 CFG calls。相同策略物理去重但角色不消失。所有shadow不写回，不能计入速度表。

实际固定WC skip/OSI/flow和ReadoutKernel在四种flow×OSI CPU组合下通过：换较早锚点时C/A_HALF改变、A_ONE逐位不变，输入和RNG保持。这里head/RF与输入是显式Toy控制；完整生产轨迹OFF/ON的36步、最终latent和93帧相等仍由后续真实CPU验证，未将局部控制升格为生产接受。

## 少步Native与后续比较

[真实调度器CPU原件](../reports/cara_PG_Native18to35_committed_scheduler_CPU_20261023.json)保存完整timesteps/sigmas、源码SHA；当前18–35请求步均多执行一次更新。历史视频入口仅支持18/26/35，因此扩展步数仍须其自己的生产CPU，不能只改一个num_steps就派GPU。

选步只读CAL时间：从实际更新数比例预测中固定4个近目标整数步，再完整测四CAL×3轮及每方法2warm。先重计冻结CARA和Native35的同卡参考，两部分总上限84计时路径。按±2%匹配；匹配不到则保留相邻实测夹点或明确无匹配，不能以新输入质量补搜。辅助接口拒绝夹带LPIPS、缺轮次或混用profile/计时边界。

P2保留强前密C/A、仅刷新、纯代理、同Q简单搜索，增加少步Native。新输入设计目标为16prompt×2seed，具体输入待方法与步数冻结后再选择；prompt是统计簇，32视频不是32独立prompt。LPIPS与独立质量指标并列报告，少步Native不能仅因不像Native35判负。最终TEST仍属于PG-P4。诊断、Native计时选择和P2比较全部进入各自完整报价，不挪用价格卡或P1额度。

## 下一执行边界

价格补测保持[651](651_CARA_PRICE_CPU_ACCEPTED_CONTROLLER_READY_WAIT_EXCLUSIVE_20261023.md)中的原CPU接受、源码、stage、完整范围和预算。既有资源检查`cara-bank24-2`已更新到13:30并补充本接续入口，没有新建重复任务；本轮没有再次轮询GPU来刷新文档。

价格接受后可以沿已落地的接口继续：补齐P1任意mask/alpha、完整请求时钟与独占生命周期的真实生产CPU/独立接受；做完整报价；原P1卡内取得干净Native预算后生成提案。当前价格、P1生产接受与整卡报价仍是明确依赖，不能写成“P1已经可直接提交GPU”。本轮所有新科学结果格保持空值。
