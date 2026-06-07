# WCDA counts 转 flux 当前状态说明

更新时间：2026-05-21

## 目标

之前的 WCDA light curve 产物本质上是 photon counts / excess count rate：

```text
old_excess_rate = sum(n_on - n_bkg) / tobs
```

它不是物理 flux。师姐建议的正确做法是使用探测器响应做 forward folding：

1. 对每个时间 bin 找到对应的 detector period。
2. 读取该 period 的响应文件：
   `/home/lhaaso/hushicong/Standard_file_lib/results/Response/Cod/Factor_1.04/`
3. 假设源谱形，例如固定 `Gamma = 2.6` 的 power-law。
4. 用响应把源 flux 模型折叠成 WCDA 各 `nhits` bin 里应该看到的 counts。
5. 用 Poisson likelihood 拟合 flux 归一化 `N0`。

师姐提到可以参考这个 IHEP notebook：

```text
https://jupyter.ihep.ac.cn/113I0f1xR6S0TBjsgfJV5Q
```

或者参考 xishaoqiang 的程序。

## 当前仓库里已有的相关文件

### 方法说明

- `docs/flux_handoff.md`
  - 记录了师姐方法的整体理解。
  - 说明 forward folding 的数学思路和需要确认的问题。

- `docs/flux_forward_folding_action_plan.md`
  - 记录已经确认的事实、执行计划和卡点。
  - 我已经把本次调研结果补进去了。

### period 查表

- `docs/iPeriod_1Days.h`
  - 旧版日到 period 的 C++ 查表。
  - `Ndura = 1565`
  - period 只到 `T068`
  - 可以作为概念参考或早期数据交叉检查，但不能覆盖当前完整 weekly CSV。

- 当前可读到的最新版 period 配置：

  ```text
  /home/lhaaso/tangruiyi/analysis/from_yaozhiguo_2/Cog/conf/mcperiods.rc
  ```

  覆盖：

  ```text
  2021-03-08 到 2025-11-05
  T001 到 T091
  ```

### counts 输入

当前主要 weekly 输入：

```text
results/LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv
```

它包含 264 个 weekly bin，每行有：

```text
name,mjd,n_on,n_bkg,n_off,tobs
```

其中 `n_on`、`n_bkg`、`n_off` 都是 7 个 `nhits` bin 的数组。

## 我这次新增的衔接产物

新增脚本：

```text
MakeLC/flux_forward_folding.py
```

这个脚本还不做物理 flux 拟合。它先做 forward folding 前必须完成的对齐工作：

1. 读取 weekly counts CSV。
2. 读取 `mcperiods.rc`。
3. 给每个 weekly bin 找主 period。
4. 标记这周是否跨 period。
5. 检查主 period 是否有 `Response.root`。
6. 计算旧的 `old_excess_rate`，后面用于和新 flux 做 sanity check。

运行命令：

```bash
/home/lhaaso/tangruiyi/miniconda3/envs/myrootenv/bin/python MakeLC/flux_forward_folding.py
```

输出：

```text
results/LHAASO-WCDA_Mkn421_week_flux_status.csv
```

当前统计结果：

```text
264 weeks total
159 ok
71 cross_period_ok
13 missing_response
21 missing_period
```

含义：

- `ok`
  - 这一周完全落在一个 period 里。
  - 主 period 有响应文件。
  - 可以进入第一版 forward folding。

- `cross_period_ok`
  - 这一周跨了多个 period。
  - 主 period 有响应文件。
  - 第一版可以先按主 period 近似处理；更严谨做法是按天数拆分响应或加权响应。

- `missing_response`
  - 有 period，但缺响应文件。
  - 当前主要是 `T084..T091`。

- `missing_period`
  - 超出当前 `mcperiods.rc` 覆盖范围。
  - 主要是 `2025-11-03` 之后。

## 当前响应库覆盖情况

响应库路径：

```text
/home/lhaaso/hushicong/Standard_file_lib/results/Response/Cod/Factor_1.04/
```

当前可见响应：

```text
T001/Response.root 到 T083/Response.root
```

当前缺失：

```text
T084 到 T091
```

因此，即使用 `mcperiods.rc` 能查到 `T084..T091`，也暂时不能对这些 period 做标准 forward folding。

## 权限问题

原始 period 配置生成脚本疑似在：

```text
/afs/ihep.ac.cn/users/w/wcdarec/wcda/masks/masks/src/mkperiods.py
```

但当前账号没有权限读取。

检查结果：

```text
ls: cannot access .../masks/masks/src/mkperiods.py: Permission denied
```

上级目录也显示权限受限：

```text
/afs/ihep.ac.cn/users/w/wcdarec      drwx------
/afs/ihep.ac.cn/users/w/wcdarec/wcda drwx------
```

所以现在不能从这个脚本确认 `2025-11-05` 之后的 period 应该怎么生成。

## 当前能做什么

### 1. 先做可覆盖区间的 Mrk 421 flux

可以先对 `T001..T083` 覆盖的 weekly bins 做第一版 forward folding。

大致范围：

```text
2021-03-08 到 2025-08-03 左右
```

这部分包含：

```text
159 ok + 71 cross_period_ok = 230 weeks
```

第一版策略：

- 固定 `Gamma = 2.6`
- 输出 `N0 @ 3 TeV`
- `ok` 周直接拟合
- `cross_period_ok` 周先按主 period 近似拟合
- 明确在输出里保留 `fit_status` 和 `period_mix`

### 2. 用当前状态表做检查

可以打开：

```text
results/LHAASO-WCDA_Mkn421_week_flux_status.csv
```

先确认每周的：

- 主 period
- 是否跨 period
- 是否缺响应
- 是否缺 period
- 旧 `old_excess_rate`

这能帮助你决定第一版 flux 要截断到哪里。

### 3. 向师姐或相关同学确认缺口

现在最值得问的是：

1. `T084..T091/Response.root` 是否已经生成？如果有，放在哪里？
2. `2025-11-05` 之后的 `mcperiods.rc` 是否已经生成？如果有，放在哪里？
3. `mkperiods.py` 是否可以给你读权限，或者直接给一份最新 `mcperiods.rc`？
4. forward folding 公式里的 `S0` 应该取什么值？
5. xishaoqiang 的程序路径在哪里？

## 当前暂时不能做什么

### 1. 不能生成完整到 2026-03-29 的物理 flux

原因有两个：

1. `2025-08-04` 到 `2025-11-02`：
   - 有 period map
   - 但缺 `T084..T091` 响应

2. `2025-11-03` 到 `2026-03-29`：
   - 缺 period map
   - 也没有确认是否有对应响应

所以现在不能对完整 264 周都做可靠的物理 flux。

### 2. 不能直接把 old_excess_rate 当 flux 用

`old_excess_rate` 只是：

```text
sum(n_on - n_bkg) / tobs
```

它没有扣除：

- 探测器效率
- 有效面积
- zenith 角响应
- nhits 到能量的响应
- period 之间探测器状态变化

它只能作为 sanity check，与 forward-folded `N0` 做相关性比较。

### 3. 不能在 login 节点上跑完整批量拟合

完整 230 周或 264 周拟合属于批量任务，应该走 HTCondor。

login 节点只适合：

- 1 到 3 周 smoke test
- 响应文件读取检查
- period 对齐检查
- 输出格式检查

## 还卡住的问题

### 卡点 1：`S0` 未确认

文档里目前知道标准拟合形式类似：

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

但 `S0` 的定义和值还没有确认。

它可能负责：

- MC 投点面积归一化
- 单位换算
- 从 differential flux 到 expected counts 的尺度因子
- 可能还包含 `m^2` 到 `cm^2` 的转换

不确认 `S0`，就不能保证输出的 `N0` 单位和绝对量级正确。

### 卡点 2：晚期响应缺失

当前 `Factor_1.04` 响应库只有：

```text
T001..T083
```

缺：

```text
T084..T091
```

这会影响 `2025-08-04` 到 `2025-11-02` 的 weekly bins。

### 卡点 3：2025-11-05 之后 period map 缺失

当前可读 `mcperiods.rc` 到：

```text
2025-11-05
```

但 counts CSV 到：

```text
2026-03-29
```

因此 `2025-11-03` 之后的 weekly bins 不能可靠分配 period。

### 卡点 4：标准程序还没拿到本地可执行版本

师姐给的是 notebook 链接，或者 xishaoqiang 的程序。

现在还缺：

- notebook 里具体的 likelihood 实现
- 响应 ROOT 轴定义的标准读取方式
- `S0` 和能量单位处理
- 标准输出格式

这些最好直接从 notebook 或 xishaoqiang 的程序里抄逻辑，而不是自己猜。

## 建议下一步

### 最短路径

1. 找到或打开师姐给的 IHEP notebook。
2. 从 notebook 中确认：
   - `S0`
   - 能量轴单位
   - `DisZen` 如何取
   - likelihood 函数
   - `N0` 单位
3. 用 `MakeLC/flux_forward_folding.py` 产出的状态表，先选前 1 到 3 个 `ok` 周做 smoke test。
4. smoke test 通过后，把 `T001..T083` 可覆盖的 230 周提交 HTCondor。
5. 输出第一版：

   ```text
   results/LHAASO-WCDA_Mkn421_flux_forward_folded_T001_T083.csv
   ```

### 你现在可以去问的问题

可以直接问师姐或维护响应库的人：

```text
我现在做 Mrk 421 weekly counts -> flux 的 forward folding。
当前可读 period 表 /home/lhaaso/tangruiyi/analysis/from_yaozhiguo_2/Cog/conf/mcperiods.rc 只到 2025-11-05，
响应库 /home/lhaaso/hushicong/Standard_file_lib/results/Response/Cod/Factor_1.04/ 只看到 T001-T083。

请问：
1. T084-T091 的 Response.root 在哪里？
2. 2025-11-05 之后的 mcperiods.rc 或 iPeriod_1Day 在哪里？
3. mkperiods.py 能否给我读权限，或者直接给我最新生成的 period 配置？
4. forward folding 里 S0 的定义和值是多少？
5. xishaoqiang 的 flux 拟合程序路径在哪里？
```

## 当前结论

现在不是完全做不了，而是只能先做“有 period 且有响应”的部分。

可靠的第一版范围是：

```text
T001..T083
约 2021-03-08 到 2025-08-03
230 个 weekly bins
```

完整做到 `2026-03-29` 需要补齐：

1. `T084` 之后的响应文件。
2. `2025-11-05` 之后的 period map。
3. 标准程序里的 `S0` 和单位定义。
