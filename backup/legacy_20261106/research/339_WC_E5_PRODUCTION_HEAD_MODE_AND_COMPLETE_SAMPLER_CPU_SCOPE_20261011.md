# E5生产head模式与完整UniPC接线：CPU预登记（2026-10-11）

**本轮把已经有数值等价和调用节省证据的E5原型接到完整采样入口。** 固定生产合同启用了AdaLN LoRA及Wan FP32，上一轮普通head原型不能直接部署。新独立版本支持这些原生模式，保留早期CC／共享α=1／候选实际存在才省去原head的算法条件；没有把调用节省预先计成速度收益。

## 已核对的生产来源与改动

`wc_h0_eval_mode_contract_20261003.json`绑定2B模型2059174912参数、hidden2048／out16／patch2×2×1／adaln_lora_dim256、两个head模式均true。原生FinalLayer来源SHA为a41a1772f694ee338e4b91f032428ea81f28e80fb90990e2db86eb7d1ce30071。真实unpatchify位于MiniTrainDIT，绑定方法比较使用同self／func；生产默认要求原生函数字节码，只有显式CPU夹具可以声明Toy边界。

旧完整采样owner用final_layer forward hook记录head，原型guard会拒绝这个hook。新owner在候选已实际执行及原head选择处明确记录；独立Python实际调用事件检查这些记录和方法费用相同。新版本拒绝compiled calls、动态hooks、参数／模式／拓扑／子层数值配置变化；不放松旧版本guard，不改变原head或求解器的数值计算。previous_output是明确改变的记录字段，自身版本完整捕获和恢复继续包含它。

`early_head_elision_sampling_r1.py`只绑定新编译器、读出和owner。旧WC／RF／RA、D/P控制器、dense统计、投影计算、CPU-owned保存和原在途E4c源码保持。源码逆替换和AST检查只证明改动范围，不能代替运行验收。

## 完整受影响CPU范围

| 检查 | 预登记完整范围 |
|---|---:|
| Flow | OFF／ON |
| 控制器族 | 固定C/P/D、current-birth working-age C/P/D |
| 读出 | OFF、阶段W1、阶段β=1 |
| 新／旧版本 | 各一，合计24条完整路径 |
| 每条实际UniPC | 36更新／72 CFG |
| 全范围更新／CFG | 864／1728 |
| 写出后独立重读 | 24文件／888张量 |
| 新旧实际逐元素比较 | 12对，每对36 guided＋final＝444项 |
| 完整physical＋owned扰动恢复 | step12／30／35／36，共96次 |

两族分别使用一条声明Toy请求，不冒充四个真实CAL场景或独立科学样本。head使用固定原生FinalLayer小权重，并执行AdaLN／Wan两个真实模式；28原生Block／MLP、原生RF与UniPC和guarded采样调用执行，attention、条件／prepare／unpatchify、VAE解码和写出是明确Toy边界。全2B构造仅Meta：核对真实类、eval、原生unpatchify合同和子层eps变化拒绝；不加载真实权重或执行2B前向。

比较包括全部guided及final、实际动作／solver returns、条件身份与字段、RNG、D锚点／校准、工作来源／年龄／投影记录及current-birth source_policy。自己的完整状态恢复不能因跨版本previous_output差异省略。实际native head事件计数必须等于新旧各自记录，OFF不得省算，两个非OFF方式必须实际覆盖早期省算；不能将未覆盖测试报为通过。

上一轮动态guard拒绝／paired故障和旧完整采样writer清理不重复扩大矩阵；本轮受影响的真实模式、记录接口、两族完整求解器和自身恢复全部执行。失败保留原receipt／源码／已写完整路径，修复另登记新版本，不覆盖原attempt或缩分母。

## 执行与接续

独立411文件CPU stage：`.sync/wc-e5-complete-sampling-cpu-r1-20261011`，406继承来源＋5新载荷，提交后才同步CPU。CPU禁止CUDA初始化、下载和账本写入；预算前后hash可能因唯一原E4c的合法结算变化，必须按原supervisor核对原因，不能用CPU回执覆盖账本。此处尚无服务器CPU运行结果，也没有新GPU提交、训练或人工评审。

原E4c 4075406／4075494与唯一CPU等待器4079033现场继续，399在途源码不改／不重投。完整4父／16suffix／24teacher不缩。E4c全24结果仍是下一H-P-W1-WORKING-REFERENCE的依据；本轮E5不提前修改它。E2全76／9.869732459GPUh、E3全64／12.377456422GPUh原准确批准待，不拆卡或重问。

用户本窗口单卡预计≤8GPUh自主，严格>8需准确整卡批准；新48累计窗口保持。前settled40.313761639725／cap77.895246589659、剩37.581484949934，当前唯一在途预留非实耗。CPU通过并独立重读后，再登记完整真实旧／新等价和同边界费用卡，加载、搬运、记录成本全部计费。
