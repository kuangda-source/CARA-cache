# P1整卡CPU组合接受、便携交付与GPU源包准备

P1整卡CPU准备已按原源与原回执组合接受，Linux原导出包到本机绘图的交付链已通过。新64GiB输出/48MiB日志、完整工程报价和拟议19GPUh配置均就绪；GPU源包尚待实际绑定，GPU及本卡中央权限仍为空。

## 原最终CPU与交付

[最终Linux13接受](../reports/cara_v1_P1_final_CPU_accepted_r1_20261102.json) · [原证明](../reports/cara_v1_P1_final_CPU_original_proof_r1_20261102.json) · [原捕获](../reports/cara_v1_P1_final_CPU_capture_r1_20261102.json) · [关闭](../reports/cara_v1_P1_final_CPU_complete_cleanup_r1_20261102.json)

固定源`dd2a73060f4097ceb91dd66c8a5f98a33fe65092`，registration`12bbbda7e0b466ff0efd7638b6e73602c71484441841264f387c5c7f49050e1e`。原宿主于09:06:08.486679开始、09:06:21.537094正常结束，13.05秒；GPU隐藏、CPU26/27、AS4GiB。13项新增控制：导出4、最终profile/报价3、来源父类型5、空硬限拒绝1。

原CPU额外保存一份新的完整52位置合成元数据导出包（416181字节），原件结束后按独立SHA取回；本机从该原字节实际输出两组PNG/PDF、四CSV，共8文件，零新指标、零远端恢复。两份PNG与先前通过视觉QA的图面字节相同。见[跨环境交付](../reports/cara_v1_P1_actual_Linux_bundle_local_figures_CPU_r1_20261102.json)与[图面SHA接受](../reports/cara_v1_P1_actual_Linux_bundle_local_visual_QA_r1_20261102.json)。未给服务器增加绘图库。

原CPU已退出，完整在首次计划半程前取回，无待执行检查；不再轮询、prepare或重放。

## 整卡CPU证据组合

[整卡接受](../reports/cara_v1_P1_whole_CPU_accepted_r1_20261102.json) · [组合器](../scripts/assemble_cara_source_lifecycle_p1_preparation_r1.py)

组合器核对全部1462个当前payload原字节、相同runtime/补充init、每份原接受/捕获/证明SHA，以及35处算法、FIT、guardian、释放评分/分析和外层核心源。复用原完整算法33、实际宿主FIT、guardian34、原释放146/32新对worker、outer31/真实后置Docker、entry23，新增final13、精确本地14与原Linux导出绘图；没有重放任何旧实验或指标。

完整范围为146语义位置、最多142物理请求/5176模型pair、64标签、42内部双FIT查询/84持卡评分、最多32后置新对和52最终质量位置。GPU容器40GiB、内部评分8GiB及原独占/温度/600秒余量不变。新[64GiB存储](../reports/cara_v1_P1_storage_accepted_r1_20261102.json)与[18.0273GPUh工程报价/拟议硬19](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_QUOTE_R1.json)已组合。

这是完整CPU准备接受，未执行真实P1 GPU容器、未接受真实V1标签或视频，不能说明方法效果成立，也不替代派发时的实时准入或用户批准。

## 新GPU源包

[源包操作器](../scripts/cara_source_lifecycle_p1_source_r1.py)只从上述已结束、完整接受的最终CPU复制原字节到唯一新P1 GPU stage，绑定原存储、完整CPU/报价与离线评分权重。已有意图、授权、容器或部分stage均只恢复；资源/权重检查先于新stage创建，不创建授权或GPU进程。

源包实际接受后，提交[完整单卡审阅](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SINGLE_CARD_REVIEW_DRAFT_R1.md)。审批为完整19GPUh及本卡原中央读取/唯一预约/实耗结算；实时资源与余额核验通过才启动。250秒/标签仍是预算假设，旧16.5责任、cap226与24增量规则、四卡维护限制和全部旧冻结/保护输入保持。
