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

## R4.2实际启动与两次检查

GitHub source `8925d16800d7d0c6266bc825ded78cc21a72284b`发布后，05:13:35.882198单次启动supervisor PID619726/start940227924；worker SHA `4aa6d0f846994773592c084f526a683519485ef30b5a82446c95a22be055d97b`，manifest SHA `d8e08ca06d2aae8503a444fbb48759f600a5c320bba8bbf05b5eb5f9b38f90e8`，独立新job按上述R4.2名称。

一次admission确认原source／全payload／manifest、原进程与本人容器活、只读root与空GPU设备一致，已完整绑定复用旧resolver成功证明及现存LPIPS权重，正在入口导入；尚无新命令终态通过。现有NVRTC库worker SHA `3d917ecfcbb1d6e1e834c0baf11a2a095c5c137d07e194b1795f2b8dcfa59ee2`，实际loader SHA `57801aa64be0fbb4d08a1a53032fbb96e55a11d0eefe5be75d761bb2659beae0`。fresh预检数据盘345,012,273,152字节／主存67,526,111,232字节仅供本资源准入。

- [实际launch](../reports/wc_four_card_offline_resources_CPU_R4_2_launch_20261022.json)／[一次admission](../reports/wc_four_card_offline_resources_CPU_R4_2_admission_20261022.json)
- `r4-2-cpu`：05:18一次技术半程，最早unix1792617455.8821979／05:17:35.882198。
- `r4-2-cpu-2`：05:24一次完整收件，最早unix1792617815.8821979／05:23:35.882198，保存后仅离线accept。

两定义已读回，原R4.1终态`r4-1-cpu-2`完成删除；两卡06:16原定义保持。R4.2状态仍为资源CPU在途，0新模型下载／环境安装／Cosmos权重／CUDA／真实评分／科研GPU／账本写入。

## 05:18槽实际05:19一次半程：入口仍失败，05:24终态保持

实际05:19:24.951087（unix1792617564.951087）仅一次原R4.2技术收件。PID/start/source／全部payload／manifest一致，supervisor和本人容器均退出；health报告05:14:13.447712结束／wall36.553971秒。唯一新入口导入命令exit1／精确marker缺失，LPIPS CPU探针未执行。原resolver成功复用证明、NVRTC／LPIPS记录及env／runtime保持，0Cosmos权重／CUDA／科研GPU／账本。

[半程原件](../reports/wc_four_card_offline_resources_CPU_R4_2_midpoint_20261022.json)与[14项技术边界](../reports/wc_four_card_offline_resources_CPU_R4_2_midpoint_technical_failure_boundary_20261022.json)已保存。本次未读最终result／日志／独立终态哈希或accept，不推测新异常、不沿用旧R4.1根因解释新失败；资源CPU不接受，无额外SSH或重派。半程r4-2-cpu已完成删除，r4-2-cpu-2仍05:24（最早unix1792617815.8821979）且新失败定位接续已读回，两卡06:16不改。

## 原科学与预算接续

原双卡四小时只读06:16保持，本任务不查双卡或改权威v2。cap226／origin79.99637737158223／历史和54科研行及状态保持。BANK24完整24→既定X-R／同D配额CPU诊断→完整1624顺序、原闭包与四CAL gate、完整1624具体12批准均保持；新机CPU／整卡报价／BANK24完整原件与费用／唯一权威预算交接前置不绕过。F/B关闭，无训练／人评／付费VLM／OMR。
