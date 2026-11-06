# confirm10 continuation — skip C05, reuse C01–C04 by hash

计划 run `cara-generator-v1-confirm10-continuation-r1-20261106`。准备阶段原话保存在 `authority.preparation_authority`：「确认重试 confirm10 续跑准备：跳过 C05，只做预注册和纯 CPU 验收，不上卡、不碰账本。」`preparation_was_not_gpu_authority=true` 只记录那段历史。精确重报已经交付。`authority.user_quote` 与 `future_dispatch_quote` 都是实际启动原话：「confirm10 跳过 C05 整组，不绕过护栏；精确重报后在空闲卡上续跑，硬限按重报，k18 等它完成后再跑。」`execution_authorized`、`ledger_reservation_authorized`、`sync_launch_authorized` 为 true；`this_commit_dispatches` 仍为 false。`quote.json` 的 `execution_authorized` 与 `GPU_dispatch_ready` 也是 true。科学范围不变；authority 和 gpu preference 写入后 scope hash 按同一张卡重算。GPU 启动仍须每卡 fresh：Linux CPU、source、asset、storage、owner lock，以及原 21 份输出 hash 核对通过后，才按中心 2.0062773472222224 GPUh、硬限 2.2 GPUh 做唯一 reserve/dispatch。本文件不启动、不联网、不碰账本，也不动 P 探针或 k18。

原 run `cara-generator-v1-confirm10-r1-20261105` 保持原样：collection 仍是 `FAILED_NO_RETRY`，scope `9fb88510b5c5b30bde05f619ad60fa609359a76c6e627d79f27c6c52da0f1904`，launch `fe91fe0468944be18b8c0950c33e092b`，唯一结算 actual `1.3313886947699616` GPUh，billing `471f3b73d840cb841f7148fa77617d10f1491e62a276961a2825984f73ae4e42`。不改它的 collection、settlement 或 manifest。

## 继承与跳过

C01–C04 的 21 份已完成输出按原 inventory/collection 的 path、bytes 和 sha256 只读复用：CONFIRM10_001–021，其中 20 formal + 1 warm。四条 formal Native36 和 16 个已评分 Alex pair 也只复用，不重跑、不重评分。C05 `av_snowy_1_0` 的 CONFIRM10_022–026 整组不进入续跑，包括 TEXT_REJECTED 的 022。prompt、seed、mask 和 guardrail 都不改，不盲重试 022，也不换输入。

续跑矩阵只保留原顺序的 CONFIRM10_027 至 CONFIRM10_051：25 formal、0 warm，C06–C10 各五臂。角色仍是 NATIVE35、F17-A2+lightC、R18C、R16C、R21C，代码与 light C 语义沿用原 run。

科学分母是九个输入 C01–C04、C06–C10。五臂齐全时 36 个 Alex pair（16 个已继承 + 20 个新评分）。C05 不在配对分母。原十输入主终点保持 NOT_EVALUABLE。本预注册不宣称这九输入终点已经完成。

主终点规则不变，只作用在这九个 prompt：ΔAlex = LPIPS(R18C, 同 seed Native36) − LPIPS(F17, 同 seed Native36)，等权均值、prompt-level paired percentile bootstrap 95% CI（100000 次，seed 20261105）。better 仍是 mean<0 且 CI 上界<0；否则次要非劣界限 +0.01；再否则 INCONCLUSIVE。冻结预测仍是旧四输入 mean ratio 0.932/0.825/0.652，不改用这次部分实测均值，也不重拟合。

任一请求若返回 TEXT_REJECTED 或其他非 COMPLETE，先把该 status、solver_steps 和 guided_pairs 写进行，再按原失败行为停止为 FAILED_NO_RETRY。没有自动 retry，也不替换输入。

## 报价

价目与原 quote 相同，公式仍是 `T_request=70.734852+6.772260*nD+0.993956*nA+0.637948*nC`，light C 的 C 成本为 0：

| arm | seconds |
|---|---:|
| NATIVE35 | 314.53621200000003 |
| F17_A2_LIGHT_C | 195.802832 |
| R18C | 192.635532 |
| R16C | 179.091012 |
| R21C | 212.952312 |

五臂各一条为 1095.0179 秒。25 formal 请求和为 **5475.0895** 秒。中心 `(1.1*sum+1200)/3600` = **2.0062773472222224 GPUh**。范围 **1.7021057083333335–2.1583631666666667 GPUh**。上界向上取 0.1 的硬限是 **2.2 GPUh**。墙钟中心 7222.59845 秒，含 600 秒加载和 600 秒释放。

所给 5465.0538 秒、中心 1.919259795 GPUh、范围 1.586821375–2.1223512 和硬限 2.1 不是这组原价的公式解；2.1 低于公式上界，不用。含 C05 的 30 请求报价 2.34086615/2.6 也不用。部分实测 T_request/T_DD 不换成新锚点。

评分只在两件事都成立之后进行：原 21 份成功输出的 latent/video 仍与登记 hash 一致，且本续跑已经唯一结算、GPU 与 CPU 进程已释放、容器成功退出。C01–C04 的 16 对不重算。k18 等本续跑完成后再单独安排，本卡不含 k18。
