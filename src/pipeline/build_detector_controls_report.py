"""Build the offline Chinese report from saved four-source diagnostics."""
from __future__ import annotations

import base64
from datetime import datetime
from zoneinfo import ZoneInfo
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd

from utils.project_paths import PROJECT_ROOT,ensure_dir


def _number(value,digits=4):
    return '—' if pd.isna(value) else f'{float(value):.{digits}g}'


def _candidate_table(frame):
    if frame.empty:
        return '未识别到符合规则的内部候选峰。'
    lines=['| 方法 | 周期 / d | 周期数 | 峰值超过95% / 99%参考 | local FAP | global FAP | 四源校正FAP |',
           '| --- | ---: | ---: | --- | ---: | ---: | ---: |']
    for _,row in frame.iterrows():
        flags=f"{'是' if row.get('above_95',False) else '否'} / {'是' if row.get('above_99',False) else '否'}"
        lines.append(f"| {row['method']} | {_number(row.period_days)} | {_number(row.get('cycles'),3)} | {flags} | {_number(row.get('local_fap'))} | {_number(row.get('global_fap'))} | {_number(row.get('four_source_fap'))} |")
    return '\n'.join(lines)


def build_report(args):
    output=Path(getattr(args,'report_path',PROJECT_ROOT/'reports/detector_controls_2day_qpo_20261011.html'))
    ensure_dir(output.parent)
    sources=args.sources
    records=[]
    for source in sources:
        folder=args.periodicity_dir/source.lower()
        records.append((source,json.loads((folder/'run_metadata.json').read_text()),
                        pd.read_csv(folder/'candidate_significance.csv')))
    config=records[0][1]['config']
    for _,meta,_ in records:
        for key in ('period_min','period_max','n_surrogates','wwz_time_divisions','wwz_freq_step_factor'):
            if meta['config'][key]!=config[key]:
                raise ValueError('Report cannot mix incompatible analysis configurations')
    candidates=pd.concat([frame for _,_,frame in records],ignore_index=True)
    wwz=candidates.loc[candidates.method.eq('WWZ')]
    passing=wwz.loc[wwz.four_source_fap.lt(.05)] if 'four_source_fap' in wwz else wwz
    hit_sources=sorted(passing.source.unique()) if 'source' in passing else []
    date=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d')
    lines=['---','title: "四源 WCDA 2day 周期诊断"',
        'subtitle: "严格质量筛选 · CWT / WWZ · AR(1) 条件显著性"',
        'author: "QPO 项目"',f'date: "{date}"','lang: "zh-CN"',
        'kicker: "Detector controls · 20261011 release"','toc: true','---','',
        '## 总体结论','']
    if hit_sources:
        lines.append(f"在本次高斯 AR(1) 条件模型下，{'、'.join(hit_sources)} 出现四源校正 FAP < 0.05 的 WWZ 候选。该统计阈值不等同于已确认天体周期；还需判断观测响应、筛选和拟合系统效应。")
    else:
        lines.append('本次未发现四源校正 FAP < 0.05 的 WWZ 内部候选峰。局部峰或超过逐周期参考线的结构，不能据此判定为显著周期。')
    lines += ['', '| 源 | 最低global FAP对应WWZ周期 / d | local FAP | global FAP | 四源校正FAP |',
              '| --- | ---: | ---: | ---: | ---: |']
    for source,_,frame in records:
        local=frame.loc[frame.method.eq('WWZ')]
        if local.empty:
            lines.append(f'| {source} | 无内部候选 | — | — | — |')
        else:
            best=local.sort_values(['global_fap','period_days']).iloc[0]
            lines.append(f'| {source} | {best.period_days:.2f} | {_number(best.local_fap)} | {_number(best.global_fap)} | {_number(best.four_source_fap)} |')
    lines += ['',f"本报告覆盖 {'、'.join(sources)}，每源 WWZ 使用 {config['n_surrogates']} 次模拟；完整观测范围 MJD {records[0][1]['mjd_min']:.8f}–{records[0][1]['mjd_max']:.8f}，搜索 {config['period_min']:g}–{config['period_max']:g} 天。四源属于探测器对照分析，强周期结构也可能反映响应或观测系统效应。",'',
        '> [!WARNING]','> 结果是严格筛选样本下的周期诊断。Blank175 大量零边界箱被剔除，样本分布明显改变；J1952 的冻结模型仍有未解决的 ROI 残差，原 calibration gate 未通过。当前模拟不包含这两类生成机制。','',
        '## 数据筛选与实际采样','',
        '| 源 | 原始箱 | 保留箱 | CWT网格箱 | 插值箱 / 占网格 | 最大有效点间隔 / d | AR(1) α / 真实相邻对 | E0 / TeV |',
        '| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |']
    for source,m,_ in records:
        lines.append(f"| {source} | {m['raw_rows']} | {m['retained_rows']} | {m['cwt_rows']} | {m['interpolated_rows']} / {m['interpolated_rows']/m['cwt_rows']:.1%} | {m['max_retained_gap_days']:g} | {m['ar1_alpha']:.4f} / {m['ar1_real_pairs']} | {m['pivot_energy_TeV']:g} |")
    lines += ['',
        '保留条件为 valid_fit=True、有限时间与 flux、有限正误差及正曝光；排除明确的 at_boundary=True、error_reliable=False、low_exposure=True、extreme_flux=True。空标记表示未知，不据此剔除。不新增 TS 阈值、sigma clipping、去趋势或再拟合。逐箱排除原因保存在 selection_audit.csv；同一箱可同时触发多个原因。','',
        'CWT 在首末保留点之间恢复 2day 网格，内部缺口线性插值、不向两端外推；插值点不作为真实观测绘制，也没有虚构误差。WWZ 直接采用真实保留时刻。归一化能量不同，不能直接比较四源绝对 flux。','',
        '## 方法、显著性与读图','',
        f"- **CWT：**复用 Morlet(6)，dj=1/12；flux 内部标准化。全局谱取时间平均，沿用 PyCWT 解析 AR(1) 95%/99% 参考。COI 阴影表示边缘效应显著区域；全局谱仍按现有代码包含所有时间格点，不把 COI 之外的贡献自动剔除。",
        f"- **WWZ：**复用现有 libwwz linear-grid 实现，时间分割 {config['wwz_time_divisions']}、频率步长系数 {config['wwz_freq_step_factor']:g}、decay constant=0.0125。全局谱为时域平均 WWZ。flux_err 只参与有效性检查和重复时刻合并，未作为逐点逆方差权重传入 WWZ。",
        '- **AR(1)：**α 仅由真实观测中相隔2天的相邻点对估计，按两组配对值各自中心化求相关，并限制在 [-0.95,0.95]；不把跨缺口的点当成一步相邻。CWT 和 WWZ 使用相同 α。',
        f"- **模拟：**每源 {config['n_surrogates']} 条高斯 AR(1) 序列，先在原始完整 2day 时间轴生成，再应用固定严格筛选掩码。均值和样本标准差取保留 flux；不额外注入测量误差，也不重新模拟质量筛选。随机种子按固定源顺序派生。",
        '- **候选峰：**全局谱内部峰，prominence 至少为功率跨度的10%，最小峰距两个频率箱。搜索边界上的最大值不会被强行记作内部候选峰；标出的峰不是自动成立的显著周期。',
        '- **周期数值：**表中周期是搜索网格上的峰位置，未估计周期误差；显示的小数位不代表同等测量精度。线性频率网格在长周期端较稀疏。',
        '- **95%/99%线：**逐周期的参考分位数，不是扫描整个频段后的置信度。表中“超过参考”比较该候选周期本身的峰值和该周期参考，FAP 则使用下面的窗口统计量。',
        '- **local FAP：**候选周期±10%窗口内观测最大值，与每条模拟在同一窗口的最大值比较。**global FAP：**同一观测统计量与模拟在整个搜索频段内的最大值比较。两者均为 (超越次数+1)/(模拟数+1)。',
        '- **四源校正：**min(1,4×global FAP)。这是四条 WWZ 曲线的 Bonferroni 校正，没有把 CWT 当作另一套已完成全局 FAP 的检验。CWT 的 FAP 留空。',
        '- **图的布局：**顶部真实 LC；中左 CWT 功率和 COI、中右 WWZ 功率和 ridge；底部为各自全局谱、参考线与红色候选周期标记。点击图片可查看原尺寸。',
        '- **显示范围：**每源按保留 flux 的1%–99%分位数，并上下各加分位跨度10%设 LC 纵轴。红色三角表示点或误差范围越界，数量按涉及的观测箱计；裁剪仅影响展示，所有保留值均参与计算。','',
        '## 四源结果与合成图','']
    for source,m,frame in records:
        lines += [f'### {source}','',
            f"保留 {m['retained_rows']}/{m['raw_rows']} 个真实箱；CWT 补入 {m['interpolated_rows']} 个内部缺测箱。最大有效点间隔 {m['max_retained_gap_days']:g} 天，AR(1) α={m['ar1_alpha']:.4f}。保留 flux 全范围 {_number(m['flux_min'])}–{_number(m['flux_max'])} TeV⁻¹ cm⁻² s⁻¹；主图有 {m['display_clipped_count']} 个观测的点或误差范围越界。",'']
        local=frame.loc[frame.method.eq('WWZ')]
        cwt_frame=frame.loc[frame.method.eq('CWT')]
        if not local.empty:
            best=local.sort_values(['global_fap','period_days']).iloc[0]
            lines += [f"WWZ 最低 global FAP 对应内部候选约 **{best.period_days:.2f} d**，local FAP={best.local_fap:.4f}，global FAP={best.global_fap:.4f}，四源校正后={best.four_source_fap:.4f}。",'']
        else:
            lines += ['WWZ 未识别到符合规则的内部候选峰；参考线仍由全部模拟计算。','']
        if not cwt_frame.empty:
            periods=', '.join(f'{p:.2f}' for p in cwt_frame.period_days)
            lines += [f'CWT 内部候选周期为 {periods} d；这里只评估解析参考线超越，不给出 CWT 全局 FAP。','']
        interpretation={
            'Crab':'**读图：**两种方法均显示突出的年尺度功率带；CWT约374天、WWZ约384天，早中段较强，长周期边缘区域受COI影响。Crab是探测器对照源，该结构应优先作为年尺度观测响应排查线索，而非天体QPO确认。',
            'IC443':'**读图：**CWT尾端有局域短周期强功率，其中一部分靠近边缘影响区域；WWZ脊线频繁跳变，没有与Crab类似的持续强年尺度带。部分CWT候选超过解析参考，但WWZ全频段检验不支持显著候选，不能将两者混同。',
            'Blank175':'**读图：**CWT与WWZ在约280天附近均有结构，但WWZ全频段及四源校正后未达到0.05阈值；高达61.2%的CWT网格由插值构成，这种表面一致性不是独立的稳健性证明。',
            'J1952':'**读图：**长周期功率主要在前半段增强，后半段WWZ脊线更多转向较短周期；CWT约353天、WWZ约384天。WWZ年尺度候选与Crab落在相同网格周期，值得检查共同观测响应；四源校正后未达到0.05阈值。',
        }
        if (not local.empty and not cwt_frame.empty and config['period_min']==10
                and config['period_max']==600 and config['wwz_time_divisions']==80
                and config['wwz_freq_step_factor']==.5 and config['n_surrogates']==1000):
            lines += [interpretation[source],'']
        if source=='Blank175':
            lines += ['**解释限制：**严格筛选后只保留约38%的原始箱；较密集的 CWT 插值及正值选择会改变分布与短周期结构。其高斯 AR(1) 结果是对当前条件模型的诊断，不能代表未筛选空场的完整零假设。','']
        if source=='J1952':
            lines += ['**模型限定：**原全区间模型冻结、每箱仅 F0 自由；7个相邻≥5σ ROI 残差像素尚未解决。原 calibration gate 为 failed，本次周期计算没有解除该模型状态。','']
        if source=='IC443':
            lines += ['**质量标记限定：**严格筛选只按已提供的标记及基础条件执行，未自动剔除所有数值离群点。完整 flux 范围如上；显示越界不代表这些点已从周期分析排除。','']
        image=args.periodicity_dir/source.lower()/f'{source}_strict_2day_cwt_wwz.png'
        relative=Path(os.path.relpath(image.resolve(),output.parent.resolve())).as_posix()
        lines += [f'![{source}：严格筛选2day LC、CWT/WWZ功率图与全局谱；逐周期参考线不等于全搜索显著性。]({relative})','',_candidate_table(frame),'']
    lines += ['## 解释边界与后续验证','',
        '1. **插值影响：**CWT 的解析参考是插值序列上的近似参考，没有传播插值不确定性；10–600天搜索保留了短周期段，但尤其是 Blank175，短周期相对缺口尺度较小，解释必须谨慎。',
        '2. **筛选与噪声模型：**剔除边界点使样本成为条件样本。固定掩码、高斯 AR(1) 不描述非负截断、异方差测量误差、质量筛选概率及真实仪器响应变化。',
        '3. **现有 WWZ 实现：**本次沿用已安装 libwwz，包括其首个观测索引未进入累加及方差中间量跨频率保留的既有行为；缓存仅加速重复计算，没有在本任务中重定义估计量。正式科学结论宜再用独立 WWZ 实现核对。',
        '4. **候选与证据：**local窗口由观测候选峰定位，逐周期99%线不能代替全频段FAP；四源校正也不能修复零假设不合适的问题。年尺度或其他共同结构需与响应周期、曝光及对照源一致性联合检查。',
        '5. **有限模拟：**1000次模拟的FAP最小分辨率为1/1001≈0.000999；四源校正最小约0.003996。不能报告0概率，也不把未达到分辨能力的显著性外推。','',
        '## 可复现记录与产物','',
        '原始发布包及解压文件保持不变：data/raw/wcda/detector_controls_2day_four_sources_20261011/。标准化输入为 data/processed/wcda_2day/detector_controls_20261011/。ZIP SHA256 为 a8eb5aa92293dcc7feaa269e90ce0ae65f5fe655a19067b8a0bb65407554744f。','',
        '筛选记录和两种输入保存在 data/processed/aligned/detector_controls_20261011/；变换数组、逐周期参考、1000条模拟全局谱及种子、候选表、图和运行元数据保存在 data/processed/periodicity/detector_controls_20261011/。运行元数据记录软件版本、代码哈希、输入SHA256、耗时及完整网格等价检查误差。','',
        '| 源 | 随机种子 | WWZ时间×频率格点 | 观测/模拟核对最大绝对差 | 耗时 / s |',
        '| --- | ---: | --- | --- | ---: |']
    for source,m,_ in records:
        lines.append(f"| {source} | {m['config']['seed']} | {m['wwz_time_bins']} × {m['wwz_frequency_bins']} | {m['observed_parity_max_abs']:.2e} / {m['null_parity_max_abs']:.2e} | {m['elapsed_seconds']:.1f} |")
    first=records[0][1]
    lines += ['',f"Python：`{first['python']}`。本地逐源运行，最多{first['workers']}个工作进程，每进程数值库线程数为1。版本："+'；'.join(f"{k} {v}" for k,v in first['versions'].items())+'。','',
        '```bash','/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/detector_controls_2day_qpo.py',
        '# 只利用保存数组重新出图和生成报告，不重复模拟',
        '/Users/luoji/miniconda3/envs/py310/bin/python src/pipeline/detector_controls_2day_qpo.py --render-only','```','',
        '本报告的四张图片内嵌于HTML，可离线阅读；Markdown来源使用本地PNG相对路径。未发布外部网站，未提交Git。','']
    markdown=output.with_suffix('.md')
    markdown.write_text('\n'.join(lines),encoding='utf-8')
    renderer=Path.home()/'.agents/skills/notion-html-report/scripts/render_notion_report.py'
    subprocess.run([sys.executable,str(renderer),str(markdown.resolve()),'--output',str(output.resolve())],check=True)
    text=output.read_text()
    def embed(match):
        src=html.unescape(match.group(1))
        if src.startswith('data:'):
            return match.group(0)
        path=(output.parent/src).resolve()
        return 'src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"'
    text=re.sub(r'src="([^"]+)"',embed,text)
    text=text.replace('<table>','<div class="table-scroll" tabindex="0" role="region" aria-label="可横向滚动的数据表"><table>')
    text=text.replace('</table>','</table></div>')
    extra='''<style>
@media(min-width:1100px){.page-shell{grid-template-columns:176px minmax(0,1160px);gap:32px}}
.document{overflow-wrap:anywhere}.table-scroll{max-width:100%;overflow-x:auto;margin:16px 0}
.table-scroll table{margin:0;min-width:700px;overflow-wrap:normal}.table-scroll td{white-space:nowrap}
.doc-body figure img{cursor:zoom-in}.doc-body figure{margin:24px 0}
dialog.figure-zoom{width:98vw;max-width:98vw;height:94vh;max-height:94vh;padding:12px;border:1px solid #ddd;border-radius:8px}
dialog.figure-zoom::backdrop{background:rgba(0,0,0,.65)}
.zoom-toolbar{position:sticky;top:0;background:#fff;padding:8px;display:flex;justify-content:space-between;gap:12px;z-index:1}
.zoom-scroll{overflow:auto;max-height:calc(94vh - 75px)}.zoom-scroll img{max-width:none;width:auto;height:auto;display:block}
.zoom-toolbar button{font:inherit;cursor:pointer;padding:5px 12px}
</style>
<dialog class="figure-zoom" aria-label="原尺寸科学图"><div class="zoom-toolbar"><span>原尺寸查看，可横向滚动；Esc关闭</span><button type="button">关闭</button></div><div class="zoom-scroll"><img alt=""></div></dialog>
<script>
const zoom=document.querySelector('.figure-zoom');
for(const img of document.querySelectorAll('.doc-body figure img')){
 img.tabIndex=0;img.setAttribute('role','button');img.setAttribute('aria-label',img.alt+' 点击查看原尺寸');
 const open=()=>{zoom.querySelector('img').src=img.src;zoom.querySelector('img').alt=img.alt;zoom.showModal()};
 img.addEventListener('click',open);img.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}});
}
zoom.querySelector('button').addEventListener('click',()=>zoom.close());
</script>'''
    text=text.replace('</body>',extra+'\n</body>')
    output.write_text(text,encoding='utf-8')
    print(f'[REPORT] {output}',flush=True)
    return output
