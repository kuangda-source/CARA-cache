# 缺失与统计口径

意向分母：B正式4×7=28，三质量门84位置，另dynamic degree28描述位置；每项LPIPS24个非Native配对、2232帧，Native自距0须有成功Native原件才能记。A选参另有4Alex配对372帧，不作为B样本。

所有位置记录COMPLETE/TEXT_REJECTED/VIDEO_REJECTED/TECH_FAILED/NOT_REACHED；评分记录SCORED/RESOURCE_UNAVAILABLE/METRIC_FAILED/NOT_REACHED。拒绝、缺失不填0，不替换提示词、不自动重试。按全部角色固定共同成功交集报告配对指标，同时列每角色覆盖率与缺失原因；若交集为空，不计算均值/优势。

帧先视频内平均、时间重复先prompt内平均，然后prompt等权。速度独立算mean(T_Native)/mean(T_method)，分别T_DD、T_request、辅助T_generate；按硬件分表。LPIPS相对改善为1−mean(L_method)/mean(L_baseline)，同一队列、逐prompt差和方向另列，不混用平均相对改善。baseline均值0时相对改善N/A。

A选择任何候选不完整则不选，不因删去失败候选缩小选择分母。原始拒绝路径有T_request；未decode的T_DD=null。视频拒绝发生于decode之后可保留实际T_DD但无视频质量，不能将此时间混入成功配对加速比。

诊断失败停止、费用耗尽未到达、热异常均保留原记录。不能事后删慢样本。既有257.7712338712067秒及0.8×fresh Native双预算仍只按原T_request合同，不重算旧结论。
