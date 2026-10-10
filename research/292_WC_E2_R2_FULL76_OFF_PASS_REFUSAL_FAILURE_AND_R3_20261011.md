# E2 R2完整flow OFF数值通过、拒绝处理失败与R3

2026-10-11。R2 sourceb3a117a、212载荷，监督4042510／子4042511均退出1并消失。原终态独立捕获保留：flow OFF完整76路径已执行，full36原件重载、全部16代表计时动作／final／Toy writer等价、原四种方法36 guided及final逐位旧结果比较、十类mutation／最后tensor截断拒绝完成；最后parity writer故障保留76位置。此后TEXT_REJECTED控制抛原pinned异常，flow ON尚未开始，整项CPU仍失败，不追认为完整通过或真实2B等价。

pinned Inference._generate_sample在两处官方text／video guardrail拒绝时：keep_going=False抛明确异常，True返回None；generate未吞异常。R3在单路径hook安装期临时使用原keep_going=True，完成及异常时恢复原值。仅官方两处拒绝返回None；其余计算／decode／写出异常仍传播，不改guardrail输出、阈值或替代视频。Native也通过原run_native_request分类，而无需吞原异常。额外加入Native text／video拒绝控制，全部八拒绝（四／流）均保存原身份。

完整R3flow OFF／ON各76成功、总152；八旧saved Toy parity、32新timing配对、20mutation、两实际截断与两个76位置写出失败保持。R2全部原bytes／stage保留，R3新登记／目录，禁止在跑目录改源。生产入口／validator已草拟仅syntax，完整生产CPU与source资产门未执行。

整张E2当前保守forecast9.869732459 GPUh：原72科学位置＋四追加等价，共76；原full64的35%费用余量与实测Native、A成本，按全部76 Native再加每步复用费用计数。它不是实测速度／硬上界；没有用未经测量的clean节省下调，也未拆范围。严格超过用户本轮8h，待完整CPU和具体生产准备完成后提出完整卡确认；此处不提前申请／提交GPU。当前额外GPU0，预算仍39.183807748／77.895246590，新48余38.711438842。
