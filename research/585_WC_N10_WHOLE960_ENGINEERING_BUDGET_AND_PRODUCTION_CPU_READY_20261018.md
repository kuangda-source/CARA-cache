# N10完整960整卡预算已登记，生产CPU代码准备完成

2026-10-18。**N10采用完整工程预算直接接正式评分生产验证，不增加一张仅用于报价的GPU卡。** 全部五模型、原160／960位置和19对比不变。当前仍为0新质量分数，GPU尚未派发。

[预算登记](../plans/WC_N10_FULL960_ENGINEERING_BUDGET_PREREG_R1_20261018.md)明确给出全部129视频／维度的规划余量：DINO／ViCLIP／MUSIQ每视频15秒，AMT／RAFT每视频30秒；五context各120秒加载／核对，另600秒汇总／失败记录／释放。总额乘1.2得到**4.915 GPUh**工程预测，计费上限为**6.25 GPUh**。它不是实测模型价格或CPU耗时的GPU换算，实际费用仍按整个原supervisor wall结算；无法完成的原位置保留，不用拆缩换成功。

[整卡原件](../reports/wc_paper_N10_full960_engineering_cost_R1_20261018.json)和[正式配置](../configs/wc_paper_N10_full960_production_r1_20261018.json)已绑定实际五CPU、全部输入、原未报价范围及测量身份，原未报价文件保留。实际配置／报价的CPU接受和GPU执行资格尚待生产阶段，报价本身不授予新方法或质量结论。

已补上从原244源只读复制新stage的[CPU部署](../scripts/deploy_wc_N10_full960_production_cpu_r1.py)、完整四组控制＋实际960入口的[五命令bundle](../scripts/run_wc_N10_production_cpu_bundle_r1.py)、[一次收件](../scripts/capture_wc_N10_production_cpu_r1.py)和[离线独立接受](../src/wcomr/automatic_quality_production_cpu_r1.py)。额外核对全部实际五模型原CPU证明，原构造器和权重不修改、不再加载模型；原source／完整配置与价格／PID＋start_ticks／五命令／CPU禁止边界分别验证。

[本地准备证据](../reports/wc_paper_N10_priced_full960_CPU_staging_local_preparation_20261018.json)：25项控制通过（报价3、CPU接受5、不可变安装9、原生产入口8），三CLI在`python -S`下冷启动通过；32项overlay与原244源无覆盖冲突，单元fixture的额外Python依赖已显式包含。冷导入检查发现旧生成栈会引入Torch，已将新CPU接受器的PID比较保持为独立纯函数，并用无site-packages导入检验；没有改旧科研结果或放宽真实生产门槛。

下一步新独立stage实际执行完整生产CPU，接受原件后再完善单次GPU派发与完整960终态重建工具。6.25严格少于12，沿既有授权及fresh v2／UUID准入，累计cap226和历史账不变。N09完整40仍优先、资源每两小时查看；正式N09测速不与重模型CPU／N10评分并发。F/B关闭，无新生成、训练、人评、付费VLM或OMR。
