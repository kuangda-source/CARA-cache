# N10固定源码、真实分词资源与质量测量预登记

2026-10-16。**最终自动质量评价的代码和文本预处理准备又补齐了一段：固定216份代码/配置，取得并校验真实BPE文件，9组文本的ViCLIP/OpenAI CLIP分词结果一致。** 在最终共同测试之前，已登记原六个维度、完整960指标位置和源码版本。实际模型CPU、神经网络权重、视频评分与整卡费用仍待完成。

当前N05原完整66/source15d77ac/原句柄与今天12:05一次查收不变。本轮未查询服务器或生成中间结果，没有新GPU任务。

## 1. 固定版本代码已具备本地副本

原468/479只保存九份说明/入口源码。本轮从同一VBench提交`fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490`取得`vbench/`下全部Python、配置与文本元数据，以及根目录说明/依赖/许可中存在的文件，共216份、1,483,691字节。每份均独立核对原Git blob SHA-1、字节数和SHA-256；与原九份身份全部一致，175份Python可在本地解析。

[代码包回执](../reports/wc_paper_N10_complete_pinned_code_resource_pack_20261016.json)保留全部原路径、固定提交URL与哈希。文件副本位于忽略目录`.sync/wc-N10-vbench-codepack-fd18b3d0-r1-20261016`，没有把上游大包或权重加入Git。这是原VBench代码包，不包括VBench-2.0、模型权重、完整第三方运行环境或官方基准全资产；没有import整个包或执行指标模型。

服务器已安装0.1.5与该pin的三处差异仍按468保留。新评分采用固定代码包，不与已安装版本静默混用；实际依赖和完整运行CPU验证仍须在评分前进行。

## 2. 一个实际部署边界：分词资源必须在导入之前就绪

固定源码的`SimpleTokenizer.__init__(bpe_path=default_bpe())`会在定义类时调用`default_bpe`。因此，等到创建模型或调用评分时才禁下载已经太晚。

[源定义CPU回执](../reports/wc_paper_N10_pinned_constructor_source_CPU_acceptance_20261016.json)使用原函数/类AST定义重现：缓存不存在时，请求一次`wget`；调用在模拟边界被阻断，没有创建真实下载进程。占位文件存在时不再请求下载，也说明上游这个检查本身不验证文件内容。该对照只覆盖原定义执行，不冒充整个VBench import或真实模型构造。

同回执还核对AMT-S的原配置、动态builder及`networks.AMT-S.Model`实际源码路径。构造回调为明确stand-in，未加载AMT权重。正式worker需提前校验资源SHA，并在独立进程中绑定源码/搜索路径。

## 3. 真实BPE与ViCLIP权重身份

从OpenAI CLIP固定提交`d05afc436d78f1c48dc0dbf8e5980a9d471f35f6`取得原BPE，1,356,917字节，Git blob与SHA-256均通过，gzip内容可完整读取。原文件SHA-256为`924691ac288e54409236115652ad4aa250f48203de50a9e4722a6ecd48d6804a`。

[真实分词CPU回执](../reports/wc_paper_N10_real_tokenizer_CPU_parity_20261016.json)：使用真实词表、原ViCLIP和原OpenAI CLIP函数/类，9组明确合成文本覆盖空串、空白、标点、大小写、Unicode与中文；token ID和decode逐项一致，词表大小49,408。资源在定义前已就绪，零隐式下载。仅在项目忽略目录准备`ftfy==6.3.1`与`wcwidth==0.2.13`，未改项目原venv或服务器环境。

这是原分词逻辑的CPU证据。完整包未import、ViCLIP编码器未加载，也没有语义视频分数；8帧视频编码与32-token模型接口仍须实际CPU核对。

[资源身份回执](../reports/wc_paper_N10_official_tokenizer_and_ViCLIP_checkpoint_identity_20261016.json)还固定HF模型仓库修订`83290ee59b4e2c0a4d198857edbc79dd186b8d44`所列的`ViClip-InternVid-10M-FLT.pth`：1,710,545,812字节，LFS预期SHA-256为`7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`。同仓库另一个4.14GB的`ViCLIP-L_InternVid-FLT-10M.pth`不是该源码要求的同一文件，不能互换。

本轮只核对该权重的官方元数据，未下载、读取或验证实际checkpoint。服务器先前只查过若干标准缓存目录，不能据此认定整机不存在；后续先做有范围的只读资源核对，再决定是否取得缺少的文件。

## 4. 测量定义现在登记，结果仍为空

[N10测量预登记](../manifests/wc_paper_N10_automatic_quality_measurement_prereg_r1_20261016.json)在N07最终输入/方法和视频尚未产生前登记：

- 全160生成位置×原六维度，共960指标位置；拒绝、失败、资源不足和不适用保留，不填零、不挑成功子集替代完整均值。
- 主体一致性、运动平滑、文本一致性为独立质量维度；动态程度为描述项，和一致性/平滑度一起报告。MUSIQ沿用旧`pyiqa==0.1.10`的已绑定SPAQ checkpoint与longer512全93帧预处理，主值是raw mean，不能和旧raw/100混写。
- 闪烁只用于在生成前已有权威静态标注的输入；无标注默认不适用，静态资格表和N07输入一起冻结。不增加人工标注或从生成后的视频挑静态样本。
- 源视频身份/93帧审计与指标内部采样分开；两seed先归到提示词再等权统计。没有加权VBench总分或自动物理正确性主张。

这里只冻结测量定义和代码选择。实际模型/依赖CPU、全部权重SHA、评分入口、GPU估价和执行权限未被这份manifest代替；费用为null，不填0。原草案与历史结果保持。

## 5. 下一步仍按主线优先级

N05在12:05一次完整验收后，优先冻结N07共同新输入/双seed测试，接着N08重复clean测速。N07冻结时同时保留本N10测量协议及生成前静态资格；N10正式评分复用其全部输出。

N10下一实质缺口是服务器已有DINO/AMT/RAFT/MUSIQ资源的实际哈希与源码依赖、ViCLIP完整权重和隔离CPU模型验证，再做完整评分费用。该准备不将N10升到N07/N08前面，也不恢复P/T1/F/B、训练、OMR或人评。

本轮0SSH、0GPUh、0服务器stage/runtime/预算写入。原累计cap/origin与完整单次严格少于12GPUh自主规则保持；原数值实现未改，所有实际质量与速度结果仍待真实原件。
