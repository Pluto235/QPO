# WCDA 周尺度光子计数 → Flux 的 forward folding 流程说明

## Context（为什么要做这一步）

现在 `src/simulation/generate_wcda_weekly_sims.py` 里用的"流量"是
`flux_excess = sum(n_on − n_bkg) / tobs`（generate_wcda_weekly_sims.py:78-84），
本质是每秒的 excess 计数率，不是物理流量。它的问题：

- 没扣 **探测器有效面积**（Aeff(E, θ)，随天顶角/时段变化）。
- 没扣 **角分辨与 nhits–能量响应**（事件在 nhits bin 之间会扩散）。
- 没扣 **DAQ 活时间、死通道、水质**等随时间段（period）变化的因素。

所以师姐建议的做法是 **forward folding**：假设源的谱形（power-law），
把它和 **每个 period 的响应文件** 卷一遍，得到"如果流量是 N0、谱指数是 Γ，
WCDA 应该看到多少 excess counts 落在每个 nhits bin"；再用 Poisson likelihood
拟合 N0 让预言和观测一致。`iPeriod_1Days.h` 就是告诉你"这一天用哪一个 period 的响应"。

最终产出：一条**物理单位**的 WCDA 周光变（dN/dE @ E0，单位 cm⁻²·s⁻¹·TeV⁻¹ 或
积分流量 cm⁻²·s⁻¹），替换掉 QPO 分析里现在用的纯计数率，让后续的 CWT/WWZ/
Emmanoulopoulos 模拟都跑在物理流量上。

本文档**只讲流程**，不动代码；具体实现等在 IHEP 上跑通 forward folding
后再决定怎么落到 `src/`。

---

## 关键概念拆解

### 1. `iPeriod_1Days.h` 是什么

它就是一张 1565 行的查表：

```c
dura_period[i][0] = 第 i 天的全局日序号（从 1 开始）
dura_period[i][1] = 这一天所属的 detector period 编号（T01..T68）
```

总共 1565 天 → 68 个稳定运行段。每个 period 内，WCDA 的水质、坏管、阈值、
DAQ live time 等基本不变，所以**响应文件按 period 划分**，而不是按天。
day 1..17 是 T01；day 18..35 是 T02；…；尾部很长一段都落在 T68（说明那段
detector 状态没怎么变过）。

实现层面就是一个 `dict[int → int]`。`.h` 是 C++ 头，给 ROOT 脚本用；
你在 Python 端只需要把 1565 对 (day, period) 读成 numpy 或 DataFrame。

### 2. 响应库目录

`/home/lhaaso/hushicong/Standard_file_lib/results/Response/Cod/Factor_1.04/`

按 period 组织（典型命名 `T01.root` / `T01/` …），每个文件里通常包含：

- `Aeff(E, nhits, δ_band, period)`：考虑了天顶角积分、PSF 圈出半径、
  delta_θ 角分辨（CSV 头里 `delta : [0.89, 0.662, ...]` 这一行就是每个
  nhits bin 用的圆锥半径，单位 deg）。
- `Aeff × tobs`：把当 period 内源每天的天顶角轨迹和 DAQ live time
  都积分进去了。直接拿来乘谱模型就是预言 counts。

到时候要确认响应文件里给的是"per-second 的 Aeff"还是"已经乘了 tobs 的
exposure"，两者用法差一个 tobs 因子。

### 3. "Factor 1.04" 是什么

WCDA 标定的一个全局修正系数（Crab 校准给出的能标修正，量级 ~1.04）。
目录名带 1.04 表示这是已经乘进去的版本，直接用即可，不需要再额外乘。

### 4. Forward folding 的最小数学

每个 nhits bin k 的预言计数：

```
N_pred(k) = ∫ dE  Φ(E; N0, Γ) · R(E, k; period_j) · T_live(day, period_j)
          ≈ N0 · Σ_E  (E/E0)^(−Γ) · R(E, k; period_j) · ΔE · T_live
```

其中：

- `Φ(E; N0, Γ) = N0 · (E / E0)^(−Γ)`，差分流量，`E0` 一般取 3 TeV
  （WCDA 标准 pivot）。
- `R(E, k; period_j)` 是响应库给的、period_j 这段时间内 nhits=k 的
  effective area。
- `T_live` 通常已被吸收进响应；如果没吸收，就需要你按周累加 tobs。

观测端，nhits bin k 在某一天的 excess 是 `n_on(k) − n_bkg(k)`，
统计涨落由 `n_off / α`（α 是 on/off 比）给出。Likelihood 用 Poisson：

```
L = Π_k Poisson(n_on(k) | μ_on(k) = N_pred(k) + n_bkg(k))
```

拟合自由量：

- 标准做法是 **固定 Γ**（Mrk 421 的 WCDA 谱指数文献上 ~2.5–2.9，
  Crab-like ~2.6），只拟 `N0`。优点：稳定、误差小；缺点：耀发段
  谱形可能变硬，固定 Γ 会把谱变化"折算"到 N0 上。
- 进阶做法是同时拟 (N0, Γ)。每周事例较少时容易发散，一般只在亮
  段才放开 Γ。

**建议**：第一版先**固定 Γ = 2.6**（或用 LHAASO Mrk 421 文章里的全局值），
只拟 N0，得到一条干净的物理流量周光变。后面再做谱演化的版本。

### 5. 周尺度 vs 日尺度

你这次要做周。直接拿 `iPeriod_1Days.h` 不够，需要先做一张
`iPeriod_7Days` 等价表：把连续 7 天聚合成一个周 bin，每个周 bin 给出
它**覆盖的 (period, 天数)** 列表。

两种处理方式：

- **A. 同 period 的周（推荐绝大多数情况）**：1565 天里大多数 7 天滑窗
  完全落在同一个 period 内。直接用那个 period 的响应即可。
- **B. 跨 period 的周（少数）**：响应得按天数加权平均
  `R_week = (n1·R_p1 + n2·R_p2) / (n1+n2)`，或者更严谨地把当周分成
  两段，每段单独 forward-fold 后相加 N_pred。

实操上先简化为：**当周 ≥4 天落在某 period 就整周记到那个 period**，
跨段周直接 mask 掉或者用加权响应。

---

## 整体操作流程（在 IHEP 端做的步骤）

### Step 0：准备 period 映射表（一次性）

把 `iPeriod_1Days.h` 转成 Python 友好的表，再聚合到周：

```python
# 伪代码
day_to_period = parse_iperiod_h("iPeriod_1Days.h")   # dict[int → int]

# 周 bin 与你 CSV 里的周一一对应（mjd 间隔 7 天）
week_to_period = {}
for w, days_in_week in enumerate(weeks):    # weeks: list of 7-day groups
    periods = [day_to_period[d] for d in days_in_week]
    # 最常见的 period 作为整周的 period
    week_to_period[w] = Counter(periods).most_common(1)[0][0]
```

### Step 1：精读师姐发的 IHEP Jupyter 教程

链接：https://jupyter.ihep.ac.cn/113I0f1xR6S0TBjsgfJV5Q

> **这是一个 tutorial 文档，不是黑盒拟合器**。流程里第一件事就是把这份
> 教程从头到尾读完——它讲的是 WCDA 标准 forward-folding 拟合的方法、
> 响应文件结构、likelihood 写法、绘图与结果导出格式。读完才知道：
>
> - 响应文件具体的 ROOT 树/分支结构。
> - 它默认用的能量分 bin、pivot 能量 E0、谱模型形式。
> - Aeff 是否已经吸收 tobs（即上面第 2 节那个待确认的点）。
> - α (on/off) 是怎么算的、likelihood 是 Poisson 还是 Wilks/Li-Ma。
> - 拟合用 iminuit 还是 ROOT::TMinuit、输出 TS 怎么定义。
> - 失败/上限事件怎么标记。
>
> **不要**没读教程就直接抄代码——你需要它的概念解释来判断把流程从
> "一段时间一次拟合"改成"逐周循环"时哪些参数需要随周变化。

读完做笔记：把上面那些点的实际答案写下来，作为下一步实现的依据。

### Step 2：仿写一个"逐周循环"

照教程描述的最小工作单元，外面套一层周循环：

1. 输入：`data/processed/wcda_week/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv`
   （这是 ETO 端，IHEP 端的对应路径用师姐那套即可）。
2. 对每一行（每周）：
   - 算这一周的 MJD 中心 → 在 1565 天里对应的周序号 → 查 `week_to_period`
     得到 period j。
   - 从 `/home/lhaaso/hushicong/.../T0j.*` 加载响应。
   - 取 `n_on`、`n_bkg`、`tobs`（7 个 nhits bin 的数组都在 CSV 里）。
   - 调教程里的拟合函数，输入观测 vec + 响应 + 固定 Γ，
     输出 (N0, σ_N0, TS, 拟合 Q)。
3. 输出：一条 DataFrame，列至少有
   `mjd, period, N0, N0_err, TS, n_signal, fit_status`。

### Step 3：Sanity check（**不要跳**）

- **用 Crab 跑一次同样的流水线**做闭环验证：拟合得到的 N0 必须接近
  WCDA 标定值（~3×10⁻¹¹ TeV⁻¹·cm⁻²·s⁻¹ @ 3 TeV，量级别错就行）。
- 在 Mrk 421 上：
  - `N0` 和老的 `flux_excess = sum(n_on − n_bkg)/tobs` 应该高度相关
    （Pearson r > 0.95），但**斜率不为 1**（前者是物理 flux，后者是计数率）。
  - 平静段 N0 和文献 Mrk 421 平均流量量级一致。
  - TS 分布合理（亮周 TS 很大；暗周 TS 小但拟合不应该崩）。
  - 拟合失败（fit_status≠0）的周数 < 5%；失败的周多半是跨 period
    或者那周只有 0/1 hits bin 有 excess——按"暗周/上限"处理而不是
    强行给一个负 N0。

### Step 4：把产出物搬回 ETO，接入 QPO 流水线

从 IHEP 拉一份产物到本仓库
`data/processed/wcda_week/flux_forward_folded.csv`（或 .parquet）。
后续的 CWT / WWZ / Emmanoulopoulos 模拟把"flux"列从
`flux_excess` 换成新的 `N0`（或积分流量），其他逻辑都不动。
具体代码改动等这条流量光变跑出来再开第二个文档。

---

## ETO ↔ IHEP 通信

两个独立的通道并存（详见 `CLAUDE.md` 的 `IHEP Connectivity` 一节）：

**(a) ETO → IHEP 正向 SSH**（拉数据用）

- 账号 `liushijie@lxlogin.ihep.ac.cn`（实际解析到 `lxlogin008`）。
- IHEP 工作目录 `/home/lhaaso/liushijie`；AFS 家目录
  `/afs/ihep.ac.cn/users/l/liushijie`。
- 历史 rsync 命令（从 `CLAUDE.md`）：

  ```bash
  rsync -av --progress --partial --append-verify --info=progress2 \
    -e "ssh -o StrictHostKeyChecking=accept-new -o PubkeyAuthentication=no -o PreferredAuthentications=password" \
    liushijie@lxlogin.ihep.ac.cn:/eos/lhaaso/ai/wcda/raw/2022/0101/ \
    /mnt/mydisk/0101/
  ```

  forward folding 产物建议放到 ETO 的 `data/processed/wcda_week/` 下。

**(b) IHEP → ETO 反向隧道**（IHEP 端主动推数据时用）

- 脚本 `/home/server/bin/ihep_reverse_tunnel.sh`，tmux session 名
  `ihep_reverse_tunnel`，做的是 `ssh -R 10022:localhost:22
  liushijie@lxlogin002.ihep.ac.cn`，IHEP 端通过 `localhost:10022` 回 ETO。
- 子命令：`start | status | logs | stop | restart`。
- IHEP 端用法：

  ```bash
  ssh -p 10022 server@localhost
  rsync -avh path/on/ihep server@localhost:dest/ -e "ssh -p 10022"
  ```

实际工作时哪种方便就用哪种。Forward folding 的 `flux_forward_folded.csv`
体量很小（KB 级），任一通道都够。

---

## 关键文件与位置（参考）

- IHEP 响应库：`/home/lhaaso/hushicong/Standard_file_lib/results/Response/Cod/Factor_1.04/`
  （按 T01..T68 组织）
- IHEP forward-folding 教程：https://jupyter.ihep.ac.cn/113I0f1xR6S0TBjsgfJV5Q
  （tutorial，必须先读完）
- ETO 端 period 映射源文件：`iPeriod_1Days.h`（仓库根目录，1565 行）
- ETO 端 WCDA 周 CSV（参考列结构）：
  `data/processed/wcda_week/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv`
  - 列：`name, mjd, n_on[7], n_bkg[7], n_off[7], tobs`
  - 头部 metadata：`ra=166.114, dec=38.209, nhits=[0..6],
    delta=[0.89, 0.662, ...], max_zen=50°`
- ETO 端 WCDA 日 CSV：`data/LHAASO-WCDA_Mkn421_2025-03-29_2026-03-29_day.csv`
  （同结构，仅最近一年；做 daily forward folding 时用得到）
- 现状里"假 flux"产生处：`src/simulation/generate_wcda_weekly_sims.py:78-84`

---

## 你需要先回答自己（或问师姐）的几个问题

1. **响应文件里的 Aeff 是否已乘 tobs**？这决定 forward folding 公式
   要不要再乘一次每周 live time。
2. **Γ 用什么值**？固定 2.6 还是用她推荐的某个值。
3. **CSV 里的"week"边界**和 `iPeriod_1Days.h` 的"day 1 = 哪一天"
   能不能对齐？大概率第一天是 MJD 59281 (2021-03-05) 附近，但要拿
   `iPeriod_1Days.h` 的 day-0 定义和你周 CSV 第一周的起始 MJD 对一遍。
4. **跨 period 的周**怎么处理：mask 掉、用加权响应、还是拆两段
   分别 forward fold 再相加。
5. **是否需要逐周谱指数**：默认固定；如果师姐说她那边平时是 free Γ
   的，就按她那边来。

---

## 验证清单（怎么知道做对了）

- [ ] period 映射：从 `iPeriod_1Days.h` 解析出的 (day, period) 表行数 = 1565。
- [ ] 周映射：聚合后的周数 ≈ 1565 / 7 ≈ 223；跨 period 的周比例 < 20%。
- [ ] Crab 闭环：N0_crab 和 LHAASO 标准 Crab 流量量级一致。
- [ ] Mrk 421：N0 和老 flux_excess 的 Pearson r > 0.95。
- [ ] 失败率：fit_status 非 0 的周 < 5%。
- [ ] 单位一致：导出表头注明 `N0` 的单位与 pivot 能量 E0。
