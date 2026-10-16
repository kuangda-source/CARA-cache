# 固定评分权重的SSH传输与原件接线已准备

2026-10-16。**N10的本机权重→服务器原件→五模型CPU部署接线已经补齐，九项小文件控制与一项完整打包接口检查通过。** 14:00取得本机原资源的完整验收后，便可单次传输同一固定文件；当前尚未执行实际传输或模型验证。

## 传输做什么

新[传输入口](../scripts/relay_wc_N10_viclip_resource_r1.py)固定使用507的同一ViCLIP文件、大小和SHA。`launch`先要求原本机查收为终态、超过原ETA、完整大小/独立SHA正确，并重新核对实际本机文件；在该条件成立前，不执行Git、SSH或派发。

通过后，入口绑定已提交源码，在独立本机stage只派发一个低优先级worker。worker为服务器创建fresh独立资源目录和固定注册，以原单次SCP复制到`.part`。SCP结束后，服务器独立读取完整大小/SHA，只有精确匹配才rename并写原result。局部文件、连接错误和未知状态保留，不自动续传、重试或覆盖旧stage。检查不写全局模型缓存、预算或生成任务目录。

长传输按启动后30分钟安排一次查收。`capture`在原ETA之前拒绝查询；到时核对原Mac PID、启动时间、不可变worker和参数，读取原SCP结果和服务器注册/原result，独立全文件SHA。Mac进程身份明确标为`LOCAL_MACOS_SCP_RELAY`，没有伪造服务器/proc句柄。`nice`执行为Python后的同PID身份继续有效；PID复用、其他worker及原件变动不混同。

## 与后续五模型CPU的衔接

远端完整资源查收使用既有`N10_ORIGINAL_RESOURCE_ONCE_CAPTURE`字节接口，额外保留本机下载、原SCP及服务器校验的来源。已在本地实际调用原五模型`packet()`：以显式合成的资源回执测试接口，复用真实固定代码/BPE生成227份payload、1651868字节打包，五角色保持完整。

这项接口检查没有权重载入、Torch模型运行、SSH部署或实际传输；合成回执仅位于已回收的临时测试目录，不能当真实资源供模型启动。资源真实接受后仍须实际五模型CPU验证；N07/N08在运行时，原CPU部署工具对重模型返回deferred，保持主线优先。

## 本轮验证与实际状态

九项控制覆盖fresh注册、原目录不覆盖、完整/截断/超长/错SHA文件的rename边界、终态独立读取、未接受资源在任何派发前拒绝、接受后本机文件变化拒绝、失败SCP保留且同worker不能重复派发、ETA前不查收，以及Mac nice执行变化/PID复用识别。原先八项回执保持，增加进程身份控制后的九项回执单列。

本轮未查N07句柄或科学partial，未SSH、写服务器、派GPU或改账。原N07/source140d0a6、1115797/1115898/post1115798、完整180、累计cap113和**10月17日05:30一次验收**保持。原本机下载18318仍按**今天14:00一次查收**，本轮没有提前检查其进度。

## 已准备的接续命令

只在原本机资源独立完整接受后执行，使用新的原件回执路径：

```sh
.venv/bin/python scripts/relay_wc_N10_viclip_resource_r1.py launch \
  --local-resource-capture reports/本机原资源完整查收.json \
  --stage .sync/wc-N10-viclip-relay-r3-20261016 \
  --output reports/wc_paper_N10_ViCLIP_relay_R3_launch_20261016.json
```

实际启动后按原launch的ETA另约一次：

```sh
.venv/bin/python scripts/relay_wc_N10_viclip_resource_r1.py capture \
  --launch-ref reports/wc_paper_N10_ViCLIP_relay_R3_launch_20261016.json \
  --output reports/新的服务器资源原件查收.json
```

若原任务仍在途，只依据剩余字节/阶段重新估时，另约一次后结束。终态资源可用也不自动启动重模型或GPU评分。F/B关闭、原主线N07→N08→N09/10和严格<12 GPUh自主规则保持。

## 原件

- [九项CPU控制及源码SHA](../reports/wc_paper_N10_resource_relay_local_CPU_R2_preparation_20261016.json)，[原八项回执](../reports/wc_paper_N10_resource_relay_local_CPU_preparation_20261016.json)。
- [五模型打包接口检查](../reports/wc_paper_N10_relay_to_five_model_packet_schema_CPU_20261016.json)。
- [小文件与进程边界控制源码](../tests/test_N10_resource_relay_r1.py)。
- [507本机资源下载原身份](507_WC_N10_SERVER_RESOURCE_TIMEOUT_RETAINED_LOCAL_PROXY_DOWNLOAD_AND_MAINLINE_PRIORITY_20261016.md)、[505完整模型CPU链](505_WC_N10_COMPLETE_FIVE_MODEL_CPU_BATCH_STAGING_AND_INDEPENDENT_ACCEPTANCE_READY_20261016.md)、[506完整共同GPU任务](506_WC_N07_FULL180_HUMAN_APPROVED_CAP113_GPU_ADMITTED_AND_0530_COLLECTION_20261016.md)。
