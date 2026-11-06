# W1 自身轨迹诊断执行卡

2026-10-06；执行入口 v4.2。科学设计沿用[post-reference v4.1](WORLD_CACHE_POST_REFERENCE_WINDOW_20261006.md)与[原假设登记](../manifests/wc_post_reference_hypotheses_r1_20261006.json)，两者原字节保留。本卡只将原登记三场景诊断落实到生成、监督、身份桥和汇总，不新增方法、观测点或训练。

## 发现与要回答的问题

已有完整七个接受场景的 W1 终点比较是4改善/3退化，等场景均值 LPIPS 降低0.4388%。misc 的旧局部与终点同时退化；AV51 旧局部改善而终点退化；AV28 是较强正例。旧局部标签来自官方轨迹，完整 W1 视频来自候选自身轨迹，因此需要直接测量自身状态上的近似，而不能把旧标签跨轨迹当作真值。

本卡回答：两个负例在实际 W1 状态上的局部改善是否仍存在？保留混合结果，区分近似迁移、传播/误差方向和目标对齐等解释。不是独立确认，不将三个曝光场景或12个相关观测当作独立泛化证据。

## 唯一执行范围

- 卡：`WC-W1-OWN-STATE-SHADOW-R1-20261006-A`；run：`wc-w1-own-state-shadow-r1`。
- 原 CAL 索引按顺序4、7、0：misc、AV51、AV28；seed0，三个原 typed 请求和模型 setup保持，setup只变输出目录。
- 每场景36个 UniPC/Karras 更新、72次 CFG；768×432、93帧、16fps；原 scalar 参数、原逐场景 fixed mask、dense attention、probe2、decoder策略和后端保持。
- calls45/46、67/68，共12个观测；四个位置在原三mask均为skip。每对CFG来自相同实际solver输入，不分开推进求解器。
- 只新增三次 shadow ON 完整生成；旧 scalar OFF 作为强制身份桥。不重新生成OFF，不替换旧拒绝，不重跑旧WC或Native。
- 在同一实际W1状态比较官方WC近似、W1近似和完整teacher。teacher只评分，不写cache、anchor、latent、solver或未来动作。
- 在原服务器项目的独立目录执行；本地[冻结R3配置](../configs/wc_w1_own_state_production_r3_draft_20261006.json)仍为GPU未选、UUID空、authority空。

## 验收和保留规则

真实输出必须与对应旧W1视频的72次forward SHA、block counts、trace、cache/校准终态、sampler网格、pipeline witness、decoder身份、后端flags、视频SHA及93帧RGB全部相同。任一身份桥失败时标记技术失败，保留原件及实费；不换参考或缩成成功子集。CPU MockWriter/模拟RGB不作为真实codec、几何或视频身份的证据。

完整三场景各四观测；先在每场景内归约prewarp/postwarp residual及velocity MSE，报告official−scalar和scalar/official、有符号单点差值。非有限观测不纳入完整卡；缺失标缺失，不填零。无需3/3全改善：负例自身局部恶化支持优先检查校准迁移/候选状态，局部仍改善而终点退化支持继续检查传播、方向和目标差异；均不是调度原因的唯一证明。

只有实际视频身份桥成立才复用旧终点LPIPS；不将本批hash/teacher/冷启动耗时称为部署速度，不新增人工评审、W2、Head、LoRA、专家训练或稀疏搜索。

## 费用、监督和下一权限

[费用代理](../reports/wc_w1_own_state_cost_proxy_r1_20261006.json)：原三OFF流水线合计591.082秒，保守计入原整卡未分摊199.051秒、最近Native整卡未分摊112.953秒、12观测43.682秒代理；名义946.767秒、1.5倍压力1420.151秒，均不是硬界。

候选总cap1800秒、child1770、kill grace5；最大0.5GPUh计入现有累计24GPUh。准入CPU规划30秒，另要求4GiB数据盘空闲、项目f1锁、fresh目标GPU UUID/VRAM/compute process及账本门。单次预付、实际全wall结算，包含加载、诊断、失败、flush和释放；当前累计13.504302792/24h，48jobs，无inflight。不得重置旧费用或把预算余额当作此卡批准。

[140生产准备与CPU](../research/140_WC_W1_OWN_STATE_PRODUCTION_CARD_AND_CPU.md)已完成必要准备。R3独立181文件/source f68bac4，实际CPU七步exit0/14.969秒；核心13文件复用不重跑。原两次生产CPU失败、全部原件和失败日志保留。下一是本卡单独直接范围确认，然后冻结selected配置和已通过CPU的生产源码、fresh准入、唯一实际运行、实费/释放/终态全帧身份审计、三场景有符号诊断。

W3-B仍为原四交换、2父/16后缀/10输出、9600秒的单独待确认卡；已有确认问题不重复。本卡不代替或取消B，不改变当前科学主优先级。
