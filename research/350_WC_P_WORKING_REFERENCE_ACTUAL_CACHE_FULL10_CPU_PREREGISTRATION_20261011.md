# P 工作参考的实际缓存接线与两 flow 完整 CPU 预登记

**下一候选已经从数学组件接到实际缓存读出。** 新实现只在 C 读取合法 P 来源时使用 `r_P + beta_D*(p_current-p_P)`；beta 继续只从真 D 拟合，D 来源沿用原读出，P 不进入真 D 校准或零风险锚点。当前完成源码接线和语法检查，完整 CPU 实际验收尚待，未产生新 GPU 或质量结果。

## 研究价值与范围

335 的 H-P-W1-WORKING-REFERENCE 和 345 的完整来源年龄实测保持。此前 P/D 局部误差差异包含来源、D 拟合历史、flow 与后续轨迹多个因素；本候选只改变近似的参考点，先判断接线与坐标是否正确，不由局部差异宣布整个部分刷新方向失败。

新模块 `p_working_reference_readout_r1.py` 在原隐藏状态回调内，直接读取当前分支的 `net.probe_residual_cache[branch]` 与 `net.residual_cache[branch]`。它们是实际 D/P 继续计算写入的 prewarp 缓存，不能用真 D 锚点或已 warp 隐藏状态代替。来源必须属于当前请求、条件和 CFG 分支，出生步严格早于当前步，D 拟合锚点严格早于 P 出生。候选继续调用原源码提取的 flow warp、原生 checkpoint head 和 RF 输出转换，保留原 head 与候选 head 全部成本，不混入在途 E5 的省 head 修改。

数学组件 R2 的 scalar/unit、七种 fallback、完整 D 状态与 RNG 保持证据复用，不重跑。实际接线中的非法 P 来源或几何、缺少有效 D 拟合使用未修改的官方 C 输出，不执行候选 head。D 来源完全沿用旧实现。此次不是新刷新控制器，也不是 P 来源可零风险复用的证明。

## 完整 CPU 卡

`WC-P-WORKING-REFERENCE-TWO-FLOW-FULL10-CPU-R1-20261011-A`：两 flow 各一个声明的 Toy 请求，每个请求保留 OFF、旧 D-reference W1、新 P-reference W1、旧 D-reference beta=1、新 P-reference beta=1，共 **10 条完整普通 UniPC 路径、360 更新、720 CFG、10 个原张量文件／370 张量、40 次完整物理与所属状态扰动恢复**。使用原完整 RF／WC／Block／条件／采样管线与已经验收的原生 checkpoint head、AdaLN LoRA/Wan FP32 标志；小权重、attention、prepare/unpatchify、decoder/writer 为明确 Toy 边界。

新候选在每个实际 C/P 回调独立重建公式，核对真实缓存、exact warp 后的输入确实进入原生 head；保留两 CFG 分支、完整 D 状态、缓存与 RNG 不变检查。前十个尚未读 P 的更新必须与旧方法相同；随后新方法须实际改变 solver 返回，避免候选接线未被调用却称通过。D/C/P 完整动作、来源风险、条件、参数和四状态恢复必须通过；全文件实际重新读取、哈希、有限 FP32 几何与 36+1 张量逐项校验，不以存在文件代替验收。

注册 `manifests/wc_p_working_reference_sampling_cpu_r1_20261011.json`，在独立目录复用原 R6 的 434 个冻结字节并增加六个绑定文件，共 440。CPU 禁止 CUDA、权重下载及账本写入。若原 GPU 在 CPU 期间正常结算，单独记录账本前后 SHA，不把合法并发结算认作 CPU 费用。

## 在途 E5 与后续顺序

真实 E5 全24、source eff2b71、原 GPU 4103103/4103190、自动终态 CPU 4103104 与 456 载荷保持，不改或重投。原 AV_R1 日志已记录 LEGACY_OFF 完整36步、视频通过 guardrail 并保存，FAST_OFF 随后开始；这是路径进度，完整新旧等价、反向顺序重复与所有可配对93帧仍待独立验收。E5 验收后才能报告真实省 head 与时间，不把 CPU 的 head100→82／128→94当作真实速度。

P 的完整 CPU 通过后，准备小型固定实际状态 teacher 诊断，保留旧读出、P 工作参考、beta=1 强对照，两 flow 与 P/D 来源条件。先登记完整配对及实测成本，再按现行单张完整≤8 GPUh授权推进，严格>8继续具体确认。不先训练、不引入人工评审，也不改 E2/E3 原完整范围或取消其尚待的具体批准。

前已结算 41.908688946 GPUh、累计上限77.895246590，新48窗口余35.986557644；E5 第79作业仍在途，账本上限预留不是已实耗。本次 P 新GPU0，目标保持 active。
