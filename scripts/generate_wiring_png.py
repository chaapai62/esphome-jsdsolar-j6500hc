#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

W, H = 1800, 1200
OUT = Path('/root/.hermes/projects/esphome-jsdsolar-j6500hc/docs/assets/jsd-j6500hc-wiring.png')

COL = {
    'bg': '#f8fafc', 'ink': '#0f172a', 'muted': '#475569', 'card': '#ffffff',
    'orange_bg': '#fff7ed', 'orange': '#ea580c', 'green_bg': '#ecfdf5', 'green': '#059669',
    'blue_bg': '#eff6ff', 'blue': '#2563eb', 'red': '#dc2626', 'black': '#111827',
    'light': '#e2e8f0', 'pin': '#f8fafc', 'warn': '#9a3412', 'wire_green': '#16a34a',
    'white': '#ffffff', 'usb_shell': '#cbd5e1', 'pcb': '#0f766e', 'pcb_dark': '#064e3b'
}

def font(size, bold=False, mono=False):
    base = '/usr/share/fonts/truetype/dejavu/'
    if mono:
        name = 'DejaVuSansMono-Bold.ttf' if bold else 'DejaVuSansMono.ttf'
    else:
        name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(base + name, size)

F = {
    'title': font(30, True), 'subtitle': font(18), 'section': font(21, True),
    'label': font(16, True), 'small': font(13), 'tiny': font(11), 'warn': font(14, True),
    'mono': font(13, True, True), 'mono_small': font(11, True, True)
}

img = Image.new('RGB', (W, H), COL['bg'])
d = ImageDraw.Draw(img)

def rr(xy, fill, outline, width=2, radius=16):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def text(x, y, s, f='small', fill='ink', anchor=None):
    d.text((x, y), s, font=F[f], fill=COL.get(fill, fill), anchor=anchor)

def line(points, fill, width=5, dash=None, arrow=True):
    if dash:
        # draw dashed segment by segment
        for (x1,y1),(x2,y2) in zip(points, points[1:]):
            dx, dy = x2-x1, y2-y1
            dist = math.hypot(dx, dy)
            if dist == 0: continue
            ux, uy = dx/dist, dy/dist
            pos = 0; on = True
            while pos < dist:
                seg = min(dash[0] if on else dash[1], dist-pos)
                if on:
                    d.line((x1+ux*pos, y1+uy*pos, x1+ux*(pos+seg), y1+uy*(pos+seg)), fill=fill, width=width)
                pos += seg; on = not on
    else:
        d.line(points, fill=fill, width=width, joint='curve')
    if arrow and len(points) >= 2:
        x1,y1 = points[-2]; x2,y2 = points[-1]
        ang = math.atan2(y2-y1, x2-x1)
        L=18; A=0.55
        p1=(x2-L*math.cos(ang-A), y2-L*math.sin(ang-A))
        p2=(x2-L*math.cos(ang+A), y2-L*math.sin(ang+A))
        d.polygon([(x2,y2),p1,p2], fill=fill)

def pinbox(x,y,w,h,label,fill,outline,textfill='ink'):
    d.rounded_rectangle((x,y,x+w,y+h), radius=5, fill=fill, outline=outline, width=2)
    d.text((x+w/2,y+h/2), label, font=F['mono_small'], fill=COL.get(textfill,textfill), anchor='mm')

# Header
text(55, 50, 'Branchement détaillé — JSD Solar J6500HC USB-A RS232 → MAX3232 → ESP32-C3 Supermini', 'title')
text(55, 84, 'Sortie PNG — port onduleur USB-A, pinout couleurs, convertisseur RS232/TTL et ESP32-C3 Supermini 16 pins', 'subtitle', 'muted')

# Cards
rr((55,130,555,655), COL['orange_bg'], COL['orange'])
rr((650,130,1105,720), COL['green_bg'], COL['green'])
rr((1215,130,1725,915), COL['blue_bg'], COL['blue'])

# Inverter / USB-A
text(85,165,'1 — Onduleur JSD Solar J6500HC','section')
text(85,197,'Connecteur visible : USB-A femelle utilisé comme liaison RS232','small','muted')
text(85,224,'Attention : ce n’est pas un port USB logique pour l’ESP32.','warn','warn')
# USB-A realistic receptacle
text(115,265,'Port USB-A physique — vue de face','label')
# outer shell with highlights
rr((115,290,445,465), '#cbd5e1', '#475569', 5, 20)
d.rectangle((142,320,418,430), fill='#f8fafc', outline='#111827', width=3)
d.rounded_rectangle((185,350,375,400), radius=5, fill='#111827')
# pins
pin_colors = [('#dc2626','1 VBUS rouge'),('#ffffff','2 D− blanc'),('#22c55e','3 D+ vert'),('#111827','4 GND noir')]
for i,(c,lbl) in enumerate(pin_colors):
    x=198+i*43
    d.rounded_rectangle((x,362,x+30,388), radius=3, fill=c, outline='#94a3b8' if c=='#ffffff' else c, width=1)
    text(x-8,410,lbl,'tiny','muted')
text(85,505,'Couleurs USB-A standard à vérifier sur le câble RS232 :','label')
legend_y=535
items=[('Rouge','VBUS habituel — peut être réutilisé par câble propriétaire','#dc2626','white'),('Blanc','D− habituel — peut porter TX/RX selon adaptateur','#ffffff','ink'),('Vert','D+ habituel — peut porter TX/RX selon adaptateur','#22c55e','ink'),('Noir','GND commun','#111827','white')]
for i,(name,desc,c,tf) in enumerate(items):
    y=legend_y+i*42
    pinbox(85,y,90,30,name,c,'#334155',tf)
    text(195,y+7,desc,'small','muted')

# Converter board
text(680,165,'2 — Convertisseur RS232 ↔ TTL','section')
text(680,197,'Module type MAX3232 compatible 3,3 V côté TTL','small','muted')
text(680,224,'Adapte les niveaux ±RS232 vers TTL 3,3 V.','warn','warn')
# PCB
rr((725,270,1040,535), '#0f766e', '#064e3b', 4, 20)
for cx,cy in [(750,295),(1015,295),(750,510),(1015,510)]:
    d.ellipse((cx-9,cy-9,cx+9,cy+9), fill='#d1fae5', outline='#064e3b', width=2)
rr((835,350,930,420), '#111827', '#334155', 2, 8)
text(855,370,'MAX','label','white')
text(852,395,'3232','label','white')
rr((750,320,805,455), '#fde68a', '#92400e', 2, 8)
text(762,374,'RS232','mono_small','#78350f')
rr((960,305,1017,475), '#bfdbfe', '#1d4ed8', 2, 8)
text(975,372,'TTL','mono_small','#1e3a8a')
# pins on converter
pinbox(740,480,82,30,'RS232 RX','#dbeafe',COL['blue'])
pinbox(833,480,82,30,'RS232 TX','#fee2e2',COL['red'])
pinbox(926,480,82,30,'GND','#e2e8f0',COL['black'])
pinbox(945,285,84,30,'TTL TX','#dbeafe',COL['blue'])
pinbox(945,323,84,30,'TTL RX','#fee2e2',COL['red'])
pinbox(945,361,84,30,'VCC','#dcfce7',COL['wire_green'])
pinbox(945,399,84,30,'GND','#e2e8f0',COL['black'])
text(680,585,'Côté TTL vers ESP32-C3 :','label')
text(700,615,'TTL TX → GPIO20 RX','mono')
text(700,645,'TTL RX ← GPIO21 TX','mono')
text(700,675,'VCC 3V3 + GND commun','mono')

# ESP board
text(1245,165,'3 — ESP32-C3 Supermini 16 pins','section')
text(1245,197,'GPIO20 = RX, GPIO21 = TX — logique 3,3 V uniquement','small','muted')
text(1245,224,'Ne jamais appliquer du TTL 5 V sur GPIO20/GPIO21.','warn','warn')
# board body
rr((1355,280,1570,735), '#1e293b', '#0f172a', 5, 28)
rr((1417,298,1509,346), '#dbeafe', '#64748b', 2, 10)
text(1437,315,'USB-C','label')
rr((1410,390,1518,520), '#111827', '#475569', 2, 12)
text(1428,442,'ESP32','label','white')
text(1450,472,'C3','label','white')
rr((1422,555,1505,600), '#334155', '#64748b', 2, 6)
text(1436,570,'FLASH','mono_small','#cbd5e1')
# ESP pins
left=[('5V','#dcfce7',COL['wire_green']),('GND','#e2e8f0',COL['black']),('3V3','#dcfce7',COL['wire_green']),('GPIO0','#f8fafc','#475569'),('GPIO1','#f8fafc','#475569'),('GPIO2','#f8fafc','#475569'),('GPIO3','#f8fafc','#475569'),('GPIO4','#f8fafc','#475569')]
right=[('GPIO5','#f8fafc','#475569'),('GPIO6','#f8fafc','#475569'),('GPIO7','#f8fafc','#475569'),('GPIO8','#f8fafc','#475569'),('GPIO9','#f8fafc','#475569'),('GPIO10','#f8fafc','#475569'),('GPIO21 TX','#fee2e2',COL['red']),('GPIO20 RX','#dbeafe',COL['blue'])]
for i,(lbl,fill,outline) in enumerate(left):
    pinbox(1245,280+i*52,96,30,lbl,fill,outline)
for i,(lbl,fill,outline) in enumerate(right):
    pinbox(1585,280+i*52,110,30,lbl,fill,outline)

# Wires
line([(445,375),(555,365),(645,470),(740,495)], COL['blue'], 6)
text(465,342,'Onduleur TX RS232 → RS232 RX','label','blue')
line([(833,495),(655,410),(555,405),(445,402)], COL['red'], 6, dash=(16,10))
text(475,430,'RS232 TX → onduleur RX — debug actif uniquement','label','red')
line([(445,455),(570,575),(720,525),(926,495)], COL['black'], 6)
text(500,510,'GND commun','label','black')
line([(1029,300),(1145,285),(1215,660),(1585,660)], COL['blue'], 6)
text(1090,284,'TTL TX → ESP GPIO20 RX','label','blue')
line([(1585,608),(1255,558),(1148,340),(1029,338)], COL['red'], 6, dash=(16,10))
text(1100,553,'ESP GPIO21 TX → TTL RX','label','red')
line([(1245,399),(1140,425),(1085,376),(1029,376)], COL['wire_green'], 6)
text(1098,400,'3V3 → VCC','label','wire_green')
line([(1245,347),(1160,380),(1090,414),(1029,414)], COL['black'], 6)
text(1105,435,'GND → GND','label','black')

# Bottom legend (no firmware correspondence table)
rr((55,790,1115,1110), COL['card'], '#334155', 2, 16)
text(85,832,'Légende et avertissements','section')
line([(95,870),(185,870)], COL['blue'], 6); text(210,860,'Bleu : réception normale des données onduleur vers ESP32.','label')
line([(95,915),(185,915)], COL['red'], 6, dash=(16,10)); text(210,905,'Rouge pointillé : émission vers l’onduleur, seulement en passerelle brute active.','label')
line([(95,960),(185,960)], COL['wire_green'], 6); text(210,950,'Vert : alimentation 3,3 V du module MAX3232 si compatible.','label')
line([(95,1005),(185,1005)], COL['black'], 6); text(210,995,'Noir : masse commune obligatoire.','label')
text(85,1050,'Le brochage USB-A RS232 de l’onduleur doit être vérifié au multimètre / documentation du câble avant mise sous tension.','warn','warn')
text(85,1082,'Le code couleur USB-A standard est montré pour identifier les fils du connecteur physique ; le JSD peut réutiliser ces contacts pour du RS232 propriétaire.','small','muted')

rr((1215,950,1725,1110), COL['card'], '#334155', 2, 16)
text(1245,990,'Notes côté ESP32-C3','section')
text(1245,1022,'GPIO20 RX : réception des données depuis le convertisseur.','small','muted')
text(1245,1052,'GPIO21 TX : émission optionnelle pour debug actif uniquement.','small','muted')
text(1245,1082,'Le port TCP 6666 peut transmettre si TX est câblé.','small','muted')

text(55,1160,'Image générée pour documentation — JSD Solar J6500HC, port USB-A RS232, MAX3232, ESP32-C3 Supermini 16 pins.','tiny','muted')

img.save(OUT)
print(OUT)
print(OUT.stat().st_size)
