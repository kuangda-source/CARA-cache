# 仓库拆分 — 2026-10-02

本库最新内容与执行队列仅保留WorldCache；OMR独立研究设计、交接、资源清单、小回执和Wan/LongLive专属CPU准备工具迁至[omr-experiments](https://github.com/kuangda-source/omr-experiments)。原联合计划分成WorldCache与OMR专属计划。

源提交：`ef23972918d5bda205c412abf869a38ee195605c`。原混合文档在OMR新库archive/pre_split保留字节原件，逐文件来源与SHA256见[迁移清单](https://github.com/kuangda-source/omr-experiments/blob/main/manifests/repository_split_20261002.json)。原库Git历史保留，不重写或force push。

现有WorldCache代码/测试、冻结配置/清单、科学回执和GPU账本保持。仅迁移没有WorldCache调用依赖的L0专属CPU工具及其测试，通用依赖在两库保留。旧包名wcomr、部署路径、历史回执source/PID不会改名；运行目录、权重、视频、环境和凭据不迁移。

当前WC-S/H冻结工作先完成；本次没有启动/取消实验或修改预算。OMR无新增GPU额度，其后续文档只在新库维护。
