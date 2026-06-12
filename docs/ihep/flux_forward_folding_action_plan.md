# WCDA Weekly Mrk 421 Photon Counts to Flux Action Plan

本文档记录把 WCDA weekly Mrk 421 光变从 photon counts / excess rate 转成
physical flux 所需的操作、当前已确认事实，以及仍需再次确认的问题。

## Current Facts

- 当前工作环境在 IHEP login node 上；大计算不要直接跑在 login node。
- `myrootenv` 可用于分析脚本，已确认包含 `pandas`、`numpy` 和 PyROOT。
- HTCondor 可用；当前 shell 里没有 `hep_sub`，批量任务优先使用原生
  `condor_submit -name scheduler@...`。
- Mrk 421 weekly 输入文件已存在：
  `results/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv`。
- weekly CSV 共 264 周，每周包含 7 个 nhits bin 的
  `n_on`、`n_bkg`、`n_off` 和 `tobs`。
- 旧的 `iPeriod_1Days.h` 只覆盖 1565 天、period `1..68`，不够覆盖完整
  weekly CSV。
- 更新的 period 配置可读：
  `/home/lhaaso/tangruiyi/analysis/from_yaozhiguo_2/Cog/conf/mcperiods.rc`。
- `mcperiods.rc` 覆盖 `2021-03-08` 到 `2025-11-05`，period `1..91`。
- 生成 `mcperiods.rc` 的脚本
  `/afs/ihep.ac.cn/users/w/wcdarec/wcda/masks/masks/src/mkperiods.py`
  当前无权限读取；检查到 `/afs/ihep.ac.cn/users/w/wcdarec` 和其下
  `wcda` 目录权限为 `drwx------ nobody nobody`，进入
  `.../masks/masks/src` 会报 `Permission denied`。
- 可读副本中，`from_yaozhiguo_2/Cog/conf/mcperiods.rc` 目前最新，覆盖到
  `2025-11-05`；`from_yaozhiguo_3/cod/conf/mcperiods.rc` 反而更旧，只覆盖到
  `2024-02-10`。
- Factor 1.04 响应库路径：
  `/home/lhaaso/hushicong/Standard_file_lib/results/Response/Cod/Factor_1.04/`。
- 当前响应库已确认有 `T001..T083/Response.root`，缺 `T084..T091`。
- 师姐原话中的 `iPeriod_1Day(s)` 指的是“每天属于哪个 detector period”的
  查表；仓库里的 `docs/iPeriod_1Days.h` 是旧版 C++ 表，`Ndura=1565`、
  period 只到 `T068`。当前 weekly CSV 到 `2026-03-29`，因此第一版衔接
  使用更完整的 `mcperiods.rc` 来做同一件事。
- 师姐已确认：`hresp_k` 就是效率。`hmap` 是大气之上的原始伽马投点事例数，
  `Left` 是最终能通过大气、触发探测器并重建成功的事例数。
- 第一版固定谱指数 `Gamma = 2.6`。
- Crab weekly CSV 暂时不做，第一版先完成 Mrk 421 流量光变。

## What `hresp_k` Means

`hresp_k` 是 WCDA 响应文件里的 detector response / detection efficiency
matrix，不是观测数据，也不是某一周的 counts。师姐确认这个量就是效率：
它描述大气之上的原始伽马中，有多少最终能通过大气、触发探测器并重建成功，
且落入对应 nhits bin 和 PSF 选择。

位置示例：

```text
/home/lhaaso/hushicong/Standard_file_lib/results/Response/Cod/Factor_1.04/T001/Response.root
  Resp_0/hresp_0
  Resp_1/hresp_1
  ...
  Resp_6/hresp_6
```

其中 `k = 0..6` 对应 weekly CSV 里的 7 个 nhits bin。

从标准代码看，`hresp_k` 的生成逻辑是：

```text
hresp_k(E, zen) = Left_k(E, zen) / hmap(E, zen)
```

含义：

- `hmap(E, zen)`：MC 在大气之上投进去的原始伽马事例数。
- `Left_k(E, zen)`：通过大气、触发探测器、重建成功，并经过 nhits bin 与
  PSF 圈选择后留在第 `k` 个 bin 的事例数。
- 因此 `hresp_k` 是从原始伽马到探测器可见重建信号的效率。

实际求 flux 时不要逐 bin 简单做 `observed_counts / hresp_k`。正确方向是
forward folding：先假设原始源谱 `Phi(E; N0, Gamma)`，通过 `hresp_k` 预测
探测器应该看到的 counts，再调节 `N0` 让预测 counts 匹配观测 counts。

标准拟合代码中的核心结构是：

```text
N_pred[k] =
  Tobs * S0 *
  sum_E sum_zen [
    integral_E Phi(E; N0, Gamma)
    * cos(zen)
    * hresp_k(E, zen, period)
    * DisZen(zen)
  ]
```

当前理解：`hresp_k` 是效率，不是 exposure，因此本身不包含本周 `tobs`。
`Tobs` 应在拟合阶段另外乘。

## Required Inputs

- Mrk 421 weekly counts CSV：
  `results/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv`
- Period 配置（当前首选）：
  `/home/lhaaso/tangruiyi/analysis/from_yaozhiguo_2/Cog/conf/mcperiods.rc`
- 旧版日到 period 查表（可作为概念参考或早期数据交叉检查）：
  `docs/iPeriod_1Days.h`
- 响应库：
  `/home/lhaaso/hushicong/Standard_file_lib/results/Response/Cod/Factor_1.04/`
- 固定谱参数：
  `Gamma = 2.6`，pivot energy 暂按 WCDA 常用 `E0 = 3 TeV`
- 待确认常数：
  `S0`

## Implementation Checklist

1. 解析 `mcperiods.rc`
   - 读取 `MCPeriods` 中每行 `start,end,period`。
   - 使用半开区间 `[start, end)` 判断日期所属 period。
   - 将 weekly CSV 的 `name` 字段解析成 `date1_date2`。
   - 对每周统计覆盖的 period 和天数，生成 `period_mix`。

2. 判断每周是否可拟合
   - 如果周内主 period 没有 `Response.root`，标记 `fit_status=missing_response`。
   - 如果周日期超出 `mcperiods.rc` 覆盖范围，标记 `fit_status=missing_period`。
   - 第一版不对缺响应或缺 period 的周硬外推。

3. 实现 forward folding
   - 读取 `Response.root:Resp_k/hresp_k`。
   - 读取每周 `n_on[k]`、`n_bkg[k]`、`n_off[k]`、`tobs`。
   - 固定 `Gamma=2.6`，只拟合 `N0 >= 0`。
   - 用 Poisson likelihood：

     ```text
     mu_on[k] = n_bkg[k] + N_pred[k](N0)
     L = product_k Poisson(n_on[k] | mu_on[k])
     ```

   - 输出 `N0`、`N0_err`、`TS` 和 `fit_status`。

4. 输出结果
   - 建议输出：
     `data/processed/wcda_week/flux_forward_folded.csv`
   - 至少包含字段：

     ```text
     name,mjd,date1,date2,period,period_mix,tobs,
     N0,N0_err,TS,fit_status,old_excess_rate
     ```

   - `old_excess_rate = sum(n_on - n_bkg) / tobs`，用于 sanity check。

## Current Bridge Artifact

已新增轻量衔接脚本：

```bash
/home/lhaaso/tangruiyi/miniconda3/envs/myrootenv/bin/python MakeLC/flux_forward_folding.py
```

当前输出：

```text
results/LHAASO-WCDA_Mkn421_week_flux_status.csv
```

这张表还不是物理 flux；它只是把每个 weekly count bin 对齐到主 period、
period mix、响应可用状态和旧的 excess count rate。最新检查结果：

- 总 weekly rows：264
- `ok`：159 周，完全落在单个有响应的 period
- `cross_period_ok`：71 周，跨 period 但主 period 有响应；第一版可先按主
  period 处理，后续再改成按天数拆分/加权响应
- `missing_response`：13 周，主要是 `T084..T091` 缺响应
- `missing_period`：21 周，`2025-11-03` 之后缺 period map

## HTCondor Execution Plan

登录节点只做 smoke test，不跑完整 264 周。

1. 本地 smoke test
   - 只跑前 1-3 周。
   - 检查响应读取、period 匹配、拟合状态和输出字段。

2. 批量任务
   - 建议建立 `JOBs_flux_Mkn421_weekly/`。
   - 每个 Condor job 处理 5-10 周。
   - 每个 chunk 输出一个 partial CSV。
   - 全部完成后合并 partial CSV。

3. 作业脚本环境

   ```bash
   source /home/lhaaso/tangruiyi/miniconda3/etc/profile.d/conda.sh
   conda activate myrootenv
   ```

4. 提交方式

   ```bash
   condor_status -schedd -af Name Machine TotalRunningJobs TotalIdleJobs TotalHeldJobs
   condor_submit -name scheduler@scheddXX.ihep.ac.cn JOBs_flux_Mkn421_weekly/flux_weekly.sub
   condor_q -global $USER
   ```

## Validation Checks

- `fit_status=ok` 的周数和比例。
- `missing_response` 应主要出现在 period `T084..T091`。
- `missing_period` 应出现在 `2025-11-05` 之后。
- `N0` 与 `old_excess_rate` 应高度相关，目标 Pearson correlation `> 0.95`。
- `N0` 不应大面积贴边为 0。
- 亮周应有更大的 `TS`。
- 最终接入 QPO 分析前，必须确认单位和归一化无误。

## Open Questions to Confirm

这些问题需要向师姐、教程或标准配置再次确认：

1. `S0` 的定义和值是什么？它应负责把 flux 单位、面积归一化和 expected counts
   接起来。
2. `hresp_k` 的 X 轴能量定义是否确认为 `log10(E/eV)`，并在拟合中转成 TeV？
3. `S0` 或标准公式里是否还包含额外面积单位转换，例如 `m^2` 到 `cm^2`？
4. `Tobs` 是否只需要使用 weekly CSV 里的 `tobs`，还是需要重新按 period/DAQ
   live time 计算？
5. `T084..T091/Response.root` 在哪里？
6. `2025-11-05` 到 `2026-03-29` 的 period map 从哪里获取？
7. 第一版是否使用 `GoodPeriods` 或 `NicePeriods` 过滤？
   - 当前默认：所有有 period 和 response 的周都拟合，同时输出 period 质量标记。
8. 后续是否需要 Crab weekly CSV 做绝对标定 sanity check？
   - 当前默认：第一版暂不做 Crab，只做 Mrk 421 内部一致性检查。

## Decisions Already Made

- 第一版固定 `Gamma = 2.6`。
- 第一版先输出 differential flux normalization `N0 @ 3 TeV`。
- 第一版不拟合谱指数，不做谱演化。
- 第一版不对缺响应或缺 period 的周硬外推。
- 大计算使用 HTCondor。
- Crab 校验延后。
