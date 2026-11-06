# E0来源与E1 CPU准备

已锁定DiCache官方commit及Wan/FLUX两个端口的blob SHA，并核实DCTA裁剪分别为[1,2]/[1,1.5]；零分母、精度和Cosmos分支身份需要明确移植适配。已复核本地旧CAL66八视频哈希，合计6.56MiB；不重复已完成锐度分析。

新增[移植与CPU用例清单](../plans/cara_predictor_refresh_scout_v2_20261026/E0_SOURCE_AUDIT_AND_E1_CPU_CASES_R1.md)，覆盖11组真实入口、状态恢复和失败边界。见[机器回执](../reports/cara_scout_E0_source_and_local_assets_20261026.json)。这是来源/准备接受，不是生产CPU或新读出结果；未运行模型、未连接服务器、未读取DEV128部分结果、未新增GPU提交或预算预约。

1624保存的guided输出可用于既有坐标诊断，但不含恢复E1稀疏父历史所需的双分支p/r bank。Native-relative梯度与固定轻模糊C对照仍待完成；没有把文档准备称为完成计算。下一步先落实DCTA/A/R4组件和真实状态隔离，再完整报价；当前DEV128及其自动验收保持原样。
