# E3 保留完整64位置：复用10、补54的运行块接线

2026-10-11，先登记后执行；继承[316实际验收](316_WC_E1_COMPLETE8_REAL_EQUIVALENCE_AND_E3_METADATA_SCOPE_20261011.md)。上一轮为实际进展：E1全8真实数值验收、持久化CPU R2验收、十候选及四参考原件重新hash完成。目标继续active。

## 完整科学范围与唯一费用范围

保留原两来源规则×四CAL×八方法的64位置、seed0、35请求/36更新/72CFG和93帧。不增加第九方法，不修改P层、密度、floor、maxP2、阶段A、RA阈值或借用的D漂移先验；保留所有旧退化、缺失和FAILED_TECH费用。

新位置manifest按原64顺序列出全部键：原八个合格AV28路径与E1 CPU_PREFIX的Human W1／β1共十个位置选择复用，其余54条选择完整生成。旧Human六个文件的缺失prepare不补造；其中W1对应E1新文件，β1对应原部分失败位置的新文件，其他五个旧完整Human方法仍须生成。复用不是独立复验。

新执行块按场景轮转、两个来源规则交错、八方法预先轮转排序；跳过已绑定的十个位置后，按同场景/同规则最多三条一块，共20块、54完整路径。每块使用独立真实模型进程，不把20块当20张独立卡绕过权限。**只有一张完整E3费用范围，所有20次加载、54路径、失败、搬运及清理一并预测和结算**。严格超过8 GPUh才针对整卡确认；当前不选择GPU、不沿用原64已消费授权。

## 接线变化与保留项

新模块以已验收的普通batch函数为源，只替换声明的请求/方法循环与cardinality，使用相同方法owner：SOURCE_RA用原RA owner，其余用已验收CPU存储owner；生产verifier只调整块数量和方法顺序，完整逐路径语义、两规则history、当前birth公式保留。物理执行、compiler、checkpoint的原两copy门、6GiB逻辑上限、4GiB工作reserve及4GiB前缀reserve全部保持。编译后的batch仅替换`PreparedInputReplay`绑定，提前保存真实成功prepare签名。

冷启动/三路径E1不证明旧14条长生命周期或泄漏根因；有限块用于避免未经验证的长生命周期，而不是宣布旧故障修复。新运行仍可能触发容量保护或其他技术失败，必须保留所有64位置/54生成槽并记录错误。

## 本次受影响CPU范围

复用已验收128完整CPU路径的算法证据，不重跑整个无关256尝试矩阵。新接线CPU选两规则下各一个完整八方法组，拆为3/3/2；flow OFF/ON，每个块比较原GPU deepcopy owner＋原prepare保存方式和CPU存储owner＋新持久化方式，同一Toy网络、条件、权重和RNG起点。

- 两规则×两flow×八方法×两实现＝**64成功完整CPU路径**，2304成功guided＋64final＝2368张量独立重读，32对各36＋final直接比较＝1184次。
- 每规则/flow增加一个三路径块末writer失败，共**12失败尝试路径**；全部76尝试均执行完整36步，共2736更新/5472CFG。失败不写最后vector、不删其计划位置，已有成功prepare在失败前的save原件中保留。
- CPU存储成功支路28个非SOURCE_RA方法×4检查点＝112次额外CPU存储恢复；失败块非RA恢复次数按实际所选方法报告，不事先把SOURCE_RA误算为CPU owner。
- 拒绝缺请求/方法、错来源规则、漏检查点、伪P floor、丢head成本、错A强度、foreign birth、错working age、伪校准；原件截断拒绝，实际normal8 metadata/RNG/object identity等证据继承316。
- 全64/十复用/54生成/20块的独立重建检查、遗漏/重复/顺序/超三条/外来复用拒绝；不因CPU只用代表组就缩减GPU科学范围。

CPU仅用现有Toy权重、attention、prepare、decode和JSON writer；运行原UniPC/WC/RF函数与完整restore/hooks。直接配对不依赖旧Toy随机初始化是否相同。禁止CUDA/下载，没有2B forward或真实视频、质量、干净速度结论。

CPU完成后继续新生产入口/启动资产/选卡监督和逐路径评分验证、冻结完整forecast。费用必须包含实测CPU存储开销；不得按旧8.3282×54/64或dense调用数直接称净速度。E2原完整76/9.869732459的具体批准仍待，准备E3不取消它或重复询问。
