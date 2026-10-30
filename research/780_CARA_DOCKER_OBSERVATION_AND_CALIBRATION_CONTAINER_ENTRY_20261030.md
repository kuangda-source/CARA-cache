# 双端 Docker 观察与校准容器入口

2026-10-30。修复779发现的真实Docker空容器格式差异，补齐预算校准容器参数与监督器入口。两台注册服务器的只读观察及26项本地控制通过；本轮未创建容器、运行GPU或写入中央账本。

## 精确观察与原证据

[生命周期读者](../src/wcomr/cara_budget_lifecycle_capture_r1.py)增加已实际观察到的 `Error response from daemon: No such container: <原名称>`。仍要求exit1及完整匹配原名称；其他名称、权限错误、daemon失联、额外错误文本、不同退出码和超时均不作为容器不存在。正常容器的ID、镜像、manifest、单UUID和原State归一化保持。

[四卡原观察](../reports/cara_budget_docker_four_card_readonly_r1_20261030.json)与[两卡原观察](../reports/cara_budget_docker_two_card_readonly_r1_20261030.json)均在20:51:55附近通过原SSH入口调用一次真实 `docker inspect`。两端均返回上述daemon格式，修订函数正确得到None。探针只执行来源SHA绑定的原 `inspect_container` 函数，目标为专用观察名称；没有创建stage/容器、读取科学输出或操作其他运行。该证据只验证空容器观察分支，不等同于完整GPU生命周期接受。

读者源码变更后，不能把旧CPU源绑定套到当前工作树。[原R3控制链复核](../reports/cara_budget_allocation_four_card_CPU_published_source_revalidation_r4_20261030.json)明确使用发布源 `17cf1e348ec4f56d717c44ee5fd596b7054345a0`，保持原13项Linux/12场景证据；未重跑原CPU。验收器只接受完整40位历史commit，拒绝HEAD、分支名和短SHA。779原接受及其失败历史保持。

## 容器与监督器入口

[候选资源配置](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_CONTAINER_PROFILE_R1.json)承接14GPUh、51次双FIT查询、112路径设计；沿用原固定镜像、2CPU、40GiB内存/同额swap上限（无可用swap）、24/25CPU亲和、host PID、无网络和只读根。该文件为准备配置，不是执行授权或已接受报价。

[命令构造器](../scripts/cara_budget_container_r1.py)复用原B36/A32受限挂载构造路径，不修改原62份关键源码。仅请求一个明确UUID、宿主监督器隐藏CUDA，记录原cidfile；项目整体只读，仅本次stage、独立输出、独立控制日志和GPU锁目录可写，stage内src/scripts再以只读挂载覆盖。拒绝错误范围/镜像/内存swap、跨输出目录、非64GiB输出镜像、非48MiB独立日志及不足的低水位配置。这里只检查命令和合同几何，实际文件系统挂载、设备、inode、非稀疏分配和余量仍须由StorageGuard及派发前准入检查。

[监督器容器入口](../scripts/cara_budget_supervisor_worker_r1.py)核对原授权/launch/registration及自身、构造器、资源配置的SHA；要求原host guardian仍明确存活。重建完整容器argv并与原冻结命令逐项相等，检查实际StorageGuard后才进入已验证的监督器。CPU夹具、错误授权/源码、篡改命令和死/UNKNOWN guardian均拒绝。入口本身不预约GPU或构造新的launch；完整once入口仍待连接。

[本地组合回执](../reports/cara_budget_container_preparation_CPU_r1_20261030.json)共26项：新增精确Docker观察/发布源5项，原采集7项，容器参数与worker元数据7项，原控制链验收器7项。worker路由测试使用明确元数据夹具并替换实际监督器调用，没有真实Docker启动、GPU模型或存储挂载；不能把这组测试称为双端整卡生产CPU接受。

下一步连接真实校准runner和完整科学验收，组合原授权/源/资产/预算准入及once入口。64GiB专用硬配额、双端受影响整卡CPU及包含所有阶段的报价完成后，提交14GPUh单次启动审批。原A32冻结、B36结果/费用和S原运行检查保持。
