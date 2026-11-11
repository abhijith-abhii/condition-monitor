#!/usr/bin/env python3
"""Build the editable report from versioned content and recorded evidence."""
import json,pathlib,statistics
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((ROOT/'docs/report-content.json').read_text())
metrics=json.loads((ROOT/'evidence/metrics.json').read_text())
soak=json.loads((ROOT/'evidence/extended-soak.json').read_text())
doc=Document();sec=doc.sections[0]
sec.top_margin=Inches(.65);sec.bottom_margin=Inches(.65);sec.left_margin=Inches(.72);sec.right_margin=Inches(.72)
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
styles=doc.styles
for key in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
 styles[key].font.name='Calibri';styles[key].font.color.rgb=RGBColor(0,0,0)
styles['Normal'].font.size=Pt(10.5);styles['Normal'].paragraph_format.space_after=Pt(7);styles['Normal'].paragraph_format.line_spacing=1.1
styles['Title'].font.size=Pt(25);styles['Title'].paragraph_format.space_after=Pt(8)
styles['Subtitle'].font.size=Pt(12);styles['Heading 1'].font.size=Pt(17);styles['Heading 2'].font.size=Pt(12.5)
styles['Heading 1'].paragraph_format.space_before=Pt(9)
footer=sec.footer.paragraphs[0];footer.alignment=2
r=footer.add_run('Embedded systems portfolio  |  ');r.font.size=Pt(8)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
markdown=['# '+m['title'],'',m['subtitle'],'']
def p(text,style=None):
 doc.add_paragraph(text,style);markdown.extend([text,''])
def h(text):doc.add_heading(text,1);markdown.extend(['## '+text,''])
def sub(text):doc.add_heading(text,2);markdown.extend(['### '+text,''])
def page(title):doc.add_page_break();h(title)
def picture(path,width=6.9):
 doc.add_picture(str(ROOT/path),width=Inches(width));markdown.extend(['!['+path+']('+(path[5:] if path.startswith('docs/') else '../'+path)+')',''])
def table(headers,rows,widths):
 t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
 for c,w in zip(t.columns,widths):c.width=Inches(w)
 for i,v in enumerate(headers):t.rows[0].cells[i].text=v
 for row in rows:
  for i,v in enumerate(row):t.add_row() if False else None
  cells=t.add_row().cells
  for i,v in enumerate(row):cells[i].text=str(v)
 for ri,row in enumerate(t.rows):
  for ci,cell in enumerate(row.cells):
   cell.width=Inches(widths[ci]);cell.vertical_alignment=1
   pr=cell._tc.get_or_add_tcPr();mar=OxmlElement('w:tcMar')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:w'),'90');e.set(qn('w:type'),'dxa');mar.append(e)
   pr.append(mar);borders=OxmlElement('w:tcBorders')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
   pr.append(borders);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'173B4B' if ri==0 else ('F0F5F7' if ri%2==0 else 'FFFFFF'));pr.append(sh)
   for para in cell.paragraphs:
    para.paragraph_format.space_after=Pt(2);para.paragraph_format.space_before=Pt(2);para.paragraph_format.line_spacing=1.0
    for run in para.runs:
     run.font.size=Pt(9);run.bold=ri==0;run.font.color.rgb=RGBColor(255,255,255) if ri==0 else RGBColor(0,0,0)
  if ri==0:
   repeat=OxmlElement('w:tblHeader');row._tr.get_or_add_trPr().append(repeat)
 p('')
 markdown.extend(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows]+[''])
def fmt(v):
 if v is None:return 'Not measured'
 if isinstance(v,int):return f'{v:,}'
 if abs(v)>0 and abs(v)<.0001:return f'{v:.3g}'
 return f'{v:,.4f}'.rstrip('0').rstrip('.')
p(m['title'],'Title');p(m['subtitle'],'Subtitle')
p('Engineering report  |  11 November 2026  |  AI-assisted implementation')
p(m['problem'])
p('Verified scope: portable C++ tests and deterministic simulations, host integration where applicable, and actual ESP32 cross-compilation. No board was flashed, sensor exercised, or physical measurement collected.')
h('Requirements and acceptance')
table(['ID','Target established before testing','Verification status'],m['requirements'],[.45,3.65,2.9])
p('Targets remain targets until their corresponding environment is tested. This report distinguishes synthetic behavior, host wall-clock execution and linker resource counts. Hardware timing, current, electrical recovery and watchdog reset remain pending.')
page('Hardware and wiring')
p('Target: classic ESP32-WROOM-32 DevKitC with 4 MB flash. One board can be reused across the three projects. Use the specified 3.3 V interfaces; WROVER pin availability differs.')
table(['Component','Qty','Planning cost'],m['bom'],[4.15,.45,2.4])
p('Sensor prices were observed on the cited supplier pages on 11 November 2026. Other costs are estimates in USD, excluding tax, shipping and measurement instruments.')
picture('docs/wiring.png',6.7)
p('Connection diagram names signal endpoints, not physical header positions. Consult the board silk screen. Use a common ground and short leads. Start with a low-voltage bench setup; industrial-voltage inputs need a suitable interface. See hardware.md for pin notes and instrument requirements.')
page('Firmware architecture and decisions')
picture('docs/architecture.png',6.8)
for text in m['decisions']:p(text)
sub('Ownership of the implementation')
p('Project code implements drivers, calculations, state machines, queue/parser policy, tests and tools. Arduino ESP32 provides the peripheral HAL and startup; ESP-IDF provides FreeRTOS, NVS, watchdog and sleep services. The environmental gateway uses SQLite transactions. Official GitHub drivers were studied as references; they were not copied into these custom headers.')
page('Testing and evidence')
table(['Requirement','Test or experiment','Result'],m['tests'],[.65,4.65,1.7])
p('Host tests compile the same portable headers used by target firmware. Strict compiler warnings, AddressSanitizer and UndefinedBehaviorSanitizer are enabled in separate test runs. Bus mocks validate transactions and selected faults; they do not reproduce analog behavior or peripheral timing.')
test=(ROOT/'evidence/tests.txt').read_text().strip();p(test)
p('Recorded extended loop: %.6f seconds and %s workload iterations. This is one short host stress run, not a field endurance qualification. Three additional approximately five-second repetitions provide throughput variability.'%(soak['duration_seconds'],f"{soak['iterations']:,}"))
if (ROOT/'evidence/gateway-tests.txt').exists():p('Five Python gateway integration tests passed, including actual subprocess restarts, real SQLite deduplication and failure to acknowledge when storage errors occur.')
p('Evidence is retained in tests.txt, sanitizers.txt, trace.csv, soak.json, extended-soak.json and build logs. test-matrix.csv maps requirements to results. Original failures remain in initial-tests.txt. No hardware test is marked passed on the strength of a simulation.')
page('Baseline and improved performance')
picture('evidence/benchmark.png',6.85)
selected=[x for x in metrics if x['id'] not in ['M08','M09','M10']]
table(['Metric','Baseline','Improved','Unit'],[[x['metric'],fmt(x['baseline']),fmt(x['final_result']),x['units']] for x in selected],[3.2,1.45,1.45,.9])
if m['id']=='condition-monitor':p('The improved rule removes DC sensitivity and rejects the five isolated bursts. That costs response time: the aligned sustained-step alarm moves from 0.32 to 0.96 seconds, an added 0.64 seconds. This is a useful tradeoff, not a claim that every metric improved. The test does not establish real machine detection accuracy.')
elif m['id']=='environment-logger':p('On the same 120-wake trace, delivery rises from 100 to 120 records: 16.67 percentage points, or 20 percent more delivered records relative to baseline. Reliability introduces 17 duplicate received frames when ACKs are lost. Deduplication preserves one database record per identity. Longer outages can still overflow the queue.')
else:p('Mean normalization error falls from 360 to 0 RPM on the phase-aligned synthetic trace. The zero is specific to the constructed input and elapsed-time arithmetic; it is not a physical RPM accuracy claim. Stall appears 2.0 simulated seconds after the final pulse. Real low-speed quantization and scheduling jitter remain.')
page('Measurement definitions and limitations')
for metric in selected:
 sub(metric['id']+' '+metric['metric'])
 p('Definition: '+metric['definition']+'. Method: '+metric['measurement_method']+'. Workload: '+metric['workload']+'. Samples: '+metric['sample_count_or_duration']+'.')
 p('Environment: deterministic host simulation of shared C++ logic. Baseline: '+fmt(metric['baseline'])+'; improved: '+fmt(metric['final_result'])+' '+metric['units']+'. Limits: '+metric['limitations']+'.')
sub('Resource counts and host execution')
for metric in [x for x in metrics if x['id'] in ['M08','M09','M10']]:
 p(metric['id']+' '+metric['metric']+': '+fmt(metric['final_result'])+' '+metric['units']+'. '+metric['measurement_method']+'. '+metric['sample_count_or_duration']+'. Baseline: not measured. '+metric['limitations']+'.')
p('Target build: Xtensa GCC 8.4.0, Arduino ESP32 2.0.17 and PlatformIO Espressif platform 6.9.0. Host: '+metrics[0]['environment']+'. The complete nine-field metric records and machine-readable values are in evidence/metrics.csv and metrics.json. Physical latency, stack use, CPU load, current and battery life are not reported as measured.')
page('Failures recovery and remaining risks')
sub('Observed failures and review fixes');p(m['failures'])
sub('Current limitations');p(m['limitations'])
sub('Hardware acceptance experiments')
for i,text in enumerate(m['experiments']):p(str(i+1)+'. '+text)
p('The engineering-review.md companion records resource budgets, failure modes and release gates. A change should update its requirements, test matrix and comparison trace together; preserve the original workload so before/after values remain comparable.')
page('Reproduce demonstrate and explain')
p('Prerequisites: C++17 compiler, Python 3.9 or later, and a terminal. The simulation and C++ tests require no board or paid service. From the project directory:')
for line in ['sh tools/test.sh','sh tools/sanitize.sh','sh tools/simulate.sh > evidence/trace.csv','python3 -m venv .venv','.venv/bin/pip install -r tools/requirements.txt','.venv/bin/python tools/benchmark.py --rerun','.venv/bin/python tools/figures.py','.venv/bin/pio run -e esp32dev -e simulated']:
 para=doc.add_paragraph();run=para.add_run(line);run.font.name='Consolas';run.font.size=Pt(9);para.paragraph_format.space_after=Pt(3);markdown.extend(['    '+line])
p('On Windows, activate the virtual environment and use its Scripts executables; run shell scripts through WSL or a compatible shell. Flash only when the matching board is attached: pio run -e esp32dev -t upload --upload-port PORT. Use pio device monitor --port PORT -b 115200. The simulated firmware environment generates inputs on a physical ESP32; the host simulator runs on the computer.')
sub('Demonstration sequence')
for i,text in enumerate(m['demo']):p(str(i+1)+'. '+text)
p('The mentor-guide.md companion contains a beginner explanation, code walkthrough, ten interview questions with answers, independent exercises and three evidence-based resume bullets. Development was AI-assisted; no independent hardware work or production deployment experience is implied.')
sub('Primary references')
refs=[('ADXL345 Rev G datasheet','https://www.analog.com/media/en/technical-documentation/data-sheets/adxl345.pdf'),('SHT3x DIS version 7 datasheet','https://sensirion.com/media/documents/213E6A3B/63A5A569/Datasheet_SHT3x_DIS.pdf'),('ESP32 DevKitC guide','https://docs.espressif.com/projects/esp-idf/en/v4.4.7/esp32/hw-reference/esp32/get-started-devkitc.html'),('ESP32 watchdog API','https://docs.espressif.com/projects/esp-idf/en/v4.4.7/esp32/api-reference/system/wdts.html'),('Pinned platform definition','https://github.com/platformio/platform-espressif32/blob/v6.9.0/platform.json')]
for title,url in refs:
 para=doc.add_paragraph(title+'\n'+url);para.paragraph_format.space_after=Pt(5)
 for r in para.runs:r.font.size=Pt(8)
 markdown.extend([title+': '+url,''])
p('See references.md for the pinned GitHub driver study, supplier links and implementation attribution.')
# Remove inherited Word template paragraph borders, especially the Title rule.
for part in [doc.styles.element,doc.element]:
 for border in list(part.xpath('.//w:pBdr')):border.getparent().remove(border)
output=ROOT/'docs/technical-report.docx';doc.save(output)
(ROOT/'docs/technical-report.md').write_text('\n'.join(markdown)+'\n')
print(output)
