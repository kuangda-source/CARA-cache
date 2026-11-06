# CARA：从校准数据自动生成区间计划

2026-10-20。最新直接人类目标是：同一套生成与校准流程输入模型、采样器、硬件和预算，自动输出刷新边界与区间修正。新模型允许重新标定，流程与选择规则保持固定。

**当前已交付 CPU 原型和可执行合成示例；尚未证明真实模型上的策略收益。** 旧 v6 的首轮32路径手选候选筛查不再是下一张必跑卡；原草案、源码和费用估计保留供追溯，兼容点可作对照或资产。原 BANK24 的已批准 scope/source/gate/CPU/资源自动化保持，先按原计划收银行。

流程：适配契约＋CAL误差/价格 → 合法区间图 → 少数候选 → 完整自然轨迹终点 → 一次联合修订 → CAL_SELECT一次选择 → 冻结policy.json。

- [方法规格](policy_generator_spec.md)：边界/覆盖/alpha、DP代理、真实终点、两个预算、迁移不变量。
- [资产复用与缺口](asset_reuse_and_gaps.md)：已有端点、单点统计和部署观察分别可证明什么。
- [首张完整真实开发卡](single_budget_validation.md)：四CAL、Q≤8、独立选择输入、完整计费与停机规则。
- [执行与验证顺序](execution_plan.md)：先生成闭环，再同额搜索对照和迁移，最后新主表。
- [冻结配方](generator_recipe_r1.json)、[任务注册表](TASK_REGISTRY.json)、[真实卡草案](P1_COMPLETE_CARD_DRAFT.json)。

CPU复现：

    PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_policy_generator_r1.py' -v
    .venv/bin/python scripts/run_wc_policy_generator_r1.py \
      --input plans/cara_policy_generator_20261020/examples/synthetic_proxy_bundle.json \
      --output 一个此前不存在的本地文件.json

示例有明确的SYNTHETIC_UNIT_FIXTURE标签，不能成为Cosmos、视频或显存/速度结果。生产适配、完整区间统计、动作费用与实际全链CPU仍待；真实卡完整GPUh报价和上限留空，不能据“8×4条主生成”称整轮约2GPUh。

WC沿用[人类固定的官方推荐配置](../cara_v6_20261020/WC_OFFICIAL_BASELINE_POLICY_20261020.json)，不新增扫参；RA原协议保持。cap226、原origin/历史、整卡严格<12自主与≥12/余额不足具体完整卡确认保持，不拆卡规避。
