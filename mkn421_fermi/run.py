from pathlib import Path

from fermipy.gtanalysis import GTAnalysis
import numpy as np


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"
ROI_PATH = BASE_DIR / "mkn421" / "mkn421_fulltime.fits"

# 初始化
gta = GTAnalysis(str(CONFIG_PATH), logging={"verbosity": 3})

# 跑数据准备（gtselect, gtmktime, gtbin, etc.）
gta.setup()

# 做一次全时段的 ROI 拟合
gta.optimize()

# 可选：再精细一点
gta.free_sources(distance=3.0)   # 释放 3° 内源的谱参数
gta.fit()

# 保存 ROI 模型
gta.write_roi(str(ROI_PATH))



# 读入刚才已经 setup+fit 好的工程
gta = GTAnalysis(str(CONFIG_PATH), logging={"verbosity": 3})
gta.load_roi(str(ROI_PATH))

# Mkn 421 在 4FGL 里的名字（你之前可能用过 3FGL 名称）
src_name = '4FGL J1104.4+3812'

# 0.1–300 GeV：log10(E/MeV) 范围 [2, log10(3e5)]
loge_min = 2.0              # 100 MeV
loge_max = np.log10(316227)   # 316227 MeV

lc = gta.lightcurve(
    src_name,
    binsz=30 * 86400,               # 30 天一个 bin = monuthly
    free_background=True,    # 每个 time bin 释放背景
    use_local_ltcube=False,
   #  use_scaled_srcmap=True
)
