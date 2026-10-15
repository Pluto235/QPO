# Recollimation-kink 伽马射线 QPO 研究路线图

> 版本：v1.1，2026-07-28  
> 基础：PDC `~/qposim/hxf_toroidal_fig` 已完成的 Hu et al. 六组基线算例，以及 MHD3 精细时空采样算例 `116705`  
> 核心目标：从“复现喷流动力学”推进到“检验 recollimation 触发的 kink 是否能产生可观测的瞬态伽马射线 QPO”

## 1. 最终要回答的科学问题

建议把课题收敛为下面这个可检验的问题：

> 在什么喷流条件下，过压喷流形成的 recollimation structure 能触发或增强 current-driven `m=1` kink，并通过磁能耗散和非热粒子加速，产生经光行时、Doppler boosting、辐射冷却和真实采样卷积后仍可探测的伽马射线准周期变化？

这个问题包含四段必须逐段建立的因果链：

```mermaid
flowchart LR
    A["过压磁化喷流"] --> B["recollimation shock / nozzle"]
    B --> C["current-driven m=1 kink"]
    C --> D["磁能转换与粒子注入"]
    D --> E["synchrotron + SSC 辐射"]
    E --> F["含光行时和 Doppler 效应的光变"]
    F --> G["通过红噪声与 trials 检验的瞬态 QPO"]
```

论文不能只展示一条弯曲的喷流或一张周期图。每个箭头都需要独立诊断、对照算例和量化证据。

### 1.1 主假设

- **H1：动力学触发。** recollimation 区域会增强低 pitch、环向磁场占优喷流中的 `m=1` current-driven kink。
- **H2：能量转换。** `m=1` 模式增强后，电流集中、磁能下降和热能/非热粒子能量增加在时空上相关。
- **H3：辐射响应。** 该准周期能量释放会在 X 射线和 SSC 主导的 GeV/TeV 光变中留下相关但可能不同相位、不同振幅的信号。
- **H4：可观测性。** 信号经过体积积分、光行时、Doppler boosting、冷却、采样间隔和观测误差后，仍能在限定参数区间内通过全局显著性检验。

### 1.2 必须允许的零结果

以下结果同样具有科学价值：

- 动力学中存在 kink 周期，但 SSC 冷却或光行时把周期抹平；
- X 射线有周期而 GeV/TeV 没有，或反之；
- 只有特定视角、磁化度或 pitch 下可观测；
- 当前 Hu et al. 参数下没有稳健周期，只出现短暂、漂移的准周期活动；
- RTI/KHI 造成的随机界面扰动比 kink 更强，无法形成显著 QPO。

因此预期结论应是“给出 QPO 可产生/不可产生的参数范围和物理原因”，而不是预设必须复现某个观测周期。

## 2. 当前基础与边界

### 2.1 已完成的工作

PDC 目录 `~/qposim/hxf_toroidal_fig` 中六组 Hu et al. Table 2 基线算例均已运行到 `t=400 R_j/c`，最终输出为 `data.0020.dbl`：

| 算例 | 当前网格 | 当前用途 | 状态 |
|---|---:|---|---|
| MHD1-2D | `250 x 1 x 600` | 轴对称基准与论文设置检查 | 完成，网格与论文一致 |
| HD | `320 x 320 x 384`，uniform | 无磁场界面不稳定性对照 | 完成 |
| MHD1 | `280 x 280 x 336`，uniform | 3D 磁化基准 | 完成 |
| MHD2 | `300 x 300 x 336`，mapped | pitch/磁化参数对照 | 完成 |
| MHD3-baseline | `300 x 300 x 336`，mapped | 已复现 Hu et al. 第一篇文章 kink 的低分辨率基线 | 完成，确认 kink |
| MHD2w | `300 x 300 x 336`，mapped | 弱场对照 | 完成 |

此外，MHD3 精细时空采样算例已经完成：

| 项目 | PDC 审计结果 |
|---|---|
| Slurm job | `116705`，名称 `MHD3-hi` |
| 运行路径 | `~/qposim/hxf_toroidal_fig/MHD3/runs/116705` |
| 网格 | `320 x 320 x 450`，Cartesian mapped transverse grid |
| 有效分辨率 | 横向核心 `48 cells/R_j`；轴向 `7.5 cells/R_j` |
| 物理时间 | 从 `t=0` 独立运行到 `t=400 R_j/c` |
| 输出策略 | `t=0-300` 每 `10 R_j/c`；`t=300-400` 每 `1 R_j/c` |
| 数据量 | 131 个完整 3D 双精度快照；每帧 `3,317,760,000` bytes；目录约 `405 GiB` |
| 数值设置 | RMHD、PPM、RK3、TVDLF、Eight-Waves、`CFL=0.1` |
| 物理参数 | 与 MHD3-baseline 的 `rho_j/rho_a`、`p_a`、`Gamma_j`、`B0`、磁化半径和 `k=sqrt(10)` 相同 |
| 计算资源 | 3 张 Tesla V100；两个阶段总计算时间约 20 h 34 min |
| 完整性 | 最终时间 `400`，131 行 `dbl.out`，所有快照大小一致，stderr 为空，文本日志 fatal scan 无命中 |

`116705` 随运行归档了 executable、`definitions.hpp`、初始化源码、两个阶段的 `pluto.ini`、`run_staged.sh` 和 GPU telemetry。2026-07-28 审计时任务已结束，用户队列中没有剩余 Slurm 作业。

已有的正面结果：

- 六组运行均正常结束，未发现 NaN、MPI abort 或 `QuitPLUTO`；
- MHD1-2D 的入口压力、Lorentz 因子和原始量重建误差检查通过；
- 纵向切片定性复现了 HD/MHD2/MHD2w 较强界面扰动、MHD3 较连贯的趋势；
- MHD3 已复现 Hu et al. 第一篇文章中的 kink 形态和演化；在论文复现的识别层级上，可以确认该算例已经出现 kink；
- MHD3-baseline 的 tracer 诊断也显示小幅、较相干的 `m=1` 分量，与上述识别一致；
- `116705` 把 MHD3 核心横向分辨率从 `39` 提高到 `48 cells/R_j`，轴向从 `5.6` 提高到 `7.5 cells/R_j`，总单元数增加约 52%；
- `116705` 提供了 `t=300-400` 的 101 个高 cadence 快照，已经具备开展模式传播和准周期 pilot 分析的数据条件。

### 2.2 当前结果还不能证明什么

- 除 `116705` 外，3D 基线算例仍低于论文分辨率，且各算例的分辨率和网格映射方式不一致；
- `116705` 横向核心 `48 cells/R_j` 已接近论文的 `50 cells/R_j`，但轴向 `7.5 cells/R_j` 仍低于论文的 `10 cells/R_j`；
- 一个加密算例不能单独证明数值收敛；仍需把 MHD3-baseline 与 `116705` 的 nozzle、`A_m`、能量和混合率做定量比较；
- `116695` 的 runtime log 与 `116705` 一致显示 RMHD、Eight-Waves、PPM、TVDLF，且 `pluto.ini` 物理参数相同；但旧运行目录未归档 definitions/初始化源码，两个 executable 哈希也不同，比较前仍要追溯旧 build 的编译级 flags；
- 六组基线输出间隔仍为 `20 R_j/c`、各 21 帧；只有 `116705` 在 `t=300-400` 具有 `1 R_j/c` cadence；
- 这 101 个高 cadence 快照尚未完成 `m=1-4` 时序分析，因此还不能声称已经测得 kink 周期或覆盖了 5 个以上相干周期；
- 固定 `y ~ 0` 纵向切片不能区分 kink、RTI、KHI 和随机界面湍动；
- 包括 `116705` 在内的当前计算都没有非热粒子、辐射或冷却：`PARTICLES=NO`、`RADIATION=NO`、`COOLING=NO`；
- 当前计算是无量纲动力学，尚不能直接把模拟周期等同于 Mrk 421 的天/年尺度周期；
- 目前可以声称“完成六组动力学复现、在 MHD3 中确认 kink，并获得首个近论文横向分辨率的高 cadence 数据集”；还不能声称“完成网格收敛”“测得稳健 kink 周期”或“确认伽马射线 QPO”。

### 2.3 课题范围

**主线：** 低 pitch、环向场占优 RMHD 喷流中的 recollimation-kink-SSC 机制。  
**源标定：** 先用 Mrk 421 作为 HBL benchmark，但结论面向 HBL blazar 的一般条件。  
**重点波段：** TeV 和 GeV 伽马射线，X 射线作为同步辐射和电子冷却的关键对照。  
**暂不主攻：** 黑洞吸积盘产生周期、双黑洞、喷流进动等其他 QPO 起源；它们放在论文讨论中作为竞争模型。

## 3. 路线图总览

| 阶段 | 当前状态 | 建议周期 | 核心任务 | 阶段产物 |
|---|---|---:|---|---|
| 0. 冻结基线 | 部分完成：`116705` 自归档充分，campaign manifest/checksum 待补 | 1 周 | 保存配置、数值修改、日志和校验信息 | baseline manifest |
| 1. 动力学定量复现 | kink 识别已完成；模式增长/传播定量待完成 | 3-5 周 | 从现有输出重建论文诊断和 3D 模式诊断 | dynamics report v1 |
| 2. 网格与物理对照 | 部分完成：MHD3 首个加密层级已完成 | 4-8 周，可并行 | 定量分辨率比较、统一网格和 recollimation/kink 对照 | controlled suite |
| 3. 高 cadence pilot | 数据生成完成：`t=300-400`、`dt_out=1`；模式分析待做 | 2-4 周 | 测 `m=1` 周期、相干时间并决定是否续跑 | high-cadence pilot report |
| 4. 伽马射线 proxy | 未开始 | 3-5 周 | 耗散代理、Doppler 和 light-travel-time 快速筛选 | proxy light curves |
| 5. 非热电子与 SSC | 未开始 | 2-4 个月 | 电子输运、synchrotron/SSC、KN、冷却、慢光 | physical light curves |
| 6. 合成观测与 QPO 统计 | 未开始 | 1-2 个月 | 真实 cadence、噪声、CWT/WWZ/PSD、全局显著性 | detectability map |
| 7. 论文与复现包 | 未开始 | 1-2 个月 | 图表、方法、数据产品、代码和审稿自检 | manuscript + release |

完整物理版本按 **12-18 个月**安排更现实。只完成动力学和明确标注的辐射 proxy，可以形成阶段性报告，但不足以强声称“kink 产生了真实伽马射线 QPO”。

## 4. Phase 0：冻结当前基线

### 目标

先把已经花费大量算力得到的六组基线和 `116705` 变成可追溯数据集，防止后续重编译、覆盖或参数变更后无法解释差异。

### 任务清单

- [ ] 为六组算例记录 commit/源代码快照、`definitions.h`、`init.c`、`pluto.ini`、Makefile 和 Slurm 脚本；
- [x] `116705` 运行目录归档 executable、definitions、初始化源码、staged configs、runner 和 GPU telemetry；
- [x] 核对 `116705` 网格、物理参数、输出时间、文件数量/大小、两阶段完成状态和空 stderr；
- [ ] 记录 gPLUTO/PLUTO 版本、编译器、GPU、MPI/OpenACC 参数和可执行文件 SHA-256；
- [ ] 记录每个算例的网格、映射、边界、CFL、Riemann solver、重构、时间积分和输出 cadence；
- [ ] 记录实际采用的 pressure floor、fallback、`RECONSTRUCT_4VEL=NO` 等数值稳定性修改；
- [ ] 保存 Slurm job ID、运行时间、退出状态、最终 `dbl.out` 和 stderr 扫描结果；
- [ ] 为每个输出生成文件大小与 checksum 清单；
- [ ] 把大体积原始数据保留在 PDC，只把 manifest、小型派生表格和图同步到本仓库；
- [ ] 将当前六组统一标记为 `baseline_reduced_grid_v1`，不要覆盖原目录。

`116705` 已满足单次运行的基本追溯要求，但整个 campaign 的 Gate 0 尚未通过：还缺六组基线的统一 manifest、源码版本对照和 checksum 清单。

### 建议目录

```text
data/simulations/gpluto/
└─ baseline_reduced_grid_v1/
   ├─ campaign_manifest.yaml
   ├─ case_summary.csv
   ├─ checksums.txt
   └─ diagnostics/

src/simulation/gpluto/
├─ diagnostics/
├─ radiation/
└─ README.md
```

PDC 原始输出路径写入 manifest，但分析脚本通过参数或配置文件读取，不能把绝对路径写死在 Python 源码中。

### Gate 0

任意一幅图都能追溯到：算例配置、输出编号、物理时间、代码版本和绘图命令。未达到这一点，不开始覆盖式重跑。

## 5. Phase 1：用现有输出完成动力学定量复现

### 5.1 首先复现论文可比较诊断

- [ ] 重建 Hu et al. Figures 2、5、6、7、8、9 中与当前算例相对应的量；
- [ ] 对所有算例使用相同空间范围、单位、切片位置和色标；
- [ ] 输出纵向 `xz/yz` 切片和多个 `z` 位置的横向 `xy` 切片；
- [ ] 用 tracer 定义 jet material，避免只按密度阈值误判喷流边界；
- [ ] 测量 jet radius `R_j(z,t)`、recollimation nozzle 位置和相邻节点间距；
- [ ] 计算横截面平均径向速度、轴向 Lorentz 因子、热压和磁压；
- [ ] 绘制磁能、动能、内能随时间及 `z` 的变化；
- [ ] 生成 3D tracer/density 等值面和磁力线，检查真实螺旋位移而非切片假象。

### 5.2 对已确认的 kink 做模式定量

MHD3 已在 Hu et al. 第一篇文章的复现层级确认出现 kink。下面的模式诊断不再用于重新判断“有没有 kink”，而是用于测量其增长、传播、周期、相干性，并为后续 kink-耗散-QPO 因果链提供定量输入。对每个 `z,t` 横截面，至少计算以下量：

1. tracer 加权质心

   $$
   x_c = \frac{\int \rho C x\,dA}{\int \rho C\,dA},\qquad
   y_c = \frac{\int \rho C y\,dA}{\int \rho C\,dA},
   $$

   其中 `C` 是喷流 tracer。定义位移幅度

   $$
   D_1=\sqrt{x_c^2+y_c^2},\qquad \phi_1=\operatorname{atan2}(y_c,x_c).
   $$

2. 方位角 Fourier 模式

   $$
   A_m(z,t)=\frac{\left|\int q(r,\phi,z,t)e^{im\phi}r\,dr\,d\phi\right|}
   {\int |q(r,\phi,z,t)|r\,dr\,d\phi},\quad m=1,2,3,4,
   $$

   `q` 至少分别使用 tracer、密度、压力和轴向电流，确认结果不是单一变量的假象。

3. 模式传播与相干性

- [ ] 画 `A_1(z,t)` 时空图；
- [ ] unwrap `phi_1(z,t)`，测量相速度、转动方向和局部周期；
- [ ] 在 recollimation nozzle 上下游分别计算增长率和相干时间；
- [ ] 比较 `m=1` 与 `m=2-4`，判断是全局 kink 还是宽带湍动；
- [ ] 检查相邻 `z` 截面的相位连续性，验证三维螺旋结构。

4. 磁拓扑和电流诊断

- [ ] 计算 `J = curl(B)`、`|J|/|B|` 和电流集中区域；
- [ ] 跟踪磁 pitch、`B_phi/B_z`、磁压和磁张力；
- [ ] 比较电流峰值、`A_1`、磁能下降和热能上升的时间关系；
- [ ] 检查 `div(B)` 误差及其与模式增长是否相关。

### 5.3 区分四类不稳定性

| 现象 | 主要位置/特征 | 需要的诊断 | 不能依赖的单一证据 |
|---|---|---|---|
| current-driven kink | 电流承载磁化喷流内部，全局 `m=1` 螺旋 | `A_1`、磁力线、轴向电流、相位连续性 | 一张弯曲密度切片 |
| RTI | 加速/减速界面，指状混合 | 有效加速度、界面密度梯度、tracer 混合 | 外边界起伏 |
| KHI | 强速度剪切层，卷吸和小尺度涡旋 | 剪切层、涡量、模式谱 | 喷流变宽 |
| centrifugal instability | 弯曲流线或旋转流中的离心不稳定 | 流线曲率、角动量和径向力平衡 | 横向扰动本身 |

### Gate 1

Gate 1 分为两个证据层级：

- **识别层：已通过。** MHD3 已复现 Hu et al. 第一篇文章中的 kink，可以确认 kink 已经在该算例中出现；
- **定量层：待完成。** 为测量 kink 周期并支撑后续 QPO 论文，需要继续满足：

- `m=1` 在有限 `z` 区间内相对 `m=2-4` 明显增强；
- 相位沿 `z` 连续并表现为传播或旋转的螺旋；
- 结构存在于 tracer、磁场/电流和流体变量中，而不只是一张切片；
- HD 或轴对称对照中不存在相同的内部磁螺旋；
- 结果不随合理的 jet-mask、切片和插值方式消失。

六组基线的 21 帧已经足以支持论文复现层面的 kink 识别，但不足以可靠测量增长率、传播和周期；这些定量任务使用 `116705` 的高 cadence 窗口完成。

## 6. Phase 2：解除网格混杂并建立因果对照

### 6.1 不要立即把六组全部按最高分辨率重跑

先用最少算例回答最关键的数值问题：当前形态差异究竟来自物理参数，还是 uniform/mapped grid 和分辨率不同。

### 推荐重跑矩阵

| 优先级 | 新算例 | 改动 | 目的 | 状态 |
|---:|---|---|---|---|
| P0 | HD-gridmatch | 改为 MHD2/3 相同 mapped grid | 去掉 HD 与 MHD 的网格混杂 | 待运行 |
| P0 | MHD1-gridmatch | 改为 MHD2/3 相同 mapped grid | 去掉 MHD1 与 MHD2/3 的网格混杂 | 待运行 |
| P0 | MHD3-highres | `320 x 320 x 450`，核心 `48 cells/R_j` | 与 `300 x 300 x 336` 基线比较 kink、节点和能量诊断 | `116705` 已完成；定量比较待做 |
| P1 | MHD3-2D | 与关键 3D 算例相同入口和轴向网格 | 保留 recollimation、禁止非轴对称 kink | 待运行 |
| P1 | MHD3-pressure-matched | 令喷流与环境近压力平衡 | 检验 recollimation 是否是触发条件 | 待运行 |
| P1 | stable-pitch-control | 增大 pitch 或降低环向场占比 | 检验是否为 current-driven kink | 待运行 |

### 6.2 收敛标准

MHD3 现在已有两个分辨率层级：baseline 的核心横向/轴向分辨率约为 `39/5.6 cells/R_j`，`116705` 为 `48/7.5 cells/R_j`。下一步至少比较：

- 第一、第二 recollimation nozzle 的位置误差；
- `A_1` 峰值、增长率和主周期；
- tracer 混合层厚度；
- 磁能转化比例；
- shock/current-sheet 的位置和数量；
- 计算成本与存储量。

不要求所有像素结构一致，但关键结论在加密后不能反转。建议把“变化小于 10%-20%”作为初始工程标准，再根据实际数值噪声调整并在文中报告。

### Gate 2

- 匹配网格后，主要物理排序仍成立；
- MHD3 的 `m=1` 不由单一网格映射边界或低分辨率触发；
- 关键 nozzle 位置和模式尺度达到可接受收敛；
- 至少有一个“有 recollimation 无 kink”或“有磁场但 kink 弱”的物理对照。

若不通过：先修正网格、边界或数值方法，不进入辐射解释。

**当前状态：Gate 2 未通过。** 这不否定已经确认的 kink，而是表示其数值收敛程度、recollimation 触发因果和相对其他不稳定性的定量归因仍待加强。`116705` 已完成加密数据生成，但 HD/MHD1 的 grid-matched 控制和独立物理控制仍缺失。

## 7. Phase 3：高时间分辨率 kink pilot

### 7.1 已完成的首轮 high-cadence 数据集

MHD3 job `116705` 已经从 `t=0` 独立运行到 `t=400 R_j/c`：

- `t=0-300`：每 `10 R_j/c` 输出一个完整 3D `dbl`；
- `t=300-400`：从 output `#30` 接续，每 `1 R_j/c` 输出；
- 高 cadence 窗口包含 `t=300` 和 `t=400` 在内的 101 帧；
- 最终 output 为 `#130`，总步数 111,986；
- 运行正常结束，当前不需要重新从 `t=0` 生成同一数据集。

这一结果完成了 Phase 3 的数据生成。kink 已由论文复现确认；尚未完成的是 kink 周期、相干性、耗散关联和 QPO 可行性 pilot，这取决于对这 101 帧的模式分析。

### 7.2 立即分析与续跑判据

- [ ] 先从 `t=300-400` 提取 `A_1-4(z,t)`、质心相位、nozzle 位置和能量代理；
- [ ] 测量候选周期 `P_sim`、相干时间和窗口内有效循环数 `N_cycle=100/P_sim`；
- [ ] 若 `N_cycle >= 5` 且相位连续，先完成 pilot report，不立即续跑；
- [ ] 若存在候选模式但 `N_cycle < 5`，从 `data.0130.dbl` 的 `t=400` checkpoint 续跑，终点由 `t_end >= 400 + 5 P_sim` 决定；
- [ ] 若自动模式分析没有恢复出与已确认 kink 一致的 `m=1`，先检查模式定义、空间 mask、相位展开和分辨率差异，再决定是否需要更长窗口；
- [ ] 只有 pilot 证明需要更长基线后，才考虑向 `t ~ 1100` 延伸。

当前每个完整 `dbl` 快照为 `3,317,760,000` bytes。若从 `t=400` 到 `1100` 仍每 1 单位写完整双精度数据，将额外产生约 `2.3 TB`，不是合理默认方案。续跑前应改成：稀疏 `dbl` 用于 restart，密集 `flt` 或在线降维量用于时序诊断，并实测读取/写出开销。

存储仍可用下式估算：

$$
S_{campaign}=N_{frame}\times S_{one\ frame}\times N_{case}\times 1.2,
$$

最后的 `1.2` 给日志、checkpoint 和派生数据留余量。`116705` 的实测目录大小约 `405 GiB`，后续预算应以这个实测值而不是理论小文件估算为基准。

### 7.3 pilot 必须包含的时序量

- `A_m(z,t)`，`m=1-4`；
- 质心位移与相位；
- recollimation nozzle 位置随时间；
- 总磁能、内能、动能；
- jet-mask 内 `J^2` 或电流集中体积分；
- compression/shock proxy，如 `max(-div(v),0)`；
- tracer 混合率；
- 不同 `z` 区间的互相关和传播时延。

### 7.4 时间序列质量检查

- [ ] 确认输出 cadence 至少比候选周期细 10 倍；
- [ ] 去掉初始建立阶段，只分析统计性质相对稳定的时间段；
- [ ] 检查周期是否随 `z` 漂移；
- [ ] 用自相关、PSD、CWT/WWZ 同时描述，不只报告单一算法峰；
- [ ] 报告周期、品质因子 `Q=nu/delta_nu`、相干周期数和振幅；
- [ ] 与 2D、HD、pressure-matched 或 stable-pitch 控制比较。

### Gate 3

满足以下条件才值得投入完整辐射计算：

- 关键算例有至少 5 个可追踪的 `m=1` 周期或准周期循环；
- 模式在不同 `z` 截面间具有可解释传播关系；
- 模式与磁能转换/电流集中存在稳定相关或时延；
- 对照算例中的信号显著更弱、寿命更短或不存在；
- 周期和增长率对输出 cadence、窗口和分析方法不敏感。

若不通过：不要强做 QPO。先扩展运行时间，或把研究问题改为“recollimation 对 kink/RTI 竞争和间歇耗散的影响”。

**当前状态：Gate 3 未通过。** 已有足够 cadence 的首轮数据，但尚无 5 个相干周期、模式传播或模式-耗散关联的量化结果。

## 8. Phase 4：先做明确标注的伽马射线 proxy

### 目的

完整 SSC 很昂贵。先用 proxy 回答：哪些区域、视角和时间段最可能保留动力学周期，从而筛选值得做粒子输运的算例。

### 8.1 可使用的局地代理

- 电流集中：`q_J = J^2` 或归一化的 `J^2/B^2`；
- 压缩/激波：`q_comp = max(-div(v),0)`；
- 磁能变化：局部或分区的磁能下降率；
- 混合/剪切：tracer 梯度、涡量和剪切层强度；
- 简化同步辐射：$j_{syn}\propto n_{nt}B_{\perp}^{1+\alpha}$，其中 `n_nt` 必须说明来自何种注入假设。

注意：理想 RMHD 中 `J^2` 不是已知电阻率下的真实耗散率，`J dot E` 也包含场与流体的可逆能量交换。它们只能叫 current-sheet/dissipation proxy，不能直接称为粒子加热率。

### 8.2 从模拟到观测者时间

每个体元的到达时间应按

$$
t_{arr}=(1+z_{cos})\left(t-\frac{\boldsymbol{n}\cdot\boldsymbol{r}}{c}\right)
$$

累积，而不是只把同一模拟时刻的所有体元直接相加。发射率还要使用局部速度计算 Doppler 因子

$$
\delta=\frac{1}{\Gamma(1-\beta\cos\theta_{local})}.
$$

扫描少量预先规定的 viewing angles，并保存无 slow-light 与含 slow-light 的差异。

### 8.3 proxy 产物

- [ ] 沿喷流的时空发射图；
- [ ] 多个视角的全区和分区 proxy 光变；
- [ ] proxy 与 `A_1`、`J^2`、磁能的互相关和时延；
- [ ] 不同积分孔径下的周期稀释程度；
- [ ] 2D/3D、recollimation/no-recollimation、kink/stable 对照；
- [ ] observer-frame 周期随 `R_j`、Doppler 因子和视角的缩放图。

### Gate 4

只有当 proxy 周期在合理视角和体积积分后仍存在，并与 `m=1` 有可解释联系时，才把该算例升级到昂贵的非热电子与 SSC。若 proxy 已完全被光行时抹平，应先理解原因，而不是通过挑视角恢复峰值。

## 9. Phase 5：非热电子、同步辐射和 SSC

### 9.1 推荐技术路线

采用分阶段实现：

1. **粒子输运验证版：** 在 RMHD 输出上注入 Lagrangian macro-particles，演化电子谱，先计算 synchrotron；
2. **局地 SSC 近似版：** 使用局部/分区 synchrotron photon field，加入 Thomson 到 Klein-Nishina 过渡；
3. **慢光 SSC 正式版：** 在观测者到达时间面上积分，并改进非局地 synchrotron photon field；
4. **可选在线耦合：** 只有离线方法无法满足精度时，再考虑运行时粒子反馈或更复杂辐射模块。

PLUTO 的粒子框架和 Vaidya et al. (2018) 可作为起点，但必须先做小型标准测试，确认与当前 gPLUTO/OpenACC 构建兼容。

### 9.2 电子谱方程

需要求解或等效离散化：

$$
\frac{\partial N(\gamma,t)}{\partial t}
=\frac{\partial}{\partial\gamma}\left[\dot\gamma_{loss}N\right]
-\frac{N}{t_{esc}}+Q(\gamma,t),
$$

其中至少包括：

- synchrotron cooling；
- SSC cooling，含 Klein-Nishina 修正；
- adiabatic cooling/heating；
- 与 shock/current-sheet proxy 关联的注入 `Q`；
- 可控的 escape 时间；
- 电子谱上下限、斜率和注入效率。

所有自由参数必须写入配置和参数表，不允许只存在于 notebook 单元格中。

### 9.3 Mrk 421 benchmark 的顺序

1. 固定红移 `z_cos ~ 0.031`，从文献给出黑洞质量、视角、Doppler 因子和平均 SED 范围；
2. 给无量纲模拟选择物理尺度 `R_j` 和磁场归一化；
3. 先拟合或合理覆盖平均 synchrotron+SSC SED；
4. 再冻结辐射参数，计算时间变化；
5. 最后才比较候选 QPO 时标，不能先按目标周期反调 `R_j` 或 `delta`；
6. TeV 通量加入 EBL attenuation，并明确采用的 EBL 模型。

### 9.4 验证测试

- [ ] 单电子 synchrotron cooling 与解析解一致；
- [ ] 均匀磁场、固定幂律电子谱的 synchrotron spectrum 与解析斜率一致；
- [ ] 一区 SSC 与公开 one-zone code 或文献 benchmark 一致；
- [ ] Thomson/KN 过渡连续；
- [ ] 粒子数和能量收支可解释；
- [ ] 时间步减半、能量网格加密后光变和 SED 收敛；
- [ ] 静态发射体的 slow-light 结果退化到 fast-light；
- [ ] 关闭 kink/recollimation 时不凭空产生周期。

### Gate 5

- 平均 SED 在预先规定容差内覆盖 Mrk 421 的 HBL 双峰结构；
- 电子冷却和 SSC 数值测试通过；
- 辐射变化能追溯到流体区域和电子谱变化；
- 周期不是注入 cadence、输出 cadence、边界或插值产生的；
- 控制算例和多个视角结果完整保留。

## 10. Phase 6：合成观测和 QPO 显著性

### 10.1 需要生成的波段

- X-ray：例如 `0.3-10 keV`，追踪高能同步辐射电子；
- Fermi-LAT：`0.1-300 GeV`，可再按能段细分；
- IACT/WCDA：`>100 GeV` 或与实际能区一致的 TeV 光变；
- 可选 optical/radio：用于检查低能电子和平滑效应，不作为主结果。

### 10.2 两级光变

1. **intrinsic synthetic light curve：** 高 cadence、无缺口、仅包含物理模型；
2. **observed synthetic light curve：** 应用真实曝光、采样间隔、缺口、flux uncertainty、TS selection 和灵敏度。

只有第二级可以回答“Fermi/WCDA 是否能探测”，第一级用于理解机制。

### 10.3 统计分析预注册

在查看最终峰值前固定：

- 时间区间和稳态截取规则；
- 搜索周期范围；
- CWT/WWZ/PSD 参数；
- 候选峰定义；
- red-noise/null model；
- surrogate 数量；
- local/global significance 规则；
- source、band、window、method 和 frequency trials 的处理方式。

使用本仓库现有 CWT、WWZ、PSD 和 Emmanoulopoulos surrogate 流程，但要为合成数据增加单元测试和端到端配置。

### 10.4 必须报告的统计量

- 局部 FAP 与全局 FAP；
- period uncertainty 和 peak width；
- `Q` 值、持续周期数、占空比；
- 不同波段的 coherence、phase lag 和相关系数；
- 不同观测 cadence 下的 recovery rate；
- 多重检验修正后的 detection efficiency；
- 对照算例的 false-positive rate。

### 10.5 observer-frame 缩放

无量纲模拟时间的物理标度近似由 `R_j/c` 给出，但最终观测周期必须从到达时间序列中测量。可用

$$
P_{obs}\sim \frac{1+z_{cos}}{\delta}P'\frac{R_j}{c}
$$

作为数量级检查，不能替代 slow-light 计算。论文应展示 `R_j-delta-theta` 参数下的 period/detectability map，而不是只给一个调到 300 天的数值。

### Gate 6

最终“可探测 QPO”至少要求：

- 在事先定义的统计流程下达到报告阈值；
- 全局而非只有局部显著；
- 至少持续若干周期且在时频图中局域一致；
- 控制算例的检出率明显较低；
- 在小幅改变采样、噪声和窗口后结论不反转；
- 动力学模式、耗散和辐射峰之间有因果顺序。

## 11. 最小实验矩阵与扩展参数扫描

### 11.1 最小可发表因果矩阵

| 类别 | 3D | 过压/recollimation | 低 pitch/toroidal | 预期作用 |
|---|---:|---:|---:|---|
| Key MHD3 | 是 | 是 | 是 | recollimation + kink + radiation 主算例 |
| MHD3-2D | 否 | 是 | 是 | 有 recollimation、无非轴对称 kink |
| pressure-matched MHD3 | 是 | 弱/无 | 是 | 检验 recollimation 触发作用 |
| stable-pitch MHD | 是 | 是 | 否 | 检验 current-driven 条件 |
| HD grid-matched | 是 | 是 | 无磁场 | RTI/KHI 和纯流体 recollimation 对照 |

这五类比盲目扫描几十组参数更优先，因为它们直接对应因果链。

### 11.2 通过 pilot 后再扫描

按下列顺序，每次先只改变一个维度：

1. 磁 pitch 或 `B_phi/B_z`；
2. 磁化度 `sigma`；
3. 过压比 `p_j/p_a`；
4. jet Lorentz factor 和 relativistic Mach number；
5. 剪切层厚度；
6. viewing angle 和物理尺度；
7. 非热注入效率、电子谱斜率、escape/cooling 参数。

每个动力学参数点不必立即做完整 SSC。先用 Gate 3 和 Gate 4 筛选，只让少数代表点进入正式辐射阶段。

## 12. 并行学习路线

学习应与正在做的算例绑定。每个主题都要有一个可交付练习，而不是只读书。

| 时间 | 主题 | 必须掌握 | 实践任务 | 完成标准 |
|---|---|---|---|---|
| Phase 0-1 | SRHD/RMHD 方程 | 守恒变量、原始量、EOS、Lorentz 变换、磁化度 | 手写当前算例的无量纲控制方程和入口状态表 | 能解释每个 `definitions/init/ini` 参数的物理意义 |
| Phase 1 | recollimation shock | 过压膨胀、斜激波、Mach disk/nozzle、节点尺度 | 从 HD/MHD1-2D 测节点位置并做数量级估算 | 模拟位置与理论趋势方向一致 |
| Phase 1-3 | MHD instability | CDI kink、RTI、KHI、离心不稳定性的判据和模式 | 对同一横截面做 `m=1-4` 分解 | 不靠肉眼区分四类机制 |
| Phase 2 | 数值 RMHD | Riemann solver、PPM、CT/Eight-Waves、CFL、floor、收敛 | 完成一组网格/solver 敏感性测试 | 能说明数值选择对结论的影响 |
| Phase 3 | 时序和信号 | PSD、ACF、Q、CWT、WWZ、非平稳信号 | 对高 cadence `A_1` 做完整分析 | 能区分周期、准周期和红噪声峰 |
| Phase 4 | 相对论观测效应 | Doppler、aberration、light-travel-time | 实现运动发射 blob 的解析 benchmark | 数值到达时间和 boosting 与解析式一致 |
| Phase 5 | 非热辐射 | 电子谱、synchrotron、SSC、KN、冷却和 EBL | 复现 one-zone Mrk 421 SED | 峰频、谱斜率和 cooling time 可解释 |
| Phase 5 | 粒子输运 | kinetic equation、注入、escape、绝热项 | 单区 cooling/injection 测试 | 粒子/能量误差达到设定容差 |
| Phase 6 | QPO 统计 | red noise、surrogates、trials、local/global FAP | 对已知注入周期的模拟光变做 recovery test | 检出率和假阳性率经过校准 |
| Phase 7 | 科学写作 | claim-evidence 对应、方法可复现、限制条件 | 每完成一阶段写 2-4 页内部 note | 图、表和文字可直接进入论文 |

### 建议的学习节奏

- 每周约 60% 时间做可运行的模拟/分析；
- 25% 阅读与当前阻塞问题直接相关的论文或教材；
- 15% 整理公式、参数、图和实验日志；
- 每读一篇核心论文，输出“一页笔记”：问题、方程、参数、诊断、结论、可复现点、与你课题的差异；
- 不以“读完 RMHD 教科书”为启动条件，先围绕当前算例补齐知识。

## 13. 代码、数据和复现工作流

### 13.1 代码职责

- `src/simulation/`：模式分析、粒子输运、辐射和合成观测的可复用逻辑；
- `src/pipeline/`：每个阶段的可运行入口；
- `src/utils/project_paths.py`：本地项目路径唯一来源；
- `notebooks/`：只做展示、交互检查和小规模探索；
- `data/simulations/`：manifest、低体积派生数组和汇总表；
- `reports/`：阶段报告、最终图和稿件；
- `work/`：Slurm 脚本、运行交接和当日实验记录。

### 13.2 建议入口

```text
src/pipeline/
├─ gpluto_baseline_diagnostics.py
├─ gpluto_mode_analysis.py
├─ gpluto_proxy_lightcurves.py
├─ gpluto_nonthermal_radiation.py
└─ synthetic_gamma_qpo_significance.py
```

名称可按实际实现调整，但命令行必须接受 campaign config、case、input/output root 和时间范围。禁止为每个算例复制一份只改路径的 `plot.py`。

### 13.3 每个 campaign 的必备文件

- `campaign.yaml`：物理参数、数值参数和分析计划；
- `cases.csv`：case ID 和控制变量；
- `run_manifest.json`：代码版本、机器、job ID、起止时间、输出列表；
- `diagnostics_summary.csv`：关键定量结果；
- `README.md`：运行与复现命令；
- `figures/`：由 pipeline 自动生成，不手工改图；
- checksums：用于确认 PDC 与本地派生产品一致。

### 13.4 质量控制

- 小网格 synthetic fixture 用于 CI/本地冒烟测试；
- 每个诊断函数至少有解析场或人工构造场测试；
- 图中固定单位、坐标方向和色标策略；
- 所有统计随机种子和 surrogate 参数入配置；
- 大型原始 3D 输出不提交 Git，只提交 manifest、表格、图和必要的小样本；
- 每次完成一个阶段，在 `work/log.md` 记录运行、结果、失败和下一步。

## 14. 论文成文路线

### 14.1 论文定位

建议标题方向：

> **Gamma-ray quasi-periodic variability driven by recollimation-triggered kink instability in relativistic blazar jets**

创新点不要写成“kink 可以产生 QPO”，已有工作已经讨论过 kink 引起的周期性同步辐射/偏振。更稳妥的贡献是：

1. 建立 recollimation 到 `m=1` kink 的受控因果链；
2. 从 RMHD 模式、磁能转换、非热电子一直追踪到 SSC 伽马射线；
3. 加入 slow-light、Doppler、KN、EBL 和真实观测窗口；
4. 用红噪声和 trials 校正检验瞬态 QPO 的可探测性；
5. 给出 HBL/Mrk 421 benchmark 下的参数范围，而非事后匹配单一周期。

### 14.2 预期论文结构

1. **Introduction**：blazar QPO、竞争机制、kink/recollimation 的现状与伽马射线缺口；
2. **RMHD setup**：方程、入口、磁场、环境、网格、边界、对照矩阵；
3. **Dynamical diagnostics**：recollimation、模式增长、RTI/KHI 区分、收敛；
4. **Particle and radiation model**：电子注入、cooling、synchrotron、SSC、observer effects；
5. **Synthetic variability**：多波段光变、时延、视角和参数依赖；
6. **QPO significance**：PSD/CWT/WWZ、surrogates、global FAP、recovery rate；
7. **Mrk 421 benchmark**：SED、时间尺度和 Fermi/WCDA 可探测性；
8. **Discussion**：与其他 QPO 模型比较、局限、可证伪预测；
9. **Conclusions**：只总结通过对应 gate 的证据。

### 14.3 预期主图

1. 模拟设置和因果链；
2. 匹配网格下关键算例的 recollimation morphology；
3. `A_1(z,t)`、相位和 recollimation 位置；
4. 磁能到热能/非热粒子能量转移；
5. 平均 synchrotron+SSC SED；
6. intrinsic 多波段光变及 kink/耗散关联；
7. observed light curve 的 PSD/CWT/WWZ 和显著性；
8. pitch-磁化度-视角下的 QPO detectability map；
9. Mrk 421 benchmark 的 observer-frame 缩放和观测窗口恢复率。

### 14.4 写作 gate

- **内部报告 v1：** Phase 1 后，写动力学复现和当前局限；
- **方法稿骨架：** Phase 3 后，固定设置、诊断和对照章节；
- **结果稿 v1：** Phase 5 后，加入 SED 和物理光变；
- **完整稿：** Phase 6 后，加入全局显著性和参数图；
- **投稿前：** 由未参与代码编写的人按 README 从 manifest 重建至少一张主图。

## 15. 风险与备选路线

| 风险 | 早期信号 | 应对 | 可形成的替代科学结果 |
|---|---|---|---|
| MHD3 没有相干 kink | `m=1` 不增长或相位随机 | 延长时间、检查 pitch/边界/分辨率 | recollimation 下不稳定性竞争 |
| kink 有但无周期耗散 | `A_1` 与能量转换不相关 | 改进 current-sheet/shock 诊断，测试注入模型 | kink 造成间歇 flare 而非 QPO |
| proxy 有周期、SSC 无周期 | slow-light/cooling 后峰消失 | 扫描源尺寸、视角、cooling regime | QPO 可见性的物理抑制条件 |
| 需要不可承受的 3D 分辨率 | 收敛慢、I/O 主导 | 高分辨率只跑关键窗口，在线降维 | 分辨率依赖与数值限制研究 |
| Mrk 421 周期不稳健 | 观测全局 FAP 不显著 | 把它作为 benchmark，不声称一一对应 | 面向一般 HBL 的机制研究 |
| 辐射自由参数过多 | 多组参数同样拟合 SED | 固定文献先验，做灵敏度和退化分析 | 可证伪的参数约束图 |

## 16. 接下来四周的具体执行清单（2026-07-28 起）

### Week 1：接管和冻结 `116705`

- [x] 完成 `320 x 320 x 450` full-grid smoke 和正式生产运行；
- [x] 确认 `t=0-400`、131 帧、空 stderr、3 GPU 和 staged cadence；
- [ ] 将 `116705` 加入 campaign manifest，并保存关键源码/配置 checksum；
- [ ] 将 405 GiB 运行目录设为不可覆盖的只读基线或建立受控备份策略；
- [ ] 验证 Python reader 能以分块/切片方式读取单个 3.3 GB snapshot；
- [ ] 固定 jet mask、`z` 采样、模式定义和输出表 schema。

**交付：** `MHD3-highres-highcadence-116705` manifest、完整性报告和 reader smoke test。

### Week 2：优先分析 `t=300-400` 的 101 帧

- [ ] 计算 tracer centroid、`A_m(z,t)`，`m=1-4`；
- [ ] unwrap `m=1` phase，测传播速度、局部周期和相干时间；
- [ ] 量化 recollimation nozzle 位置及其随时间的变化；
- [ ] 计算磁能、内能、动能、电流集中和 compression proxy；
- [ ] 做 `A_1` 与 nozzle/energy proxy 的互相关和时延；
- [ ] 输出高 cadence kink diagnosis report。

**交付：** kink 的定量模式报告、Gate 3 初步判定、候选 `P_sim` 和 `N_cycle`。

### Week 3：完成两个 MHD3 分辨率层级比较

- [ ] 从 `116695` runtime log、备份 definitions 和构建记录追溯编译级设置，列出仍无法确认的差异；
- [ ] 在共同时间 `t=300,320,...,400` 比较 baseline `116695` 与精细算例 `116705`；
- [ ] 比较 nozzle 位置、jet radius、tracer mixing、`A_m` 和能量；
- [ ] 记录两种 grid 下结论是否同向，以及差异是否低于预设容差；
- [ ] 补做统一色标的 `xz/yz/xy` 和 3D 磁结构图；
- [ ] 明确哪些差异来自分辨率，哪些仍可能来自随机非轴对称扰动。

**交付：** MHD3 resolution note；不能仅凭视觉更细腻就宣布收敛。

### Week 4：按分析结果决定下一批计算

- [ ] 若已有至少 5 个相干周期，冻结 pilot 并进入 proxy 设计；
- [ ] 若周期存在但窗口不足，从 `t=400` 续跑到由 `P_sim` 决定的终点；
- [ ] 续跑前把稀疏 restart 与密集分析输出分开，避免继续使用 `dbl every 1`；
- [ ] 准备 HD-gridmatch、MHD1-gridmatch 以及至少一个 MHD3 物理控制；
- [ ] 将分析配置在查看最终 PSD/CWT/WWZ 峰值前冻结。

**交付：** 续跑或停止的书面判据、matched-grid/control jobs、预注册分析 YAML。

## 17. 最终完成标准

当以下产物全部存在时，可以认为这条研究链完整：

- [x] MHD3 复现 Hu et al. 第一篇文章，并在论文复现层级确认 kink；
- [ ] 六组基线和新增控制算例均可追溯、可重跑；
- [ ] 用模式、磁拓扑和对照算例量化 recollimation-triggered `m=1` kink 的增长、传播和因果归属；
- [ ] 关键结果通过基本网格/时间收敛；
- [ ] kink 与磁能转换、粒子注入之间有量化时空联系；
- [ ] 有经过验证的 synchrotron+SSC 和非热电子输运；
- [ ] 有含 slow-light、Doppler、KN 和 EBL 的多波段光变；
- [ ] 有 intrinsic 与 observed 两级 QPO 检验；
- [ ] 报告 local/global FAP、trials 和 recovery rate；
- [ ] 给出参数空间内“可见、被抹平、不产生”的区域；
- [ ] Mrk 421 作为 benchmark 的 SED、尺度和 cadence 比较不依赖事后调周期；
- [ ] 主文、补充材料、配置、代码、派生数据和复现 README 完整。

最终最有价值的结果不是一张“像 QPO”的图，而是一条有控制实验支持的结论：

> recollimation-kink 机制在何种磁结构、喷流尺度、视角和冷却条件下，能够或不能够在 HBL 的伽马射线中产生可探测的瞬态 QPO。

## 18. 起始参考文献

- Hu, Mizuno & Fromm, recollimation 与 relativistic magnetized jet instability，[arXiv:2411.17389](https://arxiv.org/abs/2411.17389)
- Dong, Zhang & Giannios (2020), kink 驱动的 blazar 辐射与偏振变化，[arXiv:2003.07765](https://arxiv.org/abs/2003.07765)
- Hu et al. (2025), toroidal-dominated MHD3 设置下的辐射时变研究，[arXiv:2511.03140](https://arxiv.org/abs/2511.03140)
- Kadowaki et al. (2021), Mrk 421 kink/reconnection 与功率谱讨论，[arXiv:2011.03634](https://arxiv.org/abs/2011.03634)
- Peñil et al. (2025), blazar QPO/喷流 kink 相关观测研究，[arXiv:2504.10308](https://arxiv.org/abs/2504.10308)
- Jorstad et al. (2022), blazar 喷流中的偏振和磁结构观测，[Nature](https://doi.org/10.1038/s41586-022-05038-9)
- Vaidya et al. (2018), PLUTO 非热粒子框架，ApJ 865, 144，ADS bibcode `2018ApJ...865..144V`

这些文献是起点，不是最终文献表。进入每个 Phase 前，应针对该阶段补充方法论文和最近引用链。
