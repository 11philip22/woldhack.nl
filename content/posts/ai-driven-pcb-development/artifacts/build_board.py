"""Build the separately powered Blue Pill USB VBUS switch with KiCad 10."""
from pathlib import Path
from uuid import UUID, uuid5
import json
import math
import re
import csv
import pcbnew as p

ROOT = Path(__file__).resolve().parent
LIB = Path(r'C:\Program Files\KiCad\10.0\share\kicad')
if not LIB.exists():
    LIB = Path('/usr/share/kicad')
NAME = 'bluepill-vbus-switch'
SHEET = 'a09bd7b1-c8b5-42a8-89ad-41facbfb974f'
project_path = ROOT / f'{NAME}.kicad_pro'
project = json.loads(project_path.read_text(encoding='utf-8'))
project['erc']['rule_severities'].pop('isolated_pin_label', None)
rules = project['board']['design_settings']['rules']
rules.update(min_clearance=0.15, min_track_width=0.2, min_silk_clearance=0.1)
project['net_settings']['classes'][0]['clearance'] = 0.18
project['board']['design_settings']['diff_pair_dimensions'] = [
    {'width': 0.28, 'gap': 0.18, 'via_gap': 0.25}]

def uid(name):
    return str(uuid5(UUID(SHEET), name))

def xy(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))

def layers(*ids):
    result=p.LSET()
    for layer in ids: result.AddLayer(layer)
    return result

def native_symbol(library, name):
    source = (LIB / f'symbols/{library}.kicad_sym').read_text(encoding='utf-8')
    return re.search(r'\n\t\(symbol "' + re.escape(name) + r'"\n.*?(?=\n\t\(symbol |\n\)$)', source, re.S).group().strip()

# Pin definitions: number, name, electrical type, x, y, angle in symbol coordinates.
symbols = {}
pin_defs = {}

def block(name, pins, halfwidth=10.16, halfheight=10.16):
    pin_defs[name] = pins
    symbols[name] = f'''(symbol "{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 {halfheight+2.54} 0) (effects (font (size 1.27 1.27))))
      (property "Value" "{name}" (at 0 {-halfheight-2.54} 0) (effects (font (size 1.27 1.27))))
      (symbol "{name}_0_1" (rectangle (start {-halfwidth} {halfheight}) (end {halfwidth} {-halfheight})
       (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "{name}_1_1" ''' + '\n'.join(
        f'''(pin {kind} line (at {x} {y} {angle}) (length 5.08)
          (name "{label}" (effects (font (size 1.016 1.016))))
          (number "{num}" (effects (font (size 1.016 1.016)))))'''
        for num, label, kind, x, y, angle in pins) + '))'

bp = {
    'J1': 'VBAT PC13 PC14 PC15 PA0 PA1 PA2 PA3 PA4 PA5 PA6 PA7 PB0 PB1 PB10 PB11 NRST 3V3 GND GND'.split(),
    'J2': '3V3 GND 5V PB9 PB8 PB7 PB6 PB5 PB4 PB3 PA15 PA12 PA11 PA10 PA9 PA8 PB15 PB14 PB13 PB12'.split(),
}
for ref in bp:
    block('BluePill_' + ref, [(str(n), label, 'passive', -12.7, round(24.13-(n-1)*2.54, 4), 0)
                             for n, label in enumerate(bp[ref], 1)], 7.62, 26.67)
for name, count in [('USB_Male', 5), ('USB_Female', 6)]:
    labels = ['VBUS', 'D-', 'D+', 'GND', 'SHIELD', 'SHIELD']
    block(name, [(str(n), labels[n-1], 'passive', -15.24, 7.62-(n-1)*3.81, 0)
                 for n in range(1, count+1)], 10.16, 13.97)
block('TPS2552DBVR', [
    ('1','IN','power_in',-15.24,7.62,0), ('2','GND','power_in',-15.24,-7.62,0),
    ('3','~{EN}','input',-15.24,0,0), ('4','~{FAULT}','open_collector',15.24,-7.62,180),
    ('5','ILIM','passive',15.24,0,180), ('6','OUT','power_out',15.24,7.62,180)])
for library, name in [('Device','R'),('Device','C'),('Device','C_Polarized'),
                      ('Transistor_FET','Q_NMOS_GSD'),('power','PWR_FLAG')]:
    src = native_symbol(library, name)
    symbols[name] = src
    pins = []
    for pin in re.finditer(r'\(pin (\w+) \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\).*?\(name "([^"]*)".*?\(number "([^"]*)"', src, re.S):
        kind, x, y, angle, label, num = pin.groups()
        pins.append((num, label, kind, float(x), float(y), int(float(angle))))
    pin_defs[name] = pins

# One component list drives the schematic, PCB net assignment and BOM.
parts = {}
def component(ref, symbol, value, footprint, nets, sch, pcb=None, lcsc='', mpn=''):
    parts[ref] = dict(symbol=symbol, value=value, footprint=footprint, nets=nets,
                      sch=sch, pcb=pcb, lcsc=lcsc, mpn=mpn or value)

socket = 'Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical'
component('J1','BluePill_J1','Blue Pill socket A',socket,
          {'5':'VBUS_ON','19':'GND','20':'GND'}, (48.26,62.23), (150.63,83.88,-90),'C2905423','KH-2.54FH-1X20P-H8.5')
component('J2','BluePill_J2','Blue Pill socket B',socket,
          {'2':'GND'}, (104.14,62.23), (150.63,99.12,-90),'C2905423','KH-2.54FH-1X20P-H8.5')
component('J3','USB_Male','USB-212-BCW','USBParts:USB-A-SMD_USB-212-BCW',
          dict(zip('12345',['VBUS_IN','USB_D-','USB_D+','GND','GND'])), (48.26,137.16),
          (103.42,114.5,-90),'C720521')
component('J4','USB_Female','AF180QT1.0','USBParts:AF180QT1.0_verified',
          dict(zip('123456',['VBUS_OUT','USB_D-','USB_D+','GND','GND','GND'])), (241.3,137.16),
          (139.05,114.5,90),'C404963')
component('U1','TPS2552DBVR','TPS2552DBVR','Package_TO_SOT_SMD:SOT-23-6',
          {'1':'VBUS_IN','2':'GND','3':'SW_EN_N','5':'ILIM','6':'VBUS_OUT'}, (157.48,137.16),
          (122,121,0),'C46506')
component('Q1','Q_NMOS_GSD','2N7002','Package_TO_SOT_SMD:SOT-23',
          {'1':'GATE','2':'GND','3':'SW_EN_N'}, (165.1,60.96), (116,121,0),'C124475')
RFP = 'Resistor_SMD:R_0603_1608Metric'
CFP = 'Capacitor_SMD:C_0603_1608Metric'
component('R1','R','100k',RFP,{'1':'VBUS_IN','2':'SW_EN_N'},(180.34,38.1),(119,124,0),'C25803','0603WAF1003T5E')
component('R2','R','100k',RFP,{'1':'GATE','2':'GND'},(144.78,76.2),(112.5,121,90),'C25803','0603WAF1003T5E')
component('R3','R','1k',RFP,{'1':'VBUS_ON','2':'GATE'},(127,55.88),(112.5,124,0),'C21190','0603WAF1001T5E')
component('R4','R','43k 1%',RFP,{'1':'ILIM','2':'GND'},(185.42,154.94),(125,124,0),'C23172','0603WAF4302T5E')
component('R5','R','1k',RFP,{'1':'VBUS_OUT','2':'GND'},(210.82,154.94),(127,118,90),'C21190','0603WAF1001T5E')
component('C1','C','100n 50V',CFP,{'1':'VBUS_IN','2':'GND'},(88.9,154.94),(119,118,90),'C14663','CC0603KRX7R9BB104')
component('C2','C','100n 50V',CFP,{'1':'VBUS_OUT','2':'GND'},(200.66,121.92),(125,118,90),'C14663','CC0603KRX7R9BB104')
component('C3','C_Polarized','150u 35V','Capacitor_SMD:CP_Elec_6.3x7.7',
          {'1':'VBUS_OUT','2':'GND'},(111.76,154.94),(132,121,0),'C249984','VZT151M1VTR-0607')
component('#FLG01','PWR_FLAG','PWR_FLAG','',{'1':'VBUS_IN'},(88.9,119.38))
component('#FLG02','PWR_FLAG','PWR_FLAG','',{'1':'GND'},(104.14,119.38))

# Fully embedded project symbols also have a library for future editing.
local_library = ['(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")']
local_library += list(symbols.values())
local_library.append(')')
(ROOT / 'library/Board.kicad_sym').write_text('\n'.join(local_library),encoding='utf-8')
embedded = [s.replace(f'(symbol "{name}"',f'(symbol "Board:{name}"',1) for name,s in symbols.items()]
sch = [f'''(kicad_sch (version 20260306) (generator "eeschema")
 (uuid {SHEET}) (paper "A4")
 (title_block (title "Blue Pill - USB VBUS switch") (date "2026-09-20") (rev "2.0")
 (comment 1 "53 x 46 mm | external Blue Pill power | USB data pass-through"))
 (lib_symbols {' '.join(embedded)})''']
for ref, part in parts.items():
    x,y = part['sch']
    name = part['symbol']
    extent = 31.75 if name.startswith('BluePill') else 19.05 if name.startswith('USB') else 13.97 if name=='TPS2552DBVR' else 5.08
    side_fields=name in ('R','C','C_Polarized','Q_NMOS_GSD')
    field_x=x+(7.62 if name=='Q_NMOS_GSD' else 3.81) if side_fields else x
    sch.append(f'''(symbol (lib_id "Board:{name}") (at {x} {y} 0) (unit 1)
      (in_bom {'no' if ref.startswith('#') else 'yes'}) (on_board {'no' if ref.startswith('#') else 'yes'})
      (dnp no) (uuid {uid(ref)})
      (property "Reference" "{ref}" (at {field_x} {y-1.27 if side_fields else y-extent} 0) (effects (font (size 1.27 1.27)) {'(justify left)' if side_fields else ''} {'(hide yes)' if ref.startswith('#') else ''}))
      (property "Value" "{part['value']}" (at {field_x} {y+1.27 if side_fields else y+extent} 0)
       (effects (font (size 1.016 1.016)) {'(justify left)' if side_fields else ''} {'(hide yes)' if ref.startswith('#') else ''}))
      (property "Footprint" "{part['footprint']}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))
      (property "LCSC" "{part['lcsc']}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))
      (property "Datasheet" "{'https://www.lcsc.com/product-detail/'+part['lcsc']+'.html' if part['lcsc'] else ''}" (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))
      (instances (project "{NAME}" (path "/{SHEET}" (reference "{ref}") (unit 1)))))''')
    for num,label,kind,dx,dy,angle in pin_defs[name]:
        px,py=round(x+dx,4),round(y-dy,4)
        net=part['nets'].get(num)
        if not net:
            sch.append(f'(no_connect (at {px} {py}) (uuid {uid(ref+num+"NC")}))')
            continue
        a=math.radians(angle)
        lx,ly=round(px-5.08*math.cos(a),4),round(py+5.08*math.sin(a),4)
        sch.append(f'''(wire (pts (xy {px} {py}) (xy {lx} {ly})) (stroke (width 0) (type default)) (uuid {uid(ref+num+'wire')}))
          (label "{net}" (at {lx} {ly} 0) (effects (font (size 1.016 1.016)) (justify {'right' if angle==0 else 'left'} bottom)) (uuid {uid(ref+num+'label')}))''')
for x,y,msg,size in [
    (25.4,15.24,'BLUE PILL SOCKETS - POWER THROUGH MODULE MICRO-USB',1.524),
    (25.4,102.87,'Only PA0 and ground connect to the carrier circuit. Module 5V / 3V3 stay separate.',1.27),
    (124.46,25.4,'PA0 HIGH = VBUS ON; LOW / floating = OFF',1.27),
    (190.5,55.88,'Q1 keeps USB 5V away from PA0.\nR2 holds OFF with Blue Pill absent.\nGround is shared; no galvanic isolation.',1.016),
    (25.4,181.61,'USB D+ / D- connect directly; no connection to the Blue Pill USB pins.',1.27),
    (25.4,186.69,'43k sets ~0.61 A nominal trip; design load <=500 mA. R5 discharges output when off.',1.27),
    (25.4,191.77,'150uF output reservoir; 90 ohm differential routing target on four copper layers.',1.27),
]:
    msg=msg.replace('\n','\\n')
    sch.append(f'(text "{msg}" (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid {uid(msg)}))')
sch.append('(sheet_instances (path "/" (page "1"))) (embedded_fonts no))')
(ROOT / f'{NAME}.kicad_sch').write_text('\n'.join(sch),encoding='utf-8')
(ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Board") (type "KiCad") (uri "${KIPRJMOD}/library/Board.kicad_sym") (options "") (descr "")))\n',encoding='utf-8')

# USB connector footprints are checked-in project-local libraries, corrected
# against the manufacturer drawings. Their preparation is not repeated here.
board=p.BOARD()

board.SetCopperLayerCount(4)
board.GetDesignSettings().SetBoardThickness(p.FromMM(1.6)); board.GetDesignSettings().SetAuxOrigin(xy(100,80))
nets={}
for net in sorted({n for part in parts.values() for n in part['nets'].values()}):
    nets[net]=p.NETINFO_ITEM(board,'/'+net); board.Add(nets[net])
def line(a,b,layer=p.Edge_Cuts,width=0.05):
    s=p.PCB_SHAPE(); s.SetShape(p.SHAPE_T_SEGMENT); s.SetStart(xy(*a)); s.SetEnd(xy(*b)); s.SetLayer(layer); s.SetWidth(p.FromMM(width)); board.Add(s)
def text(msg,x,y,size=0.9,layer=p.F_SilkS):
    t=p.PCB_TEXT(board); t.SetText(msg); t.SetPosition(xy(x,y)); t.SetTextSize(xy(size,size)); t.SetTextThickness(p.FromMM(0.12)); t.SetLayer(layer); board.Add(t)
for a,b in [((100,80),(153,80)),((153,80),(153,126)),((153,126),(100,126)),((100,126),(100,80))]: line(a,b)
footprints={}
used_libs=set()
for ref,part in parts.items():
    if not part['pcb']: continue
    lib,name=part['footprint'].split(':'); used_libs.add(lib)
    directory=ROOT/'library/USBParts.pretty' if lib=='USBParts' else LIB/f'footprints/{lib}.pretty'
    fp=p.FootprintLoad(str(directory),name); fp.SetFPIDAsString(part['footprint']); fp.SetReference(ref); fp.SetValue(part['value'])
    fp.SetPath(p.KIID_PATH(f'/{SHEET}/{uid(ref)}')); fp.SetSheetfile(f'{NAME}.kicad_sch'); fp.SetSheetname('')
    fp.SetField('LCSC',part['lcsc']); fp.GetField('LCSC').SetVisible(False)
    fp.SetField('Datasheet','https://www.lcsc.com/product-detail/'+part['lcsc']+'.html' if part['lcsc'] else '')
    x,y,angle=part['pcb']; fp.SetOrientationDegrees(angle); fp.SetPosition(xy(x,y)); fp.Value().SetVisible(False)
    fp.Reference().SetTextSize(xy(0.8,0.8)); fp.Reference().SetTextThickness(p.FromMM(0.12)); fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
    for pad in fp.Pads():
        net=part['nets'].get(pad.GetNumber())
        if net: pad.SetNet(nets[net])
        elif pad.GetNumber():
            label=next(pin[1] for pin in pin_defs[part['symbol']] if pin[0]==pad.GetNumber())
            unused=p.NETINFO_ITEM(board,f'unconnected-({ref}-{label}-Pad{pad.GetNumber()})'); board.Add(unused); pad.SetNet(unused)
    board.Add(fp); footprints[ref]=fp

def pos(ref,num):
    pad=next(pad for pad in footprints[ref].Pads() if pad.GetNumber()==str(num))
    v=pad.GetPosition(); return (p.ToMM(v.x),p.ToMM(v.y))
def route(net,points,width=0.25,layer=p.F_Cu):
    for a,b in zip(points,points[1:]):
        if a==b: continue
        t=p.PCB_TRACK(board); t.SetStart(xy(*a)); t.SetEnd(xy(*b)); t.SetWidth(p.FromMM(width)); t.SetLayer(layer); t.SetNet(nets[net]); board.Add(t)
def via(net,x,y):
    v=p.PCB_VIA(board); v.SetPosition(xy(x,y)); v.SetWidth(p.FromMM(0.6)); v.SetDrill(p.FromMM(0.3)); v.SetViaType(p.VIATYPE_THROUGH); v.SetLayerPair(p.F_Cu,p.B_Cu); v.SetNet(nets[net]); board.Add(v)
def ground(ref,num,end):
    route('GND',[pos(ref,num),end],0.3); via('GND',*end)

# Equal-length data paths; all top copper, no data vias, no branches.
for num,net,sign in [(2,'USB_D-',1),(3,'USB_D+',-1)]:
    yy=114.5+sign*0.23
    route(net,[pos('J3',num),(107,114.5+sign),(107.77,yy),(136,yy),(136.77,114.5+sign),pos('J4',num)],0.28)
# Compact lower power section: decouplers share a row; Q1/U1 share a row.
# Reservoir and switched VBUS stay below the USB pair, entirely on F.Cu.
route('VBUS_IN',[pos('J3',1),(116.5,118),(118.55,120.05),pos('U1',1)],0.65)
route('VBUS_IN',[pos('C1',1),(119,120.05)],0.4)
via('VBUS_IN',118.8,120.05); via('VBUS_IN',117.5,124)
route('VBUS_IN',[(118.8,120.05),(118.8,122.7),(117.5,124)],0.3,p.B_Cu)
route('VBUS_IN',[(117.5,124),pos('R1',1)],0.3)
route('VBUS_OUT',[pos('U1',6),(124,120.05),(124.55,119.5),(128,119.5),(129.3,120.8),pos('C3',1)],0.5)
route('VBUS_OUT',[pos('C2',1),(125,119.5)],0.4)
route('VBUS_OUT',[pos('R5',1),(127,119.5)],0.3)
route('VBUS_OUT',[(128,119.5),(129,118.5),(129,117),(129.7,116.3),(135.5,116.3),(137.2,118),pos('J4',1)],0.65)
route('ILIM',[pos('U1',5),(124.4,121),(125.6,122.2),(125.6,122.8),(124.8,123.6),pos('R4',1)])
route('SW_EN_N',[pos('Q1',3),(118,121),(119.2,122.2),(120.2,122.2),pos('U1',3)])
route('SW_EN_N',[pos('R1',2),(120.2,123.625),(120.2,122.2)])
route('GATE',[pos('R3',2),(113.6,123.725),(113.6,121),(114.55,120.05),pos('Q1',1)])
route('GATE',[pos('R2',1),(113.6,121.825)])
route('VBUS_ON',[pos('J1',5),(139.2,85.15),(139.2,104),(136,107.2),(111.225,107.2),(110.5,107.925),(110.5,123)],0.25,p.B_Cu)
via('VBUS_ON',110.5,123); route('VBUS_ON',[(110.5,123),pos('R3',1)])
for ref,num,end in [('J3',4,(107,111)),('J4',4,(136.3,111)),('J4',5,(141.45,105.8)),('J4',6,(141.45,123.2)),
                    ('U1',2,(119.8,121)),('C1',2,(119,116.3)),('C2',2,(125,116.3)),
                    ('C3',2,(136.3,121)),('R2',2,(111.2,120.175)),('R4',2,(126.8,124)),('R5',2,(127,116.3)),('Q1',2,(115,123))]:
    ground(ref,num,end)
for x,y in [(106,108),(109.7,111),(115,111),(120,111),(125,111),(130,111),(134,111),(105,124),(146,104),(151,124),(151,104),(102,104),(130,125)]:
    via('GND',x,y)
for layer in (p.In1_Cu,p.In2_Cu):
    z=p.ZONE(board); z.SetLayer(layer); z.SetNet(nets['GND']); z.SetLocalClearance(p.FromMM(0.2)); z.SetThermalReliefGap(p.FromMM(0.25)); z.SetThermalReliefSpokeWidth(p.FromMM(0.3)); z.SetPadConnection(p.ZONE_CONNECTION_FULL)
    outline=z.Outline(); outline.NewOutline()
    for x,y in [(100.5,80.5),(152.5,80.5),(152.5,125.5),(100.5,125.5)]: outline.Append(p.FromMM(x),p.FromMM(y))
    board.Add(z)

# Assembly annotations and module outline avoid the through-hole pads.
for ref,pins in bp.items():
    for num,label in enumerate(pins,1):
        x,_=pos(ref,num); label=label[1:] if re.fullmatch(r'P[ABC]\d+',label) else {'VBAT':'VB','NRST':'RST'}.get(label,label)
        text(label,x,81.15 if ref=='J1' else 101.85,0.8)
for a,b in [((100,80),(153,80)),((153,80),(153,103)),((153,103),(100,103)),((100,103),(100,80))]: line(a,b,p.Dwgs_User,0.15)
text('BLUE PILL - SEPARATE USB POWER',126.5,89.5,1.0)
text('PA0 HIGH = VBUS ON',126.5,93,1.0)
text('USB IN',105.5,105.1,1.0); text('USB OUT',147.5,105.1,1.0)
text('VBUS SWITCH',116,104.8,1.0)
text('53 x 46 mm | 4 layers | 1.6 mm | rev 2.0',126.5,129,1.0,p.Dwgs_User)
refs={'J1':(149,87),'J2':(149,96),'J3':(105,122),'J4':(148,124),
      'U1':(122,118.5),'Q1':(116,118.5),
      'R1':(119,125.2),'R2':(110.8,121),'R3':(112.5,125.2),'R4':(125,125.2),
      'R5':(127,115.9),'C1':(119,115.9),'C2':(125,115.9),'C3':(132,116.5)}
for ref,at in refs.items(): footprints[ref].Reference().SetPosition(xy(*at))
board.BuildConnectivity(); p.ZONE_FILLER(board).Fill(board.Zones())
p.SaveBoard(str(ROOT/f'{NAME}.kicad_pcb'),board)
pcb_path=ROOT/f'{NAME}.kicad_pcb'
pcb_src=pcb_path.read_text(encoding='utf-8')
stackup='''(stackup
    (layer "F.SilkS" (type "Top Silk Screen"))
    (layer "F.Paste" (type "Top Solder Paste"))
    (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
    (layer "F.Cu" (type "copper") (thickness 0.035))
    (layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
    (layer "In1.Cu" (type "copper") (thickness 0.0152))
    (layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
    (layer "In2.Cu" (type "copper") (thickness 0.0152))
    (layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
    (layer "B.Cu" (type "copper") (thickness 0.035))
    (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
    (layer "B.Paste" (type "Bottom Solder Paste"))
    (layer "B.SilkS" (type "Bottom Silk Screen"))
    (copper_finish "ENIG") (dielectric_constraints yes))'''
pcb_path.write_text(pcb_src.replace('(setup\n','(setup\n'+stackup+'\n',1),encoding='utf-8')
project_path.write_text(json.dumps(project,indent=2)+'\n',encoding='utf-8')
table=['(fp_lib_table (version 7)']
for lib in sorted(used_libs):
    uri='${KIPRJMOD}/library/USBParts.pretty' if lib=='USBParts' else '${KICAD10_FOOTPRINT_DIR}/'+lib+'.pretty'
    table.append(f'(lib (name "{lib}") (type "KiCad") (uri "{uri}") (options "") (descr ""))')
(ROOT/'fp-lib-table').write_text('\n'.join(table)+')\n',encoding='utf-8')
with (ROOT/'bom.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.writer(f); writer.writerow(['Reference','Value','MPN','LCSC','Footprint'])
    for ref,part in parts.items():
        if part['pcb']: writer.writerow([ref,part['value'],part['mpn'],part['lcsc'],part['footprint']])

saved=p.LoadBoard(str(ROOT/f'{NAME}.kicad_pcb'))
assert saved.GetCopperLayerCount()==4
assert len(list(saved.GetFootprints()))==14
edges=[point for shape in saved.GetDrawings() if shape.GetLayer()==p.Edge_Cuts for point in (shape.GetStart(),shape.GetEnd())]
assert max(v.x for v in edges)-min(v.x for v in edges)==p.FromMM(53)
assert max(v.y for v in edges)-min(v.y for v in edges)==p.FromMM(46)
for ref in ('J1','J2'):
    fp=next(f for f in saved.GetFootprints() if f.GetReference()==ref)
    assert len(list(fp.Pads()))==20
    for pad in fp.Pads():
        num=int(pad.GetNumber())
        assert abs(p.ToMM(pad.GetPosition().x)-(150.63-(num-1)*2.54))<0.001
        assert abs(p.ToMM(pad.GetPosition().y)-(83.88 if ref=='J1' else 99.12))<0.001
        if str(num) in parts[ref]['nets']:
            assert pad.GetNetname()=='/'+parts[ref]['nets'][str(num)]
        if bp[ref][int(pad.GetNumber())-1] in ('3V3','5V','VBAT'):
            assert pad.GetNetname().startswith('unconnected-'), 'Controller power must remain separate from switched USB'
lengths={net:sum(t.GetLength() for t in saved.GetTracks() if t.GetNetname()=='/'+net) for net in ('USB_D+','USB_D-')}
assert abs(lengths['USB_D+']-lengths['USB_D-']) < p.FromMM(0.01)
assert not any(isinstance(t,p.PCB_VIA) and t.GetNetname() in ('/USB_D+','/USB_D-') for t in saved.GetTracks())
print('Generated 53 x 46 mm, four layers, 14 components, separate controller power.')
print('USB matched track lengths (mm):', {n:p.ToMM(v) for n,v in lengths.items()})
