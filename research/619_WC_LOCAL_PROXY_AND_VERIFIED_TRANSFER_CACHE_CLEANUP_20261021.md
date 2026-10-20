# 本地代理与已验中转缓存清理

按人类最新要求，已先在四卡只读重验10份服务器副本完整SHA，再删除13个本机wheel/旧整包/已传增量/runtime重复包；实际释放1.958GiB，删除后可用11.992GiB。约0.38GiB的GitHub源码镜像、源码/验收/私有认证与技术日志保留；不动服务器资产、环境、实验或账本。后续网络使用本地127.0.0.1:7897 HTTP/HTTPS代理，优先直接落服务器数据盘/流式转运；确需本机中转时逐文件/分块，完整远端SHA验收后及时删除本机包，不堆积整套模型或重建已传full bundle。代理已实际返回Guardrail固定revision元数据200，但文件401/GatedRepo，本机无HF token文件/环境变量；没有模型权重下载，授权缺口与网络分开保留。原BANK24两卡02:30与完整1624具体12批准/前置均保持。

## 本次清理

仅清理本次四卡准备产生的临时副本：四个已传官方CUDA wheel、已传完整base和增量Git bundle、被新base替代的旧GitHub bundle、已完成decoder审计的原decord wheel、两份已传runtime归档。每项删除前核对本地SHA/文件身份、确认无打开句柄；服务器10个当前对应资产在本轮实际只读重新核对完整SHA。旧GitHub bundle的原commit仍在保留镜像中。仓库源码、科学原件、已装环境、模型、私有认证和技术日志保持。

本机删除13文件，逻辑大小1.925GiB，删除前实际分配1.961GiB；文件系统实测空闲增加1.958GiB。后者受并发文件系统活动影响，保留原始前后字节数，不以逻辑大小冒充实际释放量。

## 后续下载与转运约定

1. 网络受阻时使用当前本人本地代理，已核对HTTP/HTTPS为`http://127.0.0.1:7897`，按命令/进程使用，不更改共享服务器或其他FRP配置。
2. 优先让数据直接进入服务器本人数据盘，或流式/有界分块中转；本机不保存整套大模型。确需本机临时文件时先核对空间，逐项完成传输。
3. 服务端完整SHA与冻结manifest匹配、接收原件保存后，及时清理本机下载和打包副本，保留小体积SHA清单、接收回执及必要源码镜像。未验证的文件不因传输进程退出就删除。
4. 已验证的server staging base/runtime/wheel继续复用，后续只传必要delta；原R1完整安装launch不可重放。同步辅助脚本已支持本地base清理后的远端记录，不因本地缺包重建整个bundle。

## 实际网络与授权结果

本地代理访问`nvidia/Cosmos-Guardrail1`固定revision `d6d4bfa899a71454a700907664f3e88f503950cf`元数据HTTP200；同revision实际blocklist文件返回HTTP401、`X-Error-Code=GatedRepo`。本机没有现存HF token文件或相关环境变量，未使用或转运认证。本次未下载模型权重。后续仍按已授权来源/已验旧缓存准备模型；网络代理不能代替HF仓库授权，不能把元数据200当下载接受。

## 原件

- [本机清理逐项原件](../reports/wc_four_card_local_verified_transfer_cache_cleanup_20261021.json)
- [删除前服务器完整SHA复核](../reports/wc_four_card_transfer_assets_remote_retention_before_local_cleanup_20261021.json)
- [代理元数据200](../reports/wc_local_proxy_fixed_guardrail_metadata_probe_20261021.json)
- [实际文件401/GatedRepo](../reports/wc_local_proxy_fixed_guardrail_authorization_probe_20261021.json)
