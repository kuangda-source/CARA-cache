# PG-P1/P2：价格接受后的直接接续

本轮完成输入曝光审计、可执行的资产转换/诊断矩阵/Native计时选择接口，以及CPU控制。原价格补测的源码、stage、10路径范围、CPU接受、11.5 GPUh上限不变。这里冻结的是后续规则；尚未产生P1策略或P2质量结果，也不预先批准尚未报价的GPU并集。

## 1. 输入和接入顺序

CAL_FIT仍为原四场景、seed0；CAL_SELECT仍为`av_animal_dear_1_0`和`industry_057`、seed0。原SELECT清单和recipe保持原字节。曝光审计只读取身份和来源，不导出评分或时间；覆盖本地reports的JSON及gzip、四卡项目outputs的文件名及声明结果JSON。退役两卡仅以已保存回执覆盖，不为此重连。四卡外或未记录的执行不在结论内。

入口：

```sh
.venv/bin/python scripts/audit_cara_cal_select_exposure_r1.py --output <新唯一曝光回执.json>
```

历史全目录清单和“下一步跑这两个输入”的自动化文字不算模型曝光。任何未分类命中、读文件失败、外部输出软链接或SSH UNKNOWN都不能自动放行。第一次SELECT端点前，再检查本次审计之后新增的执行元数据；不因出现更好的结果而替换原输入。SELECT用过即属于开发数据，不能改称最终TEST。

价格补测完整接受后，按以下顺序接续，无需重新设计接口：

1. 读取原独立价格接受及其绑定的原capture。输出完整1624格重复波动、执行顺序漂移和max-source聚合放大；低CV不替代独占接受。新bundle绑定原标签SHA和新价格SHA，旧bundle不改。
2. 完成PG-P1真实生产CPU：任意合法mask、alpha=0.5/1、严格过去锚点、D36回绕保护、真实请求/guardrails/93帧写出、拒绝保留、清理和独占生命周期。资产CPU与本轮27项局部CPU控制均不能替代这一步。
3. 为P1完整64路径上限及所有额外工作报价、冻结生产源码，按既定整卡和预算规则准入。不能先派几条CAL，再决定是否补齐原卡。自适应首4后4仍是一张完整注册卡。
4. 原卡内先完成2条Native warm、4条CAL_FIT干净Native，独立验证原件/计时后固定B=0.80×四CAL等权均值，再生成首批策略。其余2条SELECT Native放在搜索关闭、finalists冻结之后，防止提前观察SELECT。旧受竞争Native的图像可作原件参照，旧计时不能设B。
5. 运行下列转换；输入格式转换、完整域与SHA检查已实现。已有proposal CLI随后直接消费输出。Native时钟接受器必须由实际生产入口产生下面约定的原件，不能手填true。

```sh
.venv/bin/python scripts/prepare_cara_pg_continuation_r1.py generator-input \
  --price-capture <价格完整终态.json> --price-acceptance <价格独立接受.json> \
  --old-capture reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json \
  --old-acceptance reports/wc_policy_assets_full1624_fourcard_GPU_accepted_20261023_0826.json \
  --native-clock <本P1卡干净Native时钟接受.json> --output <新生成器输入.json>
.venv/bin/python scripts/run_wc_policy_generator_r1.py \
  --input <新生成器输入.json> --output <新首批提案.json>
```

转换保留原统计值，将`target`显式映射为`update`、`fit_members`映射为`CAL_FIT_members`，过滤到现有Profile/Costs的准确字段，检查1624个唯一统计格和完整合法图覆盖。保留教师条件标签属性、初始均匀权重、0.25秒离散、Q≤8、首4后4和一次SELECT；不把它解释成自身轨迹的真实损失。

### 统一时间口径

本次新增的P1/P2完整请求决策时钟为：**method_install + guarded_pipeline_without_write + video_write + method_cleanup**，均为同步墙钟，覆盖完整35请求步/36更新及93帧输出；不含研究张量复制、哈希、评分或shadow。加载/额外采集/评分期间实际占卡均进入校准账单。各方法同时保留原`core_seconds`，历史core计时不直接混入新完整请求表。

原资产动作价格覆盖core路径。转换器只在新消费文件中加一次四CAL Native的`完整请求−core`均值，作为公共开销估计；保留原动作聚合与原bundle。这一项不是方法自身安装/清理的准确价格保证，P1仍以实际完整请求时间决定可行性，并报告预测残差。不能把core预算和完整请求预算混用。

`native-clock`合同：status=`CLEAN_NATIVE_CAL_COMPLETE_REQUEST_CLOCK_ACCEPTED`；full_protocol/exclusive_monitoring接受；profile_identity对应新价格运行环境；timing_boundary=`COMPLETE_VIDEO_REQUEST_GUARDRAILS_SAMPLER_DECODE_WRITE_NO_DIAGNOSTICS`；before_candidate_endpoints=true。rows恰为四CAL，每行member/seed0/requested_steps35/actual_updates36/accepted/seconds/core_seconds，所有时间有限正数、core≤完整请求。实际接受器还必须绑定原source、请求SHA、原始时钟、独占监测和原件验收，而不是仅检查这个布尔结构。

## 2. 小规模历史失配诊断

**问题：教师表中相邻锚点的动作排序，在策略自身的稀疏刷新历史下是否保留？** 上游固定WC源码的C路径既用较早probe估计gamma，又以两个深层residual外推；OSI开启和关闭均依赖较早锚点，flow继续作用于该候选。该问题有实现依据。

冻结点为P1最终策略和对应强简单规则已确定之后。简单规则由P1已注册的SIMPLE_C/A中，按既定可行性、LPIPS、时间、fingerprint顺序选出，不能由诊断表现选择。若无可行简单控制，先记录P1预算未验证，不能补选有利基线。

| 项目 | 固定设计 |
|---|---|
| 输入 | CAL_FIT清单前两条，seed0；不使用SELECT/DEV/TEST调诊断 |
| 方法角色 | 最终CARA及上述简单控制；相同fingerprint物理去重、角色仍保留 |
| 路径上限 | 4正式＋每唯一策略1warm，最多6完整路径 |
| 目标选择 | 以前一真实D=p、最近真实D=s的间隔s−p分为2–4/5–8/≥9；每组最早合法跳步t，每轨迹最多3点 |
| 空组 | 原样保留，不改策略、不增加更有利输入 |
| 变量控制 | 同一当前状态、同一最近锚点s，比较真实窗口[p,s]与邻接影子窗口[s−1,s] |
| 动作 | 每窗口C/A_HALF/A_ONE；同一个当前状态的shadow D为共同参照 |
| 成本上界 | 最多36额外shadow D pairs；普通216 pairs，合计≤252 pairs/504 CFG calls；最多108 paired readouts |

矩阵接口：`prepare_cara_pg_continuation_r1.py history-matrix --input <冻结profile/roles/members.json> --output <新矩阵.json>`。输入profile使用现有Profile字段，roles为CARA/SIMPLE的完整compiled policy，members为原前两CAL。函数重新编译intervals验证fingerprint、action和source_before，输出准确点位、缺组、去重后的路径和费用分母；上界不是假造的已选点位。

影子执行要求：

- 在所需s−1时，针对策略自己的当前状态额外计算真实D并保存诊断锚点；在t再算shadow D。它们均不成为部署锚点、不改变候选选择。重复影子步只计算一次，所有调用记账。
- 权重共享，运行状态隔离；每次核对输入latent、solver历史、部署缓存/锚点、计数器、条件与RNG的前后指纹。生产CPU必须验证shadow OFF/ON全36 guided、最终latent与93帧RGB相等。只有本轮局部核函数测试通过还不够。
- 源/目标的影子特征在用后释放。保存两窗口的双分支C/Phi/A_HALF、共同D及其SHA、状态和锚点身份，便于以后计算共享/独立alpha诊断；不再只存guided归约。隐藏层全bank不常驻导出，具体字节数按真实shape计入磁盘/内存准入。
- A_ONE只依赖当前probe、最近真实D和固定warp；替换较早锚点应逐位不变。C和A_HALF允许变化。此次已用实际固定WC skip/OSI/flow与ReadoutKernel、显式Toy head/RF，在flow开关×OSI开关四种CPU情形验证这一控制、输入不写回及RNG不变。

分析分两层：①同自身状态两窗口的guided MSE差、动作秩、最优动作保留率及选择后悔值，识别历史因素；②1624教师条件同(s,t)的三动作排序与自身状态排序，测量包含状态漂移的总失配。主报告为C/A_HALF/A_ONE三动作的并列感知秩；常量秩相关记NA。另列跨目标秩相关和prompt级汇总，不能把所有格当独立样本。MSE参照为0时比值NA并给绝对差，不用epsilon制造倍率。带shadow的时间不进入速度表，诊断不回调已经冻结的P1策略。

## 3. 少步Native对照

本地实际固定UniPC CPU网格已覆盖18–35请求步，保存每个完整timesteps/sigmas与源码SHA。当前网格均为实际更新数=requested+1；未来生产入口逐项比对真实调度器，不能把这一关系硬编码为所有模型的规律。

```sh
.venv/bin/python scripts/prepare_cara_pg_continuation_r1.py native-schedules-cpu \
  --output <新的实际调度器CPU回执.json>
```

Native必须走原完整网络forward，CFG两支均跑所有层；验证实际首/末层调用数、guardrails、输出帧数和无缓存安装。历史入口只接受18/26/35三个步数，所以新的候选步数仍须单独通过实际生产CPU；调度器跑通不等于视频入口接受。

步数选择规则已实现：

1. 只用冻结CARA的四CAL实际完整请求均值作目标、干净Native35均值作参考。对18–34各请求步，以实际更新次数比例预测时间；取最接近目标的4个整数步数，误差并列取较小步数。比例只用于有限候选筛选，不作实测时间结论。
2. P2同卡先对已冻结CARA与Native35各做四CAL×3轮＋2warm，共28条时间基准路径，不读新质量、不改变策略。其后四个少步候选×四CAL×3正式重复，另每候选2warm，候选部分上限56路径；整个时间选择模块最多84路径，另计加载及评分/清理。各块先按方法升序做2warm；正式轮r=0,1,2的prompt顺序为原四CAL循环左移r，prompt位置j的候选顺序为升序候选循环左移(r+j) mod 方法数。该规则在输入质量出现前固定。这个开销独立计入P2，不占P1的64路径或Q。
3. 用每prompt先平均3轮、再平均4prompt的计时选择；在目标±2%内取绝对相对差最小者，其后按时间、步数打破并列。输入schema不接收任何LPIPS或质量字段；缺失/拒绝/重复计时位置均不静默删去。
4. 无±2%匹配时，保留实测时间夹住目标的两个相邻请求步数；报告两个真实点，不插值画质。无夹点则NO_CAL_TIME_MATCH，保留完整结果；扩大步数范围需要新范围和完整报价，不能查看新输入质量后补搜。时间非单调单独标记。
5. 步数在读取新输入质量前冻结。CAL匹配不保证新输入均值也匹配，后者仍报告时间差与质量—时间点；不按每个新prompt重新选择步数，不人为延迟凑平。

入口为`native-candidates`和`native-time-choice`子命令。前者输入schedule_rows/target_seconds/clean_native35_seconds；后者输入rows/candidates/members/target_seconds/profile_identity。每计时row字段固定为requested_steps/member/repeat/seconds/profile_identity/accepted/exclusive_acceptance_sha256/timing_boundary。实际独立接受原件SHA由生产收件链核验，转换工具不替代原件接受。

## 4. P2比较与分析预案

保留CARA、强前密C/A、refresh-only C/A、pure-proxy、同Q简单搜索，再加入Native35及上述少步Native。每个搜索方法分别记Q、实际校准成本；物理同计划可以复用，但不能抹掉方法看到的信息。WC保持已批准的官方固定配置，忠实性核验是独立前置工作，不在本轮偷换或调优。

新输入闭环以**16个新prompt×2个seed**作为待整卡报价的设计目标。具体身份在P1方法、P2对照和Native步数冻结后按固定hash顺序、来源组闭包排除全部历史曝光和CAL_SELECT再选择，拒绝保留位置。这是PG-P2新DEV确认，不替代PG-P4最终TEST；当前不提前选人或宣称样本量具有80%功效。多个seed先在prompt内平均，bootstrap以prompt为簇，不能将32视频或93帧计作32/2976独立prompt。

主要分析是冻结CARA与预先确定的强简单对照的配对LPIPS差和实际时间，报告prompt聚类区间、每prompt方向及最差退化。少步Native同时比较独立质量维度：沿已有N10可复用的主体一致性、运动平滑度、文本/视频一致性、MUSIQ；dynamic_degree单列，静态不适用项保留NA，不拼成未经验证的总分。LPIPS只能支持Native轨迹保真；无显著质量差异不自动写成“无损”。若主张质量非劣效，须在读新数据前另行固定具有解释依据的容忍界限。

P2主表用真正的新输入结果；CAL用于解释生成器如何选择，不冒充泛化主表。效应区间不足以区分简单规则时保留不确定性，不能靠追加seed直到显著。全部P2方法并集、搜索、Native计时选步、warm、评分、历史shadow与失败余量统一报价；不把可能超过12 GPUh的完整实验拆成小卡绕过既定审批。历史诊断可按独立科学问题注册，但不能挪用P1或价格卡额度。

## 5. 接续清单

已就绪：SELECT身份审计、来源绑定、生成器schema转换、合法图覆盖检查、诊断点位/分母生成、固定WC历史控制、真实UniPC CPU网格、Native纯计时选择器及反例测试。

下一执行者应补齐：新价格终态接受；P1任意mask/alpha与完整请求时钟的真实生产CPU/独立接受器；P1完整报价；清洁Native卡内时钟后生成策略。P1冻结后再固化诊断矩阵、P2物理去重/新输入/Native计时矩阵和各自真实生产CPU、完整报价。所有新GPU仍走四卡空闲UUID实际EXCLUSIVE_PROCESS准入与持续监测。
