# S 模型加载入口、S 优先与另一张 A6000

用户最新要求资源允许时优先 S，随后要求停止反复查看资源，并询问两卡主机的另一张 GPU。已暂停原 `q1` 资源 heartbeat；研究目标和 Q1 原单次批准保持，不再定时轮询。一次有界连接检查发现旧强制跳板已关闭，现有 `two_card_lan` 的 Tailscale 跳板也超时，未修改 SSH 或远端进程。最后有效快照为09:20：另一张 A6000 `GPU-de9a5370-cd87-0f1c-a48e-288888777dd3` 约450MiB、0%、42C、无计算进程；不能把旧快照称为当前空闲。

另一张卡在硬件类别上适合 S。原 A6000 版本复用旧 OFF，要求原 GPU UUID；新 [另一卡物理版本](S_PHYSICAL_TWO_CARD_OTHER_GPU_R2.json) 使用原十角色上限的十条新请求，不复用旧 OFF，保留旧版本。目标仍为108同状态标签、八 raw、24 anchor；物理代价变为468pair/936head/552deep block调用。[前瞻绑定](S_OTHER_A6000_BINDING_PROPOSAL_R2.json)尚缺对应完整报价、双端实际CPU/资产/资源准入；没有改写现有同机并发约定或提交GPU。

新的 `sq_s_model_entry_r1.execute` 在已有 S 准入上下文中只尝试加载一次原 inference，核对 setup、两个输入对象、原模型/experiment、BF16/Wan/条件步设置、模式和后端，再进入冻结的完整矩阵编排；成功或异常均清理环境。GPU释放、原账单和科学接受仍是外层义务。原 S runner、数值采集器与原物理范围文件保持未改。

本地15项CPU边界控制通过，环境、模型加载和矩阵均为显式 stand-in，没有权重、前向或CUDA。已准备原固定Linux环境下的真实 Cosmos配置解析器探针；实际远端运行尚未完成。代码保留真实 Path 类型的 output_dir，不能按字符串相等误拒绝原解析器。Q1授权、外卡复用、CPU解码替身、原setup/输入改变、加载/矩阵/清理失败均有拒绝控制。

当前工作隔离在本机 `worldcache_omr_sq_entry` 原生Git工作树、分支 `codex/sq-production-entry-20261029`，从已同步的 S 编排接受分支建立；不占用主线共享索引。S GPU完整entry、host allocation、独立终态/中央结算与整卡审阅仍未完成，14/17GPUh仍是未冻结旧提案。继续本地CPU准备，等入口可执行时只做必要的一次fresh准入，不持续轮询资源。
