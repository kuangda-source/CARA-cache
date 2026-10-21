# 四卡资源补齐：固定公开资产先执行，受限模型等待可用授权来源

用户已直接要求完成资源准备。复用已经接受的env-r3、固定容器、runtime和GitHub base；准备文件不重装原环境，不修改原BANK24/完整1624的冻结部署。

## 已验证的下载与资产边界

自己的SSH master将服务器127.0.0.1:17897仅转发到本机127.0.0.1:7897代理。实际从四卡取得Qwen配置及SigLIP权重的HTTP206字节范围，数据可直接进入四卡数据盘，无需在Mac暂存整套模型。此通道不改FRP、共享服务器配置或其他用户任务。

固定公开阶段是原Qwen3Guard-Gen-0.6B和SigLIP两份snapshot，共14个推理文件、5,034,332,532字节。原官方Git-blob/SHA256清单不改；下载后逐文件重读哈希。容器隐藏GPU、只读挂载旧环境，只有新job和本人HF hub可写；CPU限制2核/16GiB。最长5400秒，实际launch后另安排一次技术半程和一次预计结束查收。此阶段完成仍不能称完整模型或GPU就绪。

固定NVIDIA文件仍缺授权：本机和四卡标准HF登录位置均无token，实际Cosmos-Predict2.5-2B原revision的权重与Guardrail文件返回401/GatedRepo。已向用户询问可用登录或可读模型路径；没有转运凭据或接受新的仓库条款。先继续公开部分与代码准备。

## 冻结生产模型引用

实际runtime checkpoint_db确认：主权重使用Cosmos-Predict2.5-2B的15a82a2ec231bc318692aa0456a36537c806e7d4，post-trained文件SHA256为565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47；tokenizer.pth来自6787e176dce74a101d922174a95dba29fa5f0c55。Guardrail revision d6d4bfa899a71454a700907664f3e88f503950cf保持。不会改成当前HF main或下载无关Cosmos3-Nano。

文本编码器按当前实际配置依赖继续闭包，只获取被选中的固定模型，不因注册表还存在其他模型就下载全部权重。原模型保护机制保持。

## 后续准入

固定模型完整哈希和离线导入接受后，再进行新机实际CUDA兼容、新scope生产CPU/完整报价和共同权威v2准入。不能把原双卡CPU、公开模型下载或CPU依赖组件的通过状态移植为新机完整接受。科学GPU未启动，原BANK24→完整1624顺序、具体整卡12GPUh批准与两卡原资源检查保持。

## 原件与实现

- [模型来源本机代理实测](../reports/wc_four_card_fixed_model_sources_local_proxy_probe_20261021.json)
- [四卡实际网络/认证前置](../reports/wc_four_card_model_preparation_preflight_20261021.json)
- [自己的代理实测及原runtime模型引用](../reports/wc_four_card_owned_proxy_and_fixed_asset_sources_20261021.json)
- [公开阶段配方](../manifests/wc_four_card_public_model_preparation_r1_20261021.json)
- [新公开资产worker](../scripts/prepare_wc_four_card_model_assets_r1.py)

当前为已实现并准备部署；生产资产下载/完整哈希仍待实际回执，完整模型/新机生产CPU/GPU接受均为false。
