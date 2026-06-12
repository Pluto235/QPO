# 8 AGN Weekly Strict WCDA Flux Run Note

日期：2026-06-01

## 口径

- 任务：为 8 个 AGN QPO candidates 生成 weekly strict flux light curves。
- 时间范围：`2021-03-08` 到 `2025-07-27`，共 229 个 weekly bins。
- 数据：复用已有 weekly counts sky maps，不重新 merge map。
- map 目录：`/eos/user/l/liushijie/Skymap/2021-03-08_2026-03-29_week/`
- 拟合：单源 forward-folding fit。
- 谱模型：PL，固定 `gamma=2.6`，`E0=3 TeV`，只拟合 `F0`。
- caveat：`NGC1275` 和 `IC310` 角距离很近，本轮仍按单源 fit；对应 flux 可能包含近邻源混叠贡献，不应解释为严格解耦后的物理通量。

## 输入源

- `1ES1959p650`
- `1ES1727p502`
- `1ES2344p514`
- `BLLacertae`
- `NGC1275`
- `M87`
- `4C_p42d22`
- `IC310`

坐标沿用 `docs/ihep-wcda-pull-tasklist.md` 和 `data/wcda_week/*.csv` 头信息。

## 工作目录

- workflow script：`MakeLC/standard_flux_lc.py`
- work dir：`JOBs_flux_strict_agn_week/`
- fit manifest：`JOBs_flux_strict_agn_week/fit_jobs.csv`
- final results：`results/flux_strict_agn_week/`
- figures：`results/flux_strict_agn_week/figures/`

准备结果：

- fit jobs：1832
- missing maps：0
- 每源 bins：229

## HTCondor

提交命令：

```bash
condor_submit -name scheduler@schedd11.ihep.ac.cn JOBs_flux_strict_agn_week/fit.sub
```

提交结果：

- cluster：`2727774`
- jobs：367 chunk jobs
- chunk size：5 fit rows per job
- `max_materialize = 120`
- `request_memory = 2500 MB`
- `request_disk = 2000 MB`

检查命令：

```bash
condor_q -name scheduler@schedd11.ihep.ac.cn -constraint 'ClusterId==2727774'
find JOBs_flux_strict_agn_week/fits -name ParRes.yaml -type f | wc -l
python MakeLC/standard_flux_lc.py validate fit --work-root JOBs_flux_strict_agn_week
```

合并命令：

```bash
python MakeLC/standard_flux_lc.py merge --work-root JOBs_flux_strict_agn_week --result-root results/flux_strict_agn_week
python MakeLC/standard_flux_lc.py plot --work-root JOBs_flux_strict_agn_week --result-root results/flux_strict_agn_week
```
