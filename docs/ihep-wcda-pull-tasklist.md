# IHEP WCDA Weekly Counts Handoff for AGN QPO Survey

日期：2026-05-27

## 目标与交付边界

这份 handoff 是写给 **IHEP 上的 Codex** 的执行交接文档。目标是在 **不修改远端 MakeLC 代码主逻辑** 的前提下，复用你之前生成 `Mrk421` WCDA photon counts 的同一条 pipeline，为 AGN QPO survey 第一批目标源生成 **weekly counts CSV**。

本 handoff 的交付边界固定为：

1. 在 `/home/lhaaso/liushijie/QPO` 工作区内执行。
2. 先复盘并复用 `Mrk421` 的 `MakeLC` counts 生成 pipeline。
3. 为下列 **8 个源** 生成 weekly counts CSV：
   - `1es1959p650`
   - `1es1727p502`
   - `1es2344p514`
   - `bllac`
   - `ngc1275`
   - `m87`
   - `4c_p42d22`
   - `ic310`
4. **所有大规模 merge / counting 步骤必须通过 HTCondor / `hep_sub` 提交。**
5. **登录节点只做检查、准备、日志轮询、结果汇总，不运行大规模计算。**
6. 最终 weekly counts CSV 必须写入：
   `/home/lhaaso/liushijie/QPO/data/wcda_week/`
7. 当 8 个源的 weekly CSV 都已生成，并通过结构检查后，任务停止。
8. **不要**在本 handoff 范围内继续做：
   - periodicity / WWZ / CWT
   - flux forward folding
   - Fermi 数据处理
   - 远端 MakeLC 代码重构

## 已确认事实

### 1. 远端主工作区

- 远端主工作区固定为：`/home/lhaaso/liushijie/QPO`
- 本 handoff 文档远端落点固定为：
  `/home/lhaaso/liushijie/QPO/docs/ihep-wcda-pull-tasklist.md`

### 2. `Mrk421` 参考 pipeline 的已知来源

本地已恢复出的历史信息表明，之前的 WCDA photon counts 构造链路来自 `MakeLC` 系列 notebook / 脚本，而不是本地 `src/pipeline/periodicity_v1.py`。

已知参考线索：

- 旧 notebook 逻辑依赖 `MakeLC` 包
- `liushijie` 工作区已经有 `MakeLC` 副本思路，优先应使用：
  `/home/lhaaso/liushijie/QPO/MakeLC`
- `Mrk421 daily` 的已知适配模式是：
  - `sys.path.append("/home/lhaaso/liushijie/QPO")`
  - `from MakeLC.merge import make_list, submit_merge_jobs, check_jobs`
  - `from MakeLC.read import read_list`
  - `from MakeLC.subjobs import subjobs, contact_task_list`
- 运行环境目前已知是借用 `tangruiyi` 的 `myrootenv`

### 3. `MakeLC` 的关键流程

`Mrk421` 参考 counts 流程应视为固定链路：

1. `submit_merge_jobs(...)`
2. `read_list(...)`
3. `subjobs(...)`
4. `contact_task_list(...)`

weekly 计数的关键参数是：

- `date1 = "2021-03-08"`
- `date2 = "2026-03-29"`
- `merge_date2 = "2026-03-29"`
- `step_days = 7`
- `nhits = [0, 1, 2, 3, 4, 5, 6]`
- `delta = [0.89, 0.662, 0.498, 0.398, 0.332, 0.263, 0.196]`
- `max_zen = 50.0`
- `method = "WCDA"`

最终 CSV 的必需列固定为：

```text
name,mjd,n_on,n_bkg,n_off,tobs
```

这类 CSV 是 **weekly photon counts / excess-rate proxy 输入**，不是 calibrated physical flux。

## `Mrk421` 参考 pipeline 复盘

远端 Codex 在正式跑 8 个源前，必须先复盘 `Mrk421` 的 counts 生成方式，确认自己复用的是同一套 pipeline，而不是自己重新设计。

优先检查顺序固定为：

1. `/home/lhaaso/liushijie/QPO/MakeLC_Mkn421_daily.ipynb`，如果存在
2. `/home/lhaaso/liushijie/QPO/MakeLC.ipynb`，如果存在
3. `/home/lhaaso/liushijie/QPO/MakeLC/merge.py`
4. `/home/lhaaso/liushijie/QPO/MakeLC/subjobs.py`
5. `/home/lhaaso/liushijie/QPO/MakeLC/read.py`
6. 现有 `Mrk421` weekly CSV，如果远端已有：
   - `/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv`
   - 或 `/home/lhaaso/liushijie/QPO/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv`

如果 `liushijie` 工作区的参考 notebook 不存在，允许只读参考：

- `/home/lhaaso/tangruiyi/analysis/QPO`

但主执行路径仍然必须回到 `/home/lhaaso/liushijie/QPO`。

## 8 个源的参数与输出约定

下表中的参数在本 handoff 中已经定死，远端 Codex 不需要再自行决定。

| source_id | human_label | source_name / token | RA | DEC | output_csv |
|---|---|---|---:|---:|---|
| `1es1959p650` | `1ES 1959+650` | `1ES1959p650` | 299.95 | 65.15 | `LHAASO-WCDA_1ES1959p650_2021-03-08_2026-03-29_week.csv` |
| `1es1727p502` | `1ES 1727+502` | `1ES1727p502` | 262.05 | 50.15 | `LHAASO-WCDA_1ES1727p502_2021-03-08_2026-03-29_week.csv` |
| `1es2344p514` | `1ES 2344+514` | `1ES2344p514` | 356.75 | 51.75 | `LHAASO-WCDA_1ES2344p514_2021-03-08_2026-03-29_week.csv` |
| `bllac` | `BL Lacertae` | `BLLacertae` | 330.75 | 42.15 | `LHAASO-WCDA_BLLacertae_2021-03-08_2026-03-29_week.csv` |
| `ngc1275` | `NGC 1275` | `NGC1275` | 49.95 | 41.45 | `LHAASO-WCDA_NGC1275_2021-03-08_2026-03-29_week.csv` |
| `m87` | `M 87` | `M87` | 187.75 | 12.45 | `LHAASO-WCDA_M87_2021-03-08_2026-03-29_week.csv` |
| `4c_p42d22` | `4C +42.22` | `4C_p42d22` | 104.06 | 42.60 | `LHAASO-WCDA_4C_p42d22_2021-03-08_2026-03-29_week.csv` |
| `ic310` | `IC 310` | `IC310` | 49.05 | 41.25 | `LHAASO-WCDA_IC310_2021-03-08_2026-03-29_week.csv` |

所有源统一使用：

```python
nhits = [0, 1, 2, 3, 4, 5, 6]
delta = [0.89, 0.662, 0.498, 0.398, 0.332, 0.263, 0.196]
max_zen = 50.0
```

## 远端目录与环境约定

### 工作目录

- 主工作目录：
  `/home/lhaaso/liushijie/QPO`
- handoff 文档目录：
  `/home/lhaaso/liushijie/QPO/docs`
- weekly counts 输出目录：
  `/home/lhaaso/liushijie/QPO/data/wcda_week`

若缺失，允许创建：

```bash
mkdir -p /home/lhaaso/liushijie/QPO/docs
mkdir -p /home/lhaaso/liushijie/QPO/data/wcda_week
```

### 共享 merge 产物约定

weekly skymap merge 只做一套共享产物，供所有 8 个源复用。不要为每个源重复做一遍 merge。

共享 merge 相关路径固定为：

- `base_dir = /home/lhaaso/liushijie/QPO`
- `job_dir = /home/lhaaso/liushijie/QPO/JOBs`
- `eos_dir = /eos/user/l/liushijie/Skymap/2021-03-08_2026-03-29_week`
- `merge_log = /home/lhaaso/liushijie/QPO/2021-03-08_2026-03-29_week.csv`

### 每个源的 counting job 目录

每个源的 counting job 目录固定为：

```text
/home/lhaaso/liushijie/QPO/<Token>_2021-03-08_2026-03-29_week
```

例如：

- `/home/lhaaso/liushijie/QPO/1ES1959p650_2021-03-08_2026-03-29_week`
- `/home/lhaaso/liushijie/QPO/NGC1275_2021-03-08_2026-03-29_week`

对应 `Groups.csv` 固定放在：

```text
<count_job_dir>/Groups.csv
```

### Python / ROOT 环境

默认尝试沿用：

```bash
source /home/lhaaso/tangruiyi/miniconda3/etc/profile.d/conda.sh
conda activate myrootenv
```

如果这套环境不可用，本 handoff 不要求远端 Codex 自己重建新环境；应记录并停止。

## HTCondor 提交流程

### 必须项

`submit_merge_jobs(...)` 和 `subjobs(...)` 涉及的大规模重计算，**必须**通过 HTCondor / `hep_sub` 提交。

在当前工作区中：

- `MakeLC/merge.py` 中的 `submit_merge_jobs(...)` 通过 `hep_sub` 提交 merge 任务
- `MakeLC/subjobs.py` 中的 `subjobs(...)` 通过 `hep_sub` 提交 counting 任务

因此：

- 不要把 merge 重写成本地长循环
- 不要把 source counting 改成在登录节点直接顺序跑全部 ROOT 文件
- 不要绕开 `hep_sub`

### 登录节点允许做的事

登录节点只允许做：

1. 路径检查
2. 环境检查
3. `MakeLC` 导入测试
4. `hep_sub` / `DI_merge` 可用性检查
5. 查看日志和错误文件
6. 检查 `Groups.csv`
7. 对已完成任务运行 `contact_task_list(...)`
8. 对最终 CSV 做结构检查
9. 生成简短状态说明

### 登录节点禁止做的事

登录节点禁止直接做：

1. 大范围 skymap merge
2. 全量 source counts 批处理
3. 任何替代 HTCondor 的长时间循环
4. 8 个源全量 ROOT 输入上的本地串行重计算

本 handoff 中的操作约束是：

> **所有 merge / counting 的重计算必须提交 HTCondor 作业，不能在 login node 上直接跑批量计算。**

## 执行步骤

按以下顺序执行，不要跳步。

### Step 0：进入工作区

```bash
cd /home/lhaaso/liushijie/QPO
mkdir -p docs
mkdir -p data/wcda_week
```

### Step 1：检查核心路径

确认以下路径是否存在：

- `/home/lhaaso/liushijie/QPO/MakeLC`
- `/home/lhaaso/liushijie/QPO/MakeLC/DI_merge/DI_Merge`
- `/home/lhaaso/liushijie/QPO/JOBs`

如果缺少 `JOBs`，可以创建。  
如果缺少 `MakeLC` 或 `DI_merge/DI_Merge`，进入“回退策略”处理。

### Step 2：检查 `hep_sub` 和环境

在登录节点只做轻量检查：

```bash
which hep_sub
source /home/lhaaso/tangruiyi/miniconda3/etc/profile.d/conda.sh
conda activate myrootenv
python -c "import sys; sys.path.append('/home/lhaaso/liushijie/QPO'); import MakeLC.merge, MakeLC.read, MakeLC.subjobs; print('MakeLC import OK')"
```

如果：

- `hep_sub` 不可用 -> 记录并停止
- `myrootenv` 无法激活 -> 记录并停止
- `MakeLC` 无法导入 -> 只读参考 `tangruiyi` 目录排查，不要在这一步私自改主逻辑

### Step 3：复盘 `Mrk421` 参考 pipeline

优先检查以下对象是否存在并可读：

- `MakeLC_Mkn421_daily.ipynb`
- `MakeLC.ipynb`
- `MakeLC/merge.py`
- `MakeLC/subjobs.py`
- `MakeLC/read.py`
- 已有 `Mrk421` weekly CSV

目标是确认 weekly counts 仍然使用这条链路：

```text
submit_merge_jobs(...) -> read_list(...) -> subjobs(...) -> contact_task_list(...)
```

如果确认无误，再继续。

### Step 4：准备或复用共享 weekly merge 产物

共享 weekly merge 参数固定为：

```python
date1 = "2021-03-08"
date2 = "2026-03-29"
merge_date2 = "2026-03-29"
step_days = 7
eos_dir = "/eos/user/l/liushijie/Skymap/2021-03-08_2026-03-29_week"
job_dir = "/home/lhaaso/liushijie/QPO/JOBs"
merge_log = "/home/lhaaso/liushijie/QPO/2021-03-08_2026-03-29_week.csv"
```

执行规则：

1. 如果 `merge_log` 已存在，并且能被 `read_list(merge_log, "skymap")` 正常读取，则直接复用
2. 如果 `merge_log` 不存在，或明显不完整，则 **通过 `submit_merge_jobs(...)` 提交 merge 作业**
3. merge 作业提交后，只在登录节点轮询状态与日志，不直接改为本地批跑

### Step 5：为 8 个源准备 weekly counting 配置

对每个源按固定参数准备配置：

- `source_name = <Token>`
- `ra = <table value>`
- `dec = <table value>`
- `nhits = [0,1,2,3,4,5,6]`
- `delta = [0.89,0.662,0.498,0.398,0.332,0.263,0.196]`
- `max_zen = 50.0`
- `count_job_dir = /home/lhaaso/liushijie/QPO/<Token>_2021-03-08_2026-03-29_week`
- `group_log = <count_job_dir>/Groups.csv`
- `output_csv = /home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_<Token>_2021-03-08_2026-03-29_week.csv`

`ntask` 固定使用 `4`，与已知参考 notebook 保持一致。

### Step 6：通过 `hep_sub` / HTCondor 提交 counting 作业

对每个源：

1. 使用 `files = read_list(merge_log, "skymap")`
2. 调用：

```python
group_log = subjobs(
    files,
    jobs_dir=str(count_job_dir),
    name_pattern=r"(\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2})",
    ntask=4,
    method="WCDA",
    ra=ra,
    dec=dec,
    nhits=nhits,
    delta=delta,
    max_zen=max_zen,
)
```

3. 这一步必须走 `hep_sub`
4. 提交后不要在登录节点直接展开全量 ROOT 处理

### Step 7：轮询日志并检查错误

登录节点只做轻量轮询：

- 查看 `group_log`
- 查看各组 `.out` / `.err`
- 使用 `check_jobs(...)` 检查失败项

如果某源部分子任务失败：

- 记录失败源名
- 记录失败脚本或错误日志路径
- 不影响继续检查其他源

### Step 8：汇总最终 CSV

仅当某源的 `Groups.csv` 对应任务完成并可汇总时，执行：

```python
contact_task_list(
    group_log,
    output_csv,
    ra=ra,
    dec=dec,
    nhits=nhits,
    delta=delta,
    max_zen=max_zen,
)
```

最终 CSV 一律写入：

```text
/home/lhaaso/liushijie/QPO/data/wcda_week/
```

### Step 9：结构检查

对每个成功生成的 `output_csv` 做结构检查：

1. 能用 `pd.read_csv(path, comment="#")` 读入
2. 必需列存在：
   - `name`
   - `mjd`
   - `n_on`
   - `n_bkg`
   - `n_off`
   - `tobs`
3. 行数 `> 0`
4. `mjd` 不全为空
5. `n_on/n_bkg/n_off` 至少在首行能看出是 7-bin 数组样式

只要某个文件不满足以上条件，就标为失败，不算完成。

### Step 10：写简短状态说明并停止

在 `/home/lhaaso/liushijie/QPO/docs/` 下写一个简短状态说明，例如：

```text
ihep-wcda-pull-tasklist-status.md
```

状态说明至少包含：

- 运行日期
- 8 个源各自状态：success / failed / skipped
- 成功源的输出文件路径
- 失败源的错误摘要
- 是否全部通过结构检查

完成后停止。  
**不要继续做 periodicity、flux 或本地同步。**

## 产物与验收标准

### 主产物

8 个源的 weekly counts CSV，位置固定为：

```text
/home/lhaaso/liushijie/QPO/data/wcda_week/LHAASO-WCDA_<Token>_2021-03-08_2026-03-29_week.csv
```

### 辅助产物

- 共享 merge log：
  `/home/lhaaso/liushijie/QPO/2021-03-08_2026-03-29_week.csv`
- 每个源的 `Groups.csv`
- 日志文件 `.out/.err`
- 状态说明：
  `/home/lhaaso/liushijie/QPO/docs/ihep-wcda-pull-tasklist-status.md`

### 完成标准

只有在以下条件满足时，本 handoff 才算完成：

1. 8 个目标源都已尝试执行
2. 每个成功源都生成了 weekly CSV
3. 成功源 CSV 通过结构检查
4. 所有重计算都通过 HTCondor / `hep_sub` 提交
5. 登录节点没有被用来直接跑大规模 merge / counting
6. 状态说明已写出

## 卡点与回退策略

### 1. `MakeLC` 副本缺失

如果：

- `/home/lhaaso/liushijie/QPO/MakeLC` 不存在
- 或 `DI_merge/DI_Merge` 缺失

则允许只读参考：

```text
/home/lhaaso/tangruiyi/analysis/QPO
```

但不要直接把执行基座切换到 `tangruiyi` 工作区长期跑完整任务；优先在 `liushijie/QPO` 下恢复可执行路径。

### 2. `myrootenv` 不可用

如果默认环境不可激活：

- 记录错误
- 停止
- 不私自换成新环境或现场大改依赖

### 3. `hep_sub` / HTCondor 不可用

如果：

- `hep_sub` 不在 PATH
- 或提交系统明显不可用

则：

- 记录错误
- 停止
- **不要**改为在登录节点本地串行批跑

### 4. EOS 路径或权限失败

如果共享 merge 输入或 EOS 目录出问题：

- 记录失败源或失败阶段
- 尽量继续其它不受影响部分
- 不要擅自替换到未知数据源

### 5. 某源子任务失败

如果某源 counting job 失败：

- 保留已成功源的结果
- 在状态说明中记录：
  - 源名
  - 失败阶段
  - 关键错误日志路径

不要因为单源失败而清空已完成结果。

## 最后提醒

这份 handoff 的核心约束只有两条，执行时不要偏离：

1. **复用 `Mrk421` 的 MakeLC pipeline，不自己重新设计 counts 生成方案。**
2. **所有大规模 merge / counting 一律通过 HTCondor / `hep_sub` 提交，登录节点不要运行大规模计算。**
