# 四卡机器当前可达，但没有空闲GPU或已验WorldCache生产资源

2026-10-20 20:55–20:57只读实查。四卡原入口已用本人独立visitor恢复并通过原SSH主机密钥与历史账号身份认证，0GPU/模型加载/账本写；没有改双卡FRPC或任何服务器任务。本人四卡visitor为63606，双卡仍63302，原BANK24及22:10资源检查保持。凭据仅从原压缩历史记录在内存中使用，未保存或导出；配置/日志仅本地ignored目录。

## 当前硬件和资源

实际是4张NVIDIA RTX 6000 Ada Generation，每张49140MiB。GPU0/1/2/3已用36120/30788/30900/30789MiB，全部有compute任务，无符合独占准入的空闲UUID；没有停止他人进程。GPU2利用率11%也不等于空闲。驱动550.67，系统Python3.8.10；这和原双卡生产环境不同，未运行CUDA兼容性或模型测试，不能据版本号直接宣告可用或不可用。

系统盘余5,055,094,784字节（约4.7GiB），/data1余81,003,401,216字节（约75GiB），/data20t余478,781,566,976字节（约446GiB）。新完整采集卡最低工作空间100,400,365,568字节，/data1当前不足，/data20t文件系统有足够空间，但尚未验证本人的可写目标目录，模型资产的部署空间还须另计。没有在服务器清理、迁移或下载模型。

## 已核查的实验资产边界

本人/home/user/gaokuangda实际映射/data1/user/gaokuangda。定向核对该目录及账号默认HF hub，最多四层、9,806条目录元数据，无条目上限截断，排除生成输出/数据集/归档与其他人的目录。默认HF hub为空；定向范围内未发现Cosmos-Predict2.5或WorldCache源码/模型目录、完整guardrail权重或可复用的已验Cosmos环境。发现的siglip与huggingface_hub是其他项目的Python库代码，不能充模型资产。已有data-atlas-beamng/.venv也不能当本实验生产环境。该结论仅限已核对范围，不是全服务器不存在模型的证明。

## 能否接当前实验

硬件可作为备选。当前既无独占空卡，也没有确认可直接运行本卡的完整模型/源码/runtime资源，因此不能马上启动BANK24或1624采集卡。若以后迁移，需固定新主机的完整资产与源码身份、实际生产CPU、新硬件完整报价及同一累计v2账本/逐UUID锁，原BANK24完整原件和费用上游仍必须接受；不能把原双卡stage/CPU标志或旧余额快照当新机准入。四卡Ada的动作单价和时间属于该硬件，不能直接拼入原双卡N08干净测速。

本次只盘点，没有更换实验主机、派发GPU或新增四卡周期监控。原完整1624卡12GPUh批准保持，原BANK24/原source/gate/CPU/22:10接续不改。

证据：reports/wc_four_card_Ada_readonly_route_preflight_20261020.json、reports/wc_four_card_Ada_actual_resource_and_asset_inventory_20261020.json、reports/wc_four_card_Ada_own_asset_and_runtime_followup_20261020.json、reports/wc_four_card_Ada_experiment_readiness_assessment_20261020.json。
