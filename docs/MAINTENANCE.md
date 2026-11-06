# 当前导航维护

当前首页、主线说明、实验概览、状态和下一步围绕 frozen generator v1 维护。每个新结果先保存独立原件，再更新阅读层，并链接精确的报告或原提交。观测时间与 Git 整理时间分开；历史的“正在运行”不能冒充当前状态。

本次整理前的 `docs/project_status.json`、paper registries、templates 和 `render_repository_docs.py` 已随旧导航整体归档到 `backup/legacy_20261106/`。它们描述旧研究队列，不再生成当前首页；原字节和 Git 历史均保留。

维护步骤：

1. 更新独立结果及必要的新版本清单，不回写冻结配置、评分原件或历史文件。
2. 更新 README、EXPERIMENT_REPORT、`research/02_CURRENT_STATE.md` 和交接中的对应事实；保留拒绝、缺失、重用关系、双时钟和实际成本。
3. 若必须移动现有依赖，先检查 `docs/RETAINED_DEPENDENCIES.json`，维护运行路径或明确的新版本；不能只按日期判断无用。
4. 运行 `python3 tools/verify_repository_layout.py` 和 `git diff --check`，检查确切暂存文件。
5. 公开发布前检查新增内容中的凭据；不传私有 transport 日志、权重、视频或密钥。

`backup/ARCHIVE_MANIFEST.json` 是本次整理的审计基线，不为以后修改旧文件而更新其哈希。后续有意修改保留源码时应单独说明版本及影响，并相应更新核验策略，保留本次基线的身份和原件。
