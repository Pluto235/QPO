# mkn421_lhaaso

该目录对应 Mrk 421 的 Fermi weekly 与 LHAASO WCDA 联合时序分析。

- `mkn421_fermi.ipynb`：官方 Fermi weekly 光变的筛选、时段裁剪与时频检查。
- `mkn421_lhaaso.ipynb`：WCDA 周光变构建、CWT/WWZ 与模拟检查主 notebook。
- `simulations/generate_wcda_weekly_sims.py`：当前推荐的 WCDA Emmanoulopoulos 模拟脚本，保留清晰 CLI 接口，便于 Slurm 提交。
- `simulation.py`：兼容旧调用方式的包装入口。
- `simulations/`：HDF5 模拟输出。
- `.csv` / `.lc`：当前分析使用的数据输入。

该目录是 Fermi–WCDA 共同时段 QPO 搜索的主工作区。
