"""Local greeting-card renderer. No external image-generation API."""
from io import BytesIO
from pathlib import Path
import math
import random
import re
from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).resolve().parent / 'fonts'

def font(size, serif=False):
    return ImageFont.truetype(str(FONTS / ('DejaVuSerif.ttf' if serif else 'DejaVuSans.ttf')), size)

def card_text(text):
    # Decorative emoji are omitted: bundled fonts are not colour-emoji fonts.
    # Keep wording, punctuation, names and paragraph breaks.
    return re.sub(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0E\uFE0F\u200D]', '', text).strip()

def wrap(draw, text, face, width):
    lines=[]
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            lines.append(''); continue
        line=''
        for word in paragraph.split():
            candidate = (line + ' ' + word).strip()
            if draw.textlength(candidate, font=face) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
                line = ''
            # Only break an individual word if it is wider than the panel.
            for char in word:
                if line and draw.textlength(line + char, font=face) > width:
                    lines.append(line)
                    line = ''
                line += char
        if line.strip(): lines.append(line.rstrip())
    return lines

def render_card(text, flow_id='1'):
    text=card_text(text)
    if not text or len(text)>2200:
        raise ValueError('No usable greeting or greeting too long')
    image=Image.new('RGB',(1080,1350),'#082b30')
    d=ImageDraw.Draw(image)
    for y in range(1350):
        t=y/1349
        d.line((0,y,1080,y),fill=(int(8+8*t),int(43+27*t),int(48+25*t)))
    rng=random.Random(2027)
    for _ in range(65):
        x,y=rng.randrange(45,1035),rng.choice([rng.randrange(35,200),rng.randrange(1170,1315)])
        r=rng.choice([1,2,3]);d.ellipse((x-r,y-r,x+r,y+r),fill='#bfa66b')
    d.rounded_rectangle((35,35,1045,1315),radius=26,outline='#bfa66b',width=2)
    d.rounded_rectangle((70,265,1010,1150),radius=22,fill='#fffaf0')
    def center(y,label,face,fill):
        d.text(((1080-d.textlength(label,font=face))/2,y),label,font=face,fill=fill)
    center(80,'HAPPY NEW YEAR',font(32),'#e6d5af')
    center(127,'2027',font(90,True),'#fff6dc')
    titles={'1':'A wish just for you','2':'A playful New Year roast','3':'Your fictional 2027 forecast','4':'Words from the heart','5':'A fictional note from future you'}
    center(290,titles.get(str(flow_id),'Your New Year message'),font(27),'#42635e')
    # Fit ALL text inside the cream panel, with no truncation.
    for size in range(39,15,-1):
        face=font(size,True);lines=wrap(d,text,face,820)
        step=math.ceil(size*1.48)
        if len(lines)*step<=705:break
    else:raise ValueError('Greeting does not fit the card')
    top=370+(705-len(lines)*step)//2
    for line in lines:
        center(top,line,face,'#173b37');top+=step
    d.line((420,1190,660,1190),fill='#bfa66b',width=2)
    center(1210,'DIGITAL CATALYST',font(23),'#f2e5c8')
    center(1252,'New Year AI 2027',font(18),'#c3d7cf')
    data=BytesIO();image.save(data,format='JPEG',quality=92,optimize=True)
    return data.getvalue()
