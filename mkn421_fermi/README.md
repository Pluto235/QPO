# mkn421

该目录对应 Mrk 421 的 Fermi-LAT 自建分析链。

- `config.yaml` 与 `run.py`：事件级分析与月 bin 光变生产入口。
- `mkn421.ipynb`：整理后的月 bin QPO 分析 notebook。
- `mkn421/` 子目录：`fermipy` 生成的 ROI、light curve 与中间产物。
- `data/`：Fermi 原始事件与航天器文件。
- `emmanoulopoulos/`、`DELightcurveSimulation/`：红噪声模拟与方法参考实现。

该目录内保留了较多 `fermipy` 输出文件，以优先保障可复现性，不对其做高风险搬迁。
