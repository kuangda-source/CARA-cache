# 原M1执行准备承接：已转实际GPU运行

当前唯一运行已经启动；优先读取[M1_POST_LAUNCH_HANDOFF](M1_FULL14_POST_LAUNCH_HANDOFF_20261101.md)和[actual start](../../../reports/cara_read_write_actual_start_accepted_r1_20261101.json)，不得依下面启动前步骤重复派发。下文保存准备到准入的历史过程。

# M1完整14当前执行承接

当前节点为[829](../../../research/829_CARA_READ_WRITE_M1_ENTRY_SCORER_STORAGE_AND_SOURCE_READY_20261101.md)。执行范围仍是[完整14 R2](M1_FULL14_EXECUTION_R2.md)，现行[执行卡 R3](M1_FULL14_EXECUTION_REVIEW_R3.md)与[报价 R3](M1_FULL14_WHOLE_QUOTE_R3.json)已经具体化。用户已允许本卡原账本事务，已读取原余额，尚无新预约或GPU派发；真实方法结果未建立。

## 保留原件，不再prepare

- 组件R1 `cara-read-write-M0M1-CPU-a6000-r1-20261101-cpu` exited/1原失败保留；组件R2 exited/0、20控制/8后缀/12请求已接受。
- 完整采集 `cara-read-write-full14-CPU-a6000-r1-20261101-cpu` exited/0，28条tiny请求已接受。
- 新入口 `cara-read-write-entry-CPU-a6000-r1-20261101-cpu` exited/0；67控制、28加载tiny请求及八对真实93帧合成媒体评分接受。启动传输曾UNKNOWN，仅恢复原stage，未重派。记录短ref `b930df4b`解析为完整`b930df4b04a0924d8bea0af32c0f7aaf8c33a5c8`。
- 私有卷原PID2917051/start ticks682348915已退出，16GiB镜像、48MiB独立journal接受；禁止再执行storage launch。只可capture复核。
- 唯一GPU source stage已安装：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-read-write-M1-GPU-a6000-full14-r1-20261101`，1307文件，原注册SHA `2def9cdcb04c20b96977c6f82ad728cebf42e67907048a650238d2ba9f9bbd5e`；没有GPU authority/intent/launch/container。禁止再source prepare，只可source capture。

关键回执：`reports/cara_read_write_entry_Linux_CPU_accepted_r1_20261101.json`、`reports/cara_read_write_whole_CPU_accepted_r1_20261101.json`、`reports/cara_read_write_storage_accepted_r1_20261101.json`、`reports/cara_read_write_source_preparation_r1_20261101.json`、`reports/cara_read_write_M1_preparation_progress_r3_20261101.json`。

## 当前权限与下一动作

原小于2GPUh自主规则覆盖完整卡：预计1.6047625015、硬1.95GPUh，不拆分。**用户已回复“允许本卡原账本读取、预约与结算”。** 四卡实验维护禁入保持，例外仅新M1原账本事务；不得迁移账本、做其它卡事务或四卡实验。`central-prepare`已完成，原cap226、旧16.5责任、可用15.4601GPUh，尚无本卡预约。

唯一本地`M1_SINGLE1P95GPUH_AUTHORIZATION_R1.json`已创建并首次bind到原GPU stage，明确引用用户原自主规则及本次真实中央许可、完整14/512/8、源b930df4b、上述注册SHA和CPU/quote原字节SHA。launch_id为`7949388215944eb98c7f64f21e8e1dd1`。原bind回执为`reports/cara_read_write_authority_bound_r1_20261101.json`，禁止创建新身份。首次`admit`因SSH banner握手超时未取得结果；先status恢复原句柄并确认原stage后继续准入，不派新GPU。

随后依次：

1. `scripts/cara_read_write_control_r1.py bind`仅首次安装本卡authority。`admit`完整核验原资产SHA、runtime、私有卷/空输出、设备和资源。所有CLI action都须新output回执；UNKNOWN只恢复。
2. 仅本卡`central-prepare`部署受控原账本读者；`refresh`重查两卡资源/资产stamp，`reserve --input refresh回执`在原cap226账本一次预约；保留旧16.5责任。
3. `dispatch --input reserve回执`必须仍处于60秒fresh窗口。已有intent即recover；原guardian总计7020秒、6420秒开始停止释放、90°C；不重派、不换卡、不改源或配置。
4. `status`恢复原guardian/容器/PID-start ticks与运维14分母计数。实际开始后按预计全段安排一次半程和同一终验，静默无变化，不看部分科学分数。
5. 终态由`settle --input 原terminal status回执`唯一结算guardian全段实耗，失败同样结算。未知事务先`central-recover`，不重复收费。
6. 完整14成功并退出释放/结算后，用`scripts/cara_read_write_accept_transport_r1.py artifacts`唯一CPU读者检查全14、四latent/93RGB等价；之后`score`一次八对Fidelity-v2，活跃则`capture`恢复，不重评旧实验。
7. 接受完整八对后报告逐输入和等权read/write/interaction、全部93帧曲线。分析源码可另行版本化，但不可改GPU原source。M1是机制诊断，M2方法与read-only消融的完整新卡仍须另外完整范围、报价与准入；不自动下一GPU。

GPU只给原A6000 `GPU-cebf7119-cf03-23b9-e192-cd196332b704`，2CPU/40GiB无额外swap、独立16GiB输出。原A32/B36/S/Q/搜索/E1、WC/RA FIT UNMATCHED、旧CAL、最终16/备用16保护均保持。

连接保持原Tailscale ProxyJump私有配置；`cara_two_card_transport_r1.ssh()`旧默认会经四卡，当前禁止使用。成功端口不等于认证/执行成功，不安装Tailscale、不改Windows/Clash/路由、不重启服务。
