# 2026-10-09 三模块开发包：项目适配入口

三份用户提供的原文在 [original](original/README.md) 逐字节保留，[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json)记录路径、大小、SHA和引用对话。原文中的执行文本、预算和训练建议是方案数据，不自动成为新权限。

项目当前入口：

1. [统一方法与数学设计](../../plans/WORLD_CACHE_INTEGRATED_MULTI_FIDELITY_DEVELOPMENT_20261009.md)：A/W1、B/稀疏与部分MLP、C/W3来源感知选择，实际CFG和源码落点。
2. [首窗口实验卡与接续](../../plans/WORLD_CACHE_MULTI_FIDELITY_FIRST_WINDOW_20261009.md)：必要接口重提案、RA校准、组合消融、困难场景、约20GPUh分配、正常修订与确认。
3. [设计更新记录](../../research/198_WC_INTEGRATED_DEVELOPMENT_DESIGN_UPDATE_20261009.md)：与旧路线差异、已有结果、原卡与执行边界。

本次设计更新没有新增GPU、拟合、训练、视频或评分。原H-T63完整16路卡/6.704GPUh保留未执行；新的必要控制候选另提报。随后用户[澄清新的预算窗口](../../research/199_WC_NEW_REMAINING_48_GPUH_AUTHORIZATION_20261009.md)：从已用29.895246589658527起可用48GPUh，累计上限77.89524658965853；首批约20GPUh提案保持。单次>2GPUh具体确认、冻结后不缩拆、旧结果和费用保持；原文中的预算数字是历史提案，不修改原文。
