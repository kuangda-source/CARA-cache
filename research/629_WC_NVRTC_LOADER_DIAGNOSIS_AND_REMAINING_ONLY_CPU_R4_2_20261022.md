# NVRTC加载路径定位与仅补剩余两命令的资源CPU R4.2

## 原R4.1完整失败收件

2026-10-22 05:05沿原launch一次terminal收件，再仅离线accept。原source e5eedef4、worker／manifest／全部payload一致，原supervisor与本人容器退出、资源锁释放；实际命令退出码0／1，完整资源CPU不接受。16项独立失败留存核对通过，原失败、环境及runtime均保留。

- [完整终态原件](../reports/wc_four_card_offline_resources_CPU_R4_1_terminal_20261022.json)
- [独立不接受](../reports/wc_four_card_offline_resources_CPU_R4_1_independent_acceptance_20261022.json)
- [完整失败审计](../reports/wc_four_card_offline_resources_CPU_R4_1_complete_failure_audit_20261022.json)

原Guardrail已成功从固定本地snapshot解析，后续入口导入在Transformer Engine的`_load_nvrtc()`失败：未配置CUDA_HOME／CUDA_PATH，回退命令`ldconfig -p`又因PATH内找不到ldconfig退出。额外一次、仅限本人环境的只读诊断确认现有`nvidia/cuda_nvrtc/lib/libnvrtc.so.12`为104,454,480字节；cuDNN／CUDA runtime等库也已安装。此为已保存的具体加载路径问题，当前尚未证明其他入口依赖全部通过。

已同时核对[官方NVIDIA v2.2加载逻辑](https://raw.githubusercontent.com/NVIDIA/TransformerEngine/v2.2/transformer_engine/common/__init__.py)：先搜索CUDA_HOME／CUDA_PATH下的NVRTC库，再尝试ldconfig。实际安装副本的源码与库布局另行绑定：[只读诊断](../reports/wc_four_card_R4_1_NVRTC_loader_readonly_diagnosis_20261022.json)。新版本使用真实现有库，不设置跳过Transformer Engine原生库加载的变量。

## 独立R4.2资源范围

[固定配方](../manifests/wc_four_card_offline_resources_cpu_r4_2_20261022.json)注册新job `wc-fourcard-offline-resources-cpu-r4-2-20261022`。只在该容器进程设置现有NVRTC包的CUDA_HOME／CUDA_PATH和原生库路径，补标准sbin路径；原env-r3、29组件、原合成解码、11runtime、原科研stage均不改。

复用原110离线解析／Reason tokenizer命令的原结果／manifest／worker／probe／完整日志SHA与命令0证明，不重复执行成功命令，也不把其原失败整体当通过。只新执行原封不动的受限推理入口导入与尚未执行的预训练LPIPS CPU探针，两个新命令独立保留。已下载AlexNet244,408,911字节与原线性权重必须原SHA复用，缓存缺失或不符直接失败；禁止再次下载。完整96／公开14文件接受继续复用，不重哈希26GB模型。

2CPU／16GiB、隐藏GPU、网络none、readonly root／workspace／Torch缓存，仅新job可写。允许LPIPS加载两个固定CPU权重文件并验证预训练线性张量、自零／扰动正值／重复一致；Cosmos权重加载／CUDA初始化／真实视频评分／科研GPU／账本写入仍为0。

16项本地控制通过，含实际安装loader函数的直接路径选择／旧回退复现、错误源／非零已完成命令／变更输入拒绝；这些不当远端生产CPU。源码先GitHub发布，再一次fresh自身资源与旧句柄／锁核对后单次派发。规划8分钟，半程4分钟、最终10分钟、整体上限20分钟；实际launch与两个检查由真实时刻另记，当前为准备完成、未派发。

终态必须原source／payload／两新命令／两个精确marker／原发布probe源码、原成功resolver复用证明、现有NVRTC源码及库的独立SHA、两LPIPS独立完整SHA、原环境与runtime不改、原supervisor／容器／锁退出分别接受。资源CPU通过不充新机CUDA兼容、BANK24／1624生产CPU／整卡报价或GPU-ready。

## 原科学与预算接续

原双卡四小时只读06:16保持，本任务不查双卡或改权威v2。cap226／origin79.99637737158223／历史和54科研行及状态保持。BANK24完整24→既定X-R／同D配额CPU诊断→完整1624顺序、原闭包与四CAL gate、完整1624具体12批准均保持；新机CPU／整卡报价／BANK24完整原件与费用／唯一权威预算交接前置不绕过。F/B关闭，无训练／人评／付费VLM／OMR。
