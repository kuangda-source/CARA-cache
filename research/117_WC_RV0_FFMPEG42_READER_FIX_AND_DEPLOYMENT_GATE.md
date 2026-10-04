# FFmpeg4.2读取修复与后续部署许可门

2026-10-04。上一轮[116指定LPIPS脚本服务器审计](116_WC_RV0_LPIPS_AUTHORIZED_SERVER_READONLY_AUDIT.md)为实际进展；本轮继续完成无需传送新私有代码的读取接口验证。新W3执行器/监督/reader/评分代码同步仍未获明确许可。目标保持完整8父/24后缀/18输出及后续科学验证，不以已有CPU结果缩小成功标准。

## 实际问题与修复

[原生版本/源码预检](../reports/wc_rv0_video_reader_native_preflight_20261004.json)确认服务器FFmpeg/ffprobe为4.2.7。[原参数失败回执](../reports/wc_rv0_video_reader_fps_mode_check_20261004.json)：原草案的`-fps_mode passthrough`直接返回`Unrecognized option`，exit1，RGB输出0字节。该失败发生在解码前，不能据旧RGB夹具或较新版本文档声称兼容。

[本地reader](../src/wcomr/rv0_video_reader.py)改为4.2支持的`-vsync 0`逐帧直通，继续执行原93帧/432×768/16fps及源PTS/timebase检查，不引入缩采样。FFmpeg官方历史文档/提交说明将0对应到passthrough模式；[官方记录](https://ffmpeg.org/pipermail/ffmpeg-cvslog/2021-December/129992.html)。本次以实际4.2.7命令验证兼容性，运行环境换版后应重新验证该参数。

[首次SSH测试适配器失败](../reports/wc_rv0_video_reader_ssh_native_stream_cpu_20261004.json)漏了`subprocess.PIPE`，在本地进入decoder上下文时停止、0/2完成；原回执保留，没有改生产逻辑来掩盖该失败。补齐本地适配器常量后另开[CPU R2读取回执](../reports/wc_rv0_video_reader_ssh_native_stream_cpu_r2_20261004.json)。

## 两真实原视频完整读取

R2直接调用当前本地reader的`probe_video`、`decoded_video`、`decode_stream`；只把subprocess传输指向既有SSH的服务器FFmpeg/ffprobe，远端没有上传或执行新reader代码。视频为112真实restore卡的两份既有父视频，原编码SHA分别`fa7f…c379`、`4d0f…82fb`；不是新的C/D或Native参考输出。

两份均完成93帧432×768 RGB uint8、每份92,565,504字节；完整源PTS/timebase、每帧RGB SHA和整流SHA记录，EOF检查/远端命令退出0通过。全RGB流直接交本地reader消费，没有保存视频或大张量到Git。每份约31.40/31.66秒含SSH传输及本地验证，不是模型推理速度或服务器纯解码计时。两原视频及权威预算的前后SHA逐个相同，未导入Torch、新GPU/费用/LPIPS视频分数均0。

[本地CPU R3合同](../reports/wc_rv0_execution_cpu_contract_r3_20261004.json)35拒绝控制、62 payload源码SHA及10文件语法通过，费用账本字节未变；旧原生审计器六拒绝控制源码未改，复用R2证据。当前[未选草案](../configs/wc_rv0_causal_r1_draft.json)仅更新reader SHA，旧62文件草案另存v4、R2合同保留原身份。40份实际因果CPU核心和9官方源未改，无需重复274秒核心回归。

初次在服务器项目根目录没找到Native CPU helper/contract，不是全盘资产缺失。依据111实际冻结部署路径重新定位，[三文件位置/哈希审计](../reports/wc_rv0_existing_native_CPU_source_location_audit_20261004.json)确认它们位于`.sync/wc-rv0-restore-r1-deploy1`且与本地/source793beed相同；不重复已通过的meta模式模型检查，也不将旧入口验收升级为新入口CPU通过。

## 当前门与停止条件

读取命令和本地reader跨SSH的完整真实视频路径已验证；服务器上新Python reader的导入、完整新运行/监督/评分入口、实际部署以及真实C/D因果控制仍未验证。完整18输出/24后缀未减少；正式同预算标签、Head、CONF、质量/物理或端到端收益仍未成立，107稀疏方向判断保持。

预算保持used11.022315686839217/13GPUh、45jobs、无inflight；原104单次和restore卡不重提。完整卡拟6900全wall+15准入，余额7119.663527秒，成本/峰值仍未测，不靠当前读取成功提交GPU。

[阻塞审计](../reports/wc_rv0_production_upload_blocked_audit_20261004.json)从当前对话复核三个连续goal回合：15e736b提出完整新代码同步许可；用户只明确允许LPIPS审计脚本并由b545f04完成；本轮修复读取/完成安全验证后，完整新代码同步许可仍未到达。三个回合均有实际进展，但剩余关键步骤不能用原生只读操作或单份LPIPS许可替代，现有安全准备已完成。同步本轮代码/回执/文档后，将自主goal设置为blocked以等待这项输入；研究目标保持未完成。

需要用户明确允许将新W3运行/监督/终态审计/reader/评分代码及绑定配置报告同步到同一服务器独立stage，先仅CPU验证。获准后恢复完整新入口实际CPU/source/assets/读取与评分接口门，再冻结执行身份、fresh UUID/VRAM/compute/锁/完整余额准入；真实完整C/D执行与释放审计后才做8个Native相对全93帧LPIPS视频对。同步许可本身不证明CPU通过、GPU已运行、正式标签可用或论文成立。
