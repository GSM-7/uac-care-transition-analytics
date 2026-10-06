const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, LevelFormat, BorderStyle, PageBreak } = require('docx');

const W = 9026; // A4 content width in DXA with 1" margins
const P = (t, o = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, ...o,
  children: Array.isArray(t) ? t : [new TextRun(t)] });
const B = (t) => new TextRun({ text: t, bold: true });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (t) => new Paragraph({ numbering: { reference: 'b', level: 0 }, spacing: { after: 80 },
  children: Array.isArray(t) ? t : [new TextRun(t)] });
const img = (f, w, h, cap) => [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 }, keepNext: true,
    children: [new ImageRun({ type: 'png', data: fs.readFileSync('figures/' + f), transformation: { width: w, height: h },
      altText: { title: cap, description: cap, name: f } })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: cap, italics: true, size: 18, color: '555555' })] })];
const bd = { style: BorderStyle.SINGLE, size: 4, color: 'BBBBBB' };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
function table(cols, rows, widths) {
  const mk = (t, i, head) => new TableCell({ borders, width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { fill: '1F4E79', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: String(t), bold: head, size: 18, color: head ? 'FFFFFF' : '000000' })] })] });
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: cols.map((c, i) => mk(c, i, true)) }),
      ...rows.map(r => new TableRow({ children: r.map((c, i) => mk(c, i, false)) }))] });
}
const styles = {
  default: { document: { run: { font: 'Calibri', size: 22 } } },
  paragraphStyles: [
    { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { size: 30, bold: true, color: '1F4E79' }, paragraph: { spacing: { before: 300, after: 140 }, outlineLevel: 0 } },
    { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { size: 25, bold: true, color: '2E75B6' }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } }]
};
const numbering = { config: [{ reference: 'b', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•',
  alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] };
const page = { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } };
const title = (t, s) => [
  new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: t, bold: true, size: 40, color: '1F4E79' })] }),
  new Paragraph({ spacing: { after: 240 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: '1F4E79', space: 4 } },
    children: [new TextRun({ text: s, size: 22, color: '555555' })] })];

// =========================== RESEARCH PAPER ===========================
const paper = [
  ...title('Care Transition Efficiency & Placement Outcome Analytics',
    'A process-efficiency analysis of the HHS Unaccompanied Children Program, Jan 2023 – Dec 2025'),
  P([B('Author: '), new TextRun('[Your name]   '), B('Course/Program: '), new TextRun('[Your course]   '), B('Date: '), new TextRun('6 October 2026')]),

  H1('Abstract'),
  P('The Unaccompanied Children (UAC) Program is usually monitored through headcounts. This paper instead treats it as a three-stage pipeline (CBP custody → HHS care → sponsor placement) and measures how efficiently children move through it. Using 720 reporting days from 12 January 2023 to 21 December 2025, we derive five KPIs: Transfer Efficiency Ratio, Discharge Effectiveness, Pipeline Throughput, Backlog Accumulation Rate and Outcome Stability Score.'),
  P('Three findings stand out. (1) The HHS census fell from a peak of 11,516 (20 Dec 2023) to a trough of 1,972 (21 Aug 2025), but this was driven mainly by collapsing intake, not faster placement: the share of the HHS population discharged per report fell from 2.9% in 2024 to 1.1% in 2025, implying that children now take roughly 2.6 times longer to turn over. (2) In 2024, four sustained imbalance periods (up to 61 consecutive reports) saw transfers outrun discharges and added about 2,500 children to the HHS census. (3) Outcome stability dropped from about 77/100 in 2023–24 to 55/100 in 2025, with two abrupt discharge collapses in February and March 2025. We also document that the data do not fully reconcile (HHS census changes track transfers minus discharges with r = 0.22), a limitation that matters for any process-level policy conclusion. We close with recommendations and a live Streamlit dashboard.'),

  H1('1. Introduction'),
  P('Aggregate counts show how many children are in custody, but not whether the system is working. A census of 2,000 children could mean a healthy, fast-moving pipeline or a stalled one. Policy-relevant questions therefore concern flow: how quickly children leave CBP custody, whether discharges keep pace with inflows, where backlogs accumulate, and whether placement outcomes are improving.'),
  P('The objectives of this project are to (i) measure the efficiency of CBP→HHS transitions, (ii) evaluate discharge and sponsor-placement outcomes, and (iii) identify delays and bottlenecks. Secondary objectives are to support faster reunification and to inform process reform.'),

  H1('2. Data and Methods'),
  H2('2.1 Dataset'),
  P('The dataset contains daily-reported counts for: children apprehended and placed in CBP custody, children in CBP custody, children transferred out of CBP, children in HHS care, and children discharged from HHS care. The raw file has 1,170 rows, of which 450 are empty trailing rows. After removing them, converting comma-formatted numbers (e.g. "2,484") and sorting chronologically, 720 valid, non-duplicate reports remain (12 Jan 2023 – 21 Dec 2025). No negative values or missing values remain.'),
  H2('2.2 Data quality observations'),
  bullet([B('Reports are not daily. '), new TextRun('There are about five reports per week with gaps of up to 10 days. 558 of 719 intervals are one day, 151 follow a gap of three or more days. Metrics are therefore expressed per report, not per calendar day.')]),
  bullet([B('No Friday/Saturday records. '), new TextRun('Only Sunday–Thursday dates appear (two Friday rows). A true weekday-versus-weekend comparison is impossible; we compare reports after a 3+ day gap with consecutive-day reports instead. The date labels may be offset by one day relative to the original reporting calendar.')]),
  bullet([B('Stocks and flows do not reconcile. '), new TextRun('On the 558 consecutive-day intervals, the change in HHS census correlates only r = 0.22 with transfers minus discharges, and the census rose faster than reported net flow in 76% of cases (mean excess +68 children per report). This suggests children enter HHS care through routes not captured in the CBP-transfer column, or that counts are timed differently.')]),
  bullet([B('Transfers exceed CBP intake. '), new TextRun('Total transfers (92,641) are 1.38 times total recorded apprehensions (67,337), reinforcing the same point. End-to-end throughput above 1 should therefore not be read as "better than perfect".')]),
  bullet([B('Aggregate only. '), new TextRun('Without individual-level records we cannot measure length of stay directly; we use the implied turnover time (1 ÷ discharge effectiveness) as a proxy.')]),
  H2('2.3 KPI definitions'),
  table(['KPI', 'Definition', 'Interpretation'], [
    ['Transfer Efficiency Ratio (TER)', 'Transfers out of CBP ÷ children in CBP custody', 'Turnover of CBP custody; can exceed 1 (12% of reports) because custody is a point-in-time count'],
    ['Discharge Effectiveness (DE)', 'Discharges ÷ children in HHS care', 'Share of the HHS population placed per report; its inverse is the implied turnover time'],
    ['Pipeline Throughput', 'Exits ÷ entries, by stage and end-to-end', '>1 means exits exceed recorded entries'],
    ['Backlog Accumulation Rate', 'Mean (transfers − discharges) per report', 'Positive = children piling up in HHS care'],
    ['Outcome Stability Score', '100 × (1 − CV of DE), 30-report rolling window', 'Higher = more consistent placements']],
    [2300, 3300, 3426]),
  P('', { spacing: { after: 60 } }),
  P('Rolling metrics use a 7-report window with ratio-of-sums weighting. A "sustained imbalance" is a run of at least 14 reports in which the 7-report mean net flow into HHS is positive. A "stagnation period" is a run of at least 10 reports in which 7-report DE sits in its bottom quartile. A "sudden drop" is a fall of at least 35% in 7-report mean DE relative to the preceding 7 reports.'),

  H1('3. Results'),
  H2('3.1 The pipeline: stock and flow'),
  P('The HHS census rose from about 7,400 in early 2023 to a peak of 11,516 on 20 December 2023, declined through 2024, and fell sharply in early 2025 to around 2,000–2,500, where it has stayed. CBP custody and intake followed the same pattern: monthly intake dropped from 2,000–4,500 in 2024 to roughly 70–220 in mid-2025.'),
  ...img('fig1_census.png', 600, 390, 'Figure 1. Children in HHS care (top) and in CBP custody with 7-report average intake (bottom).'),
  ...img('fig2_flows.png', 600, 255, 'Figure 2. Flows between stages (14-report moving average).'),
  table(['Year', 'Apprehended', 'Transferred', 'Discharged', 'TER', 'DE (%)', 'Backlog rate', 'Stability'], [
    ['2023', '27,056', '36,124', '66,244', '0.78', '3.33', '−131.0', '77.7'],
    ['2024', '37,166', '52,552', '51,689', '0.76', '2.92', '+3.4', '77.1'],
    ['2025', '3,115', '3,965', '6,920', '0.50', '1.14', '−12.4', '54.9'],
    ['All', '67,337', '92,641', '124,853', '0.75', '2.86', '−44.7', '69.8']],
    [900, 1250, 1250, 1250, 800, 900, 1300, 1376]),
  P('Table 1. Annual KPIs (backlog rate in children per report; negative = HHS census shrinking).', { spacing: { before: 60, after: 200 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Table 1. Annual KPIs (backlog rate in children per report; negative = HHS census shrinking).', italics: true, size: 18, color: '555555' })] }),

  H2('3.2 Transfer efficiency (CBP → HHS)'),
  P('Transfer efficiency was steady at 0.78 in 2023 and 0.76 in 2024, then fell to 0.50 in 2025. In 2025, CBP custody is small (monthly average of roughly 14–36 children), so ratios are noisier, but the decline is consistent across the year: the latest report (21 Dec 2025) shows 0.23, below our default alert level of 0.50. A low ratio here means children stay in CBP custody longer relative to the number held. Because CBP custody is very small, the absolute humanitarian impact of the slowdown at this stage is small compared with the HHS-stage effect below, but it signals that the transfer step is also less responsive than in earlier years.'),
  ...img('fig3_efficiency.png', 600, 375, 'Figure 3. Transfer Efficiency Ratio (top) and Discharge Effectiveness (bottom).'),

  H2('3.3 Discharge effectiveness and placement outcomes'),
  P('Discharge effectiveness fell from 3.33% (2023) to 2.92% (2024) to 1.14% (2025). Inverting these gives an implied turnover time of about 30, 34 and 88 reporting days respectively, so the HHS population now turns over about 2.6 times more slowly than in 2024. Because the census stabilised around 2,000–2,500 while intake collapsed, the system is holding a small, slow-moving population rather than clearing it. Prolonged low-discharge periods confirm this: 16 March – 1 July 2025 (71 reports, mean DE 0.45%) and 21 July – 21 December 2025 (106 reports, mean DE 0.52%).'),
  P('Monthly absolute discharges per reporting day fell from roughly 300–350 in late 2023 to under 30 from March 2025 onward (Figure 5), consistent with the smaller caseload, but the relative measure (DE) shows that the fall is more than proportional to the shrinking census.'),
  ...img('fig5_monthly.png', 600, 248, 'Figure 5. Average discharges per reporting day, by month.'),

  H2('3.4 Backlog and bottleneck identification'),
  P('Eight sustained-imbalance periods were found (Figure 4). The four most significant all fall in 2024, when intake was highest and discharges failed to keep pace:'),
  table(['Period', 'Reports', 'Avg net flow / report', 'HHS census change'], [
    ['6 Feb – 14 Mar 2024', '27', '+51.2', '+650 (8,045 → 8,695)'],
    ['21 Apr – 13 Jun 2024', '39', '+46.4', '+799 (6,745 → 7,544)'],
    ['20 Aug – 13 Sep 2024', '16', '+43.1', '+331 (5,995 → 6,326)'],
    ['30 Sep – 26 Dec 2024', '61', '+31.9', '+740 (5,967 → 6,707)']],
    [2900, 1300, 2300, 2526]),
  P('Table 2. Largest sustained imbalance periods.', { spacing: { before: 60, after: 160 }, alignment: AlignmentType.CENTER, children: [new TextRun({ text: 'Table 2. Largest sustained imbalance periods.', italics: true, size: 18, color: '555555' })] }),
  P('Together these four periods account for roughly 2,500 additional children in HHS care. The four 2025 periods are far milder (+1.6 to +3.7 children per report). By contrast 2023 shows sustained net drawdown (−131 per report), meaning discharges exceeded transfers as the post-peak census was worked down. The CBP stage, by comparison, almost never accumulates a backlog: average intake minus transfers is negative in all three years, so the bottleneck is the HHS discharge stage, not the CBP-to-HHS handoff.'),
  ...img('fig4_backlog.png', 600, 375, 'Figure 4. HHS backlog accumulation rate (red shading = sustained imbalance) and cumulative net flow.'),

  H2('3.5 Temporal patterns'),
  P('Discharges are uneven across reporting weekdays: Sunday and Thursday are the strongest (mean about 206 per report; DE 3.5% and 3.4%), Tuesday the weakest (136; DE 2.2%). Reports that follow a 3+ day gap show higher discharges than reports 1–2 days after the previous one (201 vs 166 per report; DE 3.35% vs 2.72%), which is consistent with batching of placements around non-reporting days, but we stress that with no Friday/Saturday data this cannot be called a weekend effect. Transfer efficiency varies much less (0.72–0.78). Month-over-month, discharges per reporting day are volatile (Figure 5) and track the census more than any seasonal pattern.'),
  ...img('fig7_weekday.png', 450, 225, 'Figure 7. Mean discharges by reporting weekday.'),

  H2('3.6 Outcome stability'),
  P('The Outcome Stability Score averaged 77.7 in 2023 and 77.1 in 2024 but 54.9 in 2025. Three sudden-drop episodes were detected: 25 February 2025 (7-report DE down 69%, from 2.9% to 0.9%), 23 March 2025 (down 75%, from 1.2% to 0.3%) and 21 October 2025 (down 37%). The first two coincide with the census falling to about 2,100–2,400 and the start of the long stagnation period in Section 3.3, i.e. placements slowed abruptly rather than gradually. One reporting day recorded zero discharges.'),
  ...img('fig6_stability.png', 600, 240, 'Figure 6. Outcome Stability Score; dashed lines mark sudden-drop episodes.'),

  H1('4. Discussion'),
  P('The headline story of a shrinking system hides a deterioration in process quality. In 2023 the system cleared a very large census quickly (DE above 3%). In 2024, as intake rose again, discharges did not scale and backlogs grew in four sustained episodes. In 2025, intake fell by about 90%, yet children are discharged more slowly relative to the census than at any earlier point and outcomes are less predictable. This pattern is consistent with a system whose placement step is constrained by factors other than caseload (sponsor vetting and verification requirements, case-management capacity, or policy changes) rather than by volume, though the dataset cannot identify the cause.'),
  H2('Limitations'),
  bullet('Aggregate counts only: no length-of-stay, sponsor type, or outcome quality, so "efficiency" means flow speed, not case quality or child safety.'),
  bullet('Stocks and flows do not reconcile, suggesting unobserved entry routes into HHS care; backlog estimates from (transfers − discharges) are therefore lower bounds.'),
  bullet('Irregular reporting (5 of 7 days, gaps up to 10 days) and a possible date-label offset limit weekday analysis.'),
  bullet('2025 volumes are small, so ratios there are inherently noisier; we describe consistent patterns, not individual-day swings.'),
  bullet('The analysis is descriptive. Causal explanations (policy changes, sponsor vetting rules) are hypotheses for follow-up, not findings.'),

  H1('5. Recommendations'),
  bullet([B('Track flow KPIs routinely. '), new TextRun('Publish DE, backlog rate and implied turnover time alongside headcounts; the dashboard provides threshold alerts (e.g. DE below 1%, backlog above +25 per report).')]),
  bullet([B('Trigger a surge response on sustained imbalance. '), new TextRun('When the 7-report net flow stays positive for about two weeks, add discharge-side capacity (case managers, sponsor-vetting staff), as the 2024 episodes showed backlogs of 30–50 children per report building for 1–3 months.')]),
  bullet([B('Investigate the 2025 slowdown. '), new TextRun('Review the February–March 2025 discharge collapses and the two long low-discharge periods with case-level data to determine whether sponsor verification, staffing or policy change is responsible.')]),
  bullet([B('Fix data reconciliation. '), new TextRun('Report all entry routes into HHS care, publish seven-day data, and add length-of-stay and sponsor-category fields so process delay can be measured directly.')]),
  bullet([B('Monitor placement stability. '), new TextRun('Use the Outcome Stability Score as an early-warning indicator; a fall below about 50 should prompt review.')]),

  H1('6. Conclusion'),
  P('Viewed as a pipeline, the UAC program shows a clear pattern: the CBP-to-HHS handoff is comparatively smooth, whereas the HHS discharge stage is where backlogs accumulate (2024) and where performance has deteriorated most (2025). Flow-based KPIs reveal this where headcounts do not. The accompanying Streamlit application lets stakeholders explore any date range, adjust thresholds and monitor these metrics going forward. Future work should add individual-level length-of-stay data and test causal explanations for the 2025 slowdown.'),
  H1('Appendix: Reproducibility'),
  P('All code (uac_metrics.py, analysis.py, app.py) and the cleaned-data pipeline are in the project repository. Running python analysis.py regenerates every figure and number in this paper; streamlit run app.py launches the dashboard.'),
];

// =========================== EXECUTIVE SUMMARY ===========================
const exec = [
  ...title('Executive Summary', 'UAC Care Transition Efficiency & Placement Outcome Analytics · Jan 2023 – Dec 2025'),
  P([B('Purpose. '), new TextRun('Headcounts show how many children are in care, not whether the system is moving them to sponsors efficiently. This analysis measures process flow across the pipeline: CBP custody → HHS care → sponsor placement.')]),
  H2('Key findings'),
  bullet([B('The shrinking caseload is not the whole story. '), new TextRun('The HHS census fell from 11,516 (Dec 2023) to about 2,000–2,500 in 2025, but mainly because intake dropped about 90%. The share of children discharged per report fell from 2.9% (2024) to 1.1% (2025): children now turn over about 2.6 times more slowly.')]),
  bullet([B('The bottleneck is discharge, not transfer. '), new TextRun('Transfers out of CBP kept pace with intake in every year. In 2024, four sustained periods (16–61 consecutive reports) saw transfers outrun discharges, adding about 2,500 children to HHS care.')]),
  bullet([B('Placements became less stable in 2025. '), new TextRun('The Outcome Stability Score fell from about 77 to 55 out of 100, with abrupt discharge collapses on 25 Feb and 23 Mar 2025 and two long low-discharge periods (Mar–Jul and Jul–Dec 2025).')]),
  bullet([B('Transfer efficiency is slipping. '), new TextRun('The ratio of transfers to CBP custody fell from about 0.76–0.78 to 0.50 in 2025 (0.23 on the latest report).')]),
  H2('KPI snapshot'),
  table(['KPI', '2023', '2024', '2025'], [
    ['Transfer Efficiency Ratio', '0.78', '0.76', '0.50'],
    ['Discharge Effectiveness (% of HHS care per report)', '3.33%', '2.92%', '1.14%'],
    ['Backlog rate (children/report, + = building)', '−131', '+3.4', '−12'],
    ['Outcome Stability Score (0–100)', '77.7', '77.1', '54.9']], [4426, 1500, 1500, 1600]),
  H2('Recommended actions'),
  bullet('Adopt flow KPIs (discharge effectiveness, backlog rate, stability score) in routine reporting, with alert thresholds.'),
  bullet('Define a surge trigger: two weeks of net inflow to HHS above exits should prompt added case-management and sponsor-vetting capacity.'),
  bullet('Review the 2025 discharge slowdown using case-level data to identify whether sponsor verification, staffing or policy changes are the cause.'),
  bullet('Improve data: publish seven-day reports, all HHS entry routes, length of stay and sponsor category.'),
  H2('Caveats'),
  P('Data are aggregate counts with irregular reporting (about five reports a week) and do not fully reconcile between stocks and flows; findings describe flow speed, not case quality or child safety, and causes are hypotheses for follow-up. Full methods, figures and limitations are in the research paper; a live dashboard allows any date range and threshold to be explored.'),
];

const mk = (children, footer) => new Document({ styles, numbering,
  sections: [{ properties: { page }, children }] });
Packer.toBuffer(mk(paper)).then(b => fs.writeFileSync('docs/Research_Paper_UAC_Care_Transition_Analytics.docx', b));
Packer.toBuffer(mk(exec)).then(b => fs.writeFileSync('docs/Executive_Summary_UAC.docx', b));
