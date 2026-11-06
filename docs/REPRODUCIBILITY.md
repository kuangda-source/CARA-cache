# 复现与证据核验

## 本次目录整理的核验

在仓库根目录运行：

```bash
python3 tools/verify_repository_layout.py
```

该工具只读本地文件，逐一核对整理前全部 tracked 文件的 SHA256、大小和保存位置，并检查保留 Python 文件的语法、仓库内导入、显式原路径和当前 Markdown 链接。它不加载模型、不连接服务器、不触发 GPU/CPU 评分或账本操作。

[ARCHIVE_MANIFEST.json](../backup/ARCHIVE_MANIFEST.json) 记录整理前提交 `8671422cd2c497d0cb7ab42084b3e09f5f84dc81` 的 14084 个文件：13191 个移入 backup，893 个主线或兼容依赖保持原路径、原字节。新导航和核验工具另行新增。旧文件内容没有为修复历史链接而改写。

## 科学结果

- [冻结掩码及资产哈希](../plans/cara_next_stage_20261105/generator_v1_frozen/frozen_masks_r16_r18_r21.json)：核对布局身份、D/A/C 次数、参数及旧资产 SHA。
- [最终验收](../reports/cara_primary11_r1_20261106/FINAL_VERIFICATION.json)：核对源、复用产物和评分对应关系。
- [逐输入完整报告](../reports/cara_primary11_r1_20261106/REPORT.md) 与 [分析原字节](../reports/cara_primary11_r1_20261106/complete_analysis.original.json)：核对队列分母、拒绝、配对集合、双时钟及描述性统计。
- [结算原件](../reports/cara_primary11_r1_20261106/central_settlement.json)：保存唯一实际费用及责任，不因 Git 发布或归档重复结算。

原视频、latent、模型权重和私有连接配置不在 Git 中。仓库保存哈希、冻结清单和验收回执；重现实验需要相同上游版本、资源、模型和对应产物访问权限。已有源哈希标识原提交，不标识整理后的整棵树。

原生成脚本需要冻结说明所列的校准工作区，部分生产工具需要 Linux、固定上游文件和服务器资源；目录核验成功不代表这些外部环境齐备。本次没有重跑生成器、真实视频评分或实验。

## 历史代码和工具

历史入口和旧路径可能假设原树的层级。请从[归档索引](../backup/INDEX.md) 使用固定提交链接阅读；需要旧运行环境时在独立目录 checkout 原提交，保留当前主线树。不要直接运行 `backup/legacy_20261106/scripts/` 下的旧派发器或原导航生成器。

少量旧名模块/配置仍留在原路径，是主线运行器、scorer、tiny 控制或冻结引用的依赖。依据见 [RETAINED_DEPENDENCIES.json](RETAINED_DEPENDENCIES.json)。保留它们不构成对应方向的科学晋级或执行授权。
