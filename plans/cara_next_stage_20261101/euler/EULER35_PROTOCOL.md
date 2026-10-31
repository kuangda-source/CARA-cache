# EULER-E0 当前协议入口

规范与未决问题见[协议差异和硬门](../EULER35_PROTOCOL_GAPS.md)，完整数组和源身份见[sigma契约](sigma_grid_and_call_contract.json)。

显式flow Euler采用35次更新、70个C/U调用及递减sigma，以本Euler Native作为未来质量参考。E-SOLVER另保留原36更新显式网格，不与35更新重建混用。818完成数值原型；821补齐完整固定采样入口的微型CPU组合，详见[分层CPU接受](EULER35_CPU_ACCEPTANCE.json)。

新增隔离scheduler与已有ATS beta4适配器共同验证70-call reset；Native与强制全计算wrapper的70个分支输出、35个更新latent、最终latent、微型解码RGB及RNG一致。原UniPC及已准备E1源包保持不变。

执行在macOS CPU，使用明确的微型模型/条件/解码和mock writer边界。当前未加载真实权重或派发Euler GPU，Linux兼容和真实权重Native/allD等价仍待。方法相关噪声坐标保护、年龄、晚期间隔及完整卡费用须在E1确定方法后前瞻冻结；此版本不进入科学结果表。
