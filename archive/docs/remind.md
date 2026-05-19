## 0. 先想清楚：你要“复现到什么程度？”

短期内很现实的目标可以分三层：

1. **最小复现版**

   * 选 1–3 个源（比如 PG 1553+113、PKS 1510−089、3C 454.3），
   * 用和 Ren 一样的数据选择 + 分箱 + CWT + MC 显著性，
   * 看能不能得到**类似的周期峰和显著性级别**。

2. **小样本复现版**

   * 把 35 个源都跑一遍，
   * 得到自己的“QPO候选列表”和他们 Table/图类似的结果。

3. **带自己改进的小升级版**

   * 在复现的基础上，适当用 Wu 2025 那套更严格的显著性检验或 GP 模型去 cross-check。

你可以先从“最小复现版”开始，成了以后再扩展。

---

## 1. 读论文 + 把流程拆成模块

Ren 的整套流程可以拆成 4 个模块（你基本都可以一一对应写成 Python 脚本 / notebook）：

1. **源列表 & 数据准备**

   * 从 4LAC-DR2 里选取 35 个最亮 AGN，满足 flux 和 TS 要求。
   * 时间范围：2008-08 到 2021-04（~13 年）。

2. **Fermi-LAT 数据分析，做光变曲线**

   * 使用 Fermitools + gtlike，在 0.1–300 GeV 上做全时段拟合，得到模型 xml。
   * 用 7 天和 30 天两种 binning 做光变；每个 bin 用 unbinned likelihood 拟合 flux。

3. **连续小波变换 (CWT) 周期分析**

   * 对每个 LC 做 Morlet CWT，得到时–频谱。
   * 计算 global wavelet spectrum（时间平均的功率谱），找峰。

4. **蒙特卡洛模拟 + 显著性**

   * 拟合每条 LC 的 PSD 为 bent power-law（平滑折线幂律）。
   * 用这个 PSD + 正态或对数正态 PDF 生成 1 万条模拟 LC；
   * 对每条模拟 LC 做同样的 CWT，得到在每个 period 上的 global spectrum 分布；
   * 用 χ² 拟合得到显著性曲线 & trial correction（用 Auchère+2016 的经验公式）。

你现在要做的，就是**把这四块变成你自己的 pipeline**。

---

## 2. 模块一：源 & 数据准备（建议先只选少数源）

### 2.1 选 1–3 个 test 源

直接从他们的源表里挑几个你感兴趣的 blazar：

* PG 1553+113
* PKS 1510−089
* 3C 454.3
* Mrk 421, Mrk 501（亮，很容易出结果）

### 2.2 搭 Fermitools & 基本脚本

环境建议：

* `fermitools` + `fermipy`（方便）
* Python：`numpy`, `astropy`, `scipy`, `matplotlib`, `pywavelets` 或 `wavelets` 包

你需要实现：

* 从 FSSC 下载 **Pass 8 SOURCE class** 数据（0.1–300 GeV, ROI ~ 10°–15°，这点和 Wu 类似，也和 Helena 的做法一致）。
* 做基本 cuts：`evclass=128`, `evtype=3`, `zmax=90`, GTIs。
* 用 make4FGLxml / fermipy 自动生成模型文件。

---

## 3. 模块二：光变曲线的重建

参考 Ren 的文字描述：他们先在**全时段**做一次拟合确定模型，再用这个模型去做 LC。

### 3.1 全时段拟合

* 用 `gtlike` 或 `fermipy` 对整段数据做一次 global fit：

  * 固定大部分远端源的谱形，只留下本源+附近亮源的归一化自由。

### 3.2 生成 7d 和 30d LC

* 采用 unbinned likelihood：每个 bin 拟合 flux，得到 `F`, `dF`, `TS`；
* 可以像他们一样，对 TS 过低的 bin 给 upper limit（或者直接舍去）。

**短期复现目标**：
画出跟他们类似的 7d/30d 光变图，检查是否和 LCR/文章里的大致相似。

---

## 4. 模块三：CWT 周期分析

Ren 这篇的核心是 **Continuous Wavelet Transform (CWT)**，不是 LSP。

### 4.1 选择小波和参数

* Morlet wavelet（标准选择）；
* 周期范围：比如 **50–2000 天**（覆盖他们关注的年级 QPO）；
* 步长可以 log-spaced。

### 4.2 实现要点

你要为每条 LC 计算：

* **Wavelet power spectrum** (W(t, P))：二维图，时间–周期；
* **Cone of influence (COI)**：边界效应区域要标出来（COI 内侧才可靠）；
* **Global wavelet spectrum**：对时间方向积分，得到功率 vs 周期（类似功率谱）。

然后：

* 找出 global spectrum 中的主峰（在 COI 外）；
* 读出对应的周期 & 功率。

---

## 5. 模块四：蒙特卡洛显著性（这部分最重要，也最容易和原文有差异）

Ren 的做法：

1. **对每条光变拟合 PSD**，采用 **smoothly bent power-law**（折线平滑幂律）。
2. 用这个 PSD + 光变的统计特性（PDF）生成 1 万条模拟 LC；
3. 每条模拟 LC 同样做 CWT → 得到它们在每个 period 的 global power 分布；
4. 用 χ² 拟合这些分布，得到每个 period 的显著性曲线；
5. 再按 Auchère+2016 提供的参数化公式做 **trial correction**（考虑源数 + 时–频 bins）。

### 5.1 你可以怎么实现（建议）

* 用 **Timmer & Koenig** 或 **Emmanoulopoulos** 方法生成红噪声时序；
* PSD 拟合可以用 `scipy.optimize` 拟合 (P(f)\sim (1+(f/f_b)^{\alpha})^{-1}) 或类似形式；
* 对每条模拟 LC 做 CWT，记录在每个周期上的最大 global power；
* 对每个周期的“最大功率分布”做经验 CDF，直接给出 95%、99%、99.9% 置信线，而不是一定要 χ² 拟合——这样实现上更简单。

**短期妥协版**：
一开始你也可以**只算 local 显著性**（先不做 trial correction），把 pipeline 跑通，再加全局 FAP。

---

## 6. 复现时可以专门对照的几块“关键结果”

你复现的时候，可以对照论文里这些“可量化”的结果来检查自己：

1. **光变大致形状、平均 flux、方差**：
   看你做出来的 LC 和文中图（比如 Fig. 1/2/3）是不是同一风格。

2. **global wavelet spectrum 主峰的位置（周期）**：
   对 PG 1553+113、PKS 1510−089 等，他们给了具体的周期（~年级），你可以看你的 peak 是不是落在类似位置。

3. **显著性等级**：
   文章里说他们对每条 LC 生成 10000 条模拟 LC，用 χ² 拟合出信噪比和 trial correction。你的结果不必完全一样，但应该同量级，比如 “某个峰 ~2–3σ，绝大多数 <2σ”。

4. **QPO candidate 列表**：
   他们有最终几个候选（比如 PKS 2247−131、PG 1553+113 等），你可以看在这些源上自己是不是也看到类似的显著峰。

---

## 7. 怎么在复现基础上“顺手加一点自己的东西”

你短期先以“尽量按照原文复现”为主，
但完全可以在局部加一点自己的 enhancement，让后面写小论文更顺畅，比如：

1. **对某几个源再加一遍 WWZ 分析**，和 CWT 对比（用你已经学得很熟的 WWZ）；
2. 对 1–2 个强候选源跑一次 **GP (SHO×2) 模型**（照 Wu 2025 的做法），看 PSD 里有没有对应 peak；
3. 检查光变的 **flux PDF 是不是 log-normal**（Shapiro–Wilk 检验，和 Wu 那样），这对你之后做 PSD+PDF MC 也有帮助。

---

## 8. 可以当作“工作计划”的简短版本

> 1. 搭建 Fermi-LAT 数据分析环境，基于 Fermitools/fermipy 重现 Ren et al. (2023) 中 1–3 个典型源的 7d/30d γ-ray 光变。
> 2. 使用 Morlet 连续小波变换，对这些光变重现文中的时–频谱和 global wavelet spectrum，验证主周期峰位置。
> 3. 实现基于 bent power-law PSD 拟合的蒙特卡洛模拟，生成 10³–10⁴ 条人工光变，重建每个周期的显著性曲线，并与原文给出的显著性等级对比。
> 4. 在复现基础上，尝试对少数候选源增加 WWZ/GP 分析，用更严格的显著性检验方法检查 QPO 稳健性，为后续自己的系统性工作（方法改进或大样本扩展）打基础。


## 11.7 尝试实现mkn421的光变曲线
1. ✅从官网下载FT1和FT2文件
Equatorial coordinates (degrees)	(166.11,38.21)
Time range (MET)	(239557417,428903014)
Time range (Gregorian)	(2008-08-04 15:43:36,2014-08-05 03:43:31)
Energy range (MeV)	(100,316227)
Search radius (degrees)	15

2. ✅写一个yaml配置文件
3. ✅做全时段拟合，查看tsmap，查看sed
4. ✅以30days为bin画出光变曲线
5. ✅小波分析
接下来进入显著性分析的步骤：
1. 蒙卡模拟
2. 

观测方面：QPO分析方法上：WWZ，GP，✅CWT ，显著性分析的地方是共通的
WWZ 在Ferimi上有人做了，CWT在Fermi上有人做了，GP的对4FGL的搜寻？？

理论方面：QPO的产生机理，需要查文献看一看，也许可以做一些理论的工作

## 2026.1.19
1. 对mkn421进行了周期性检验，在149d发现了接近3sigma 局域显著性的周期信号，这个信号和fermi的300d周期有点类似。
2. 目前代码在局域显著性方面计算应该有些问题，还没有办法完全复原helena的文章，算出的显著性有些偏低

## 2026.1.29
❓1. 把fermi mkn421对应WCDA观测时间的光变画出来
把模拟光变保存到本地

值得改善
❓https://arxiv.org/abs/2402.04352（TESS & Fermi）文中显著性方法使用Timmer & Koenig 1995，拟合PSD 符合simple / bending power law（保证二阶统计量一致），生成模拟光变。Emmanoulopoulos et al. 2013要控制PDF和PSD一致，是更一般的做法，但是在之前的方法里貌似缺少了拟合simple /bending power那一项；在用 simple / bending power law 拟合观测 PSD 之后，把该拟合结果当作“母体功率谱”，并在这个母体分布上随机抽样（随机相位、随机幅度），生成多条统计上服从该 PSD 的模拟光变。
❓在做post trail的时候，除了拟合chi square或者百分位数，有没有更好的方法
❓GP方法，按照文章的结果（开源代码）有没有更进一步可以操作空间？