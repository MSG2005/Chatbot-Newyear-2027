"""Local greeting-card renderer. No external image-generation API."""
from io import BytesIO
from pathlib import Path
import math
import random
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps

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

def render_card(text, flow_id='1', variant=0):
    text=card_text(text)
    if not text or len(text)>2200:
        raise ValueError('No usable greeting or greeting too long')
    fid=str(flow_id) if str(flow_id) in {'1','2','3','4','5'} else '1'
    variant=int(variant)%2
    path=Path(__file__).resolve().parent/'assets'/'cards'/f'theme-{fid}.png'
    with Image.open(path) as source:
        image=source.convert('RGB').resize((1080,1350),Image.Resampling.LANCZOS)
    if variant:
        image=ImageOps.mirror(image)
    image=image.convert('RGBA')
    accent={'1':'#1d584a','2':'#a73e1d','3':'#503279','4':'#964755','5':'#79502d'}[fid]
    titles={'1':'Happy New Year!','2':'New Year, Same You!','3':'Your 2027 Forecast','4':'From the Heart','5':'A Letter from Future You'}
    overlay=Image.new('RGBA',image.size,(0,0,0,0));o=ImageDraw.Draw(overlay)
    if variant:
        o.rounded_rectangle((78,403,1002,1127),radius=24,fill=accent+'ed',outline=accent,width=2)
        ink='#fff9ed';secondary='#fff0d9'
    else:
        o.rounded_rectangle((78,403,1002,1127),radius=24,fill=(255,251,240,100),outline=accent+'45',width=2)
        ink=accent;secondary=accent
    image=Image.alpha_composite(image,overlay);d=ImageDraw.Draw(image)
    def center(y,label,face,color):
        d.text(((1080-d.textlength(label,font=face))/2,y),label,font=face,fill=color)
    title=titles[fid]
    for heading_size in range(48,25,-1):
        heading=font(heading_size,not variant)
        if d.textlength(title,font=heading)<=830:break
    center(428,title,heading,ink)
    subtitle='NEW YEAR 2027' if fid not in {'3','5'} else 'NEW YEAR 2027 · FICTIONAL MESSAGE'
    center(493,subtitle,font(20),secondary)
    d.line((440,538,640,538),fill=secondary,width=2)
    for size in range(36,13,-1):
        face=font(size,not variant);lines=wrap(d,text,face,810)
        step=math.ceil(size*1.4)
        if len(lines)*step<=460:break
    else:raise ValueError('Greeting does not fit the card')
    top=572+(460-len(lines)*step)//2
    for line in lines:
        if variant:
            d.text((135,top),line,font=face,fill=ink)
        else:center(top,line,face,ink)
        top+=step
    center(1077,'DIGITAL CATALYST · NEW YEAR AI',font(17),secondary)
    data=BytesIO();image.convert('RGB').save(data,format='JPEG',quality=90,optimize=True)
    return data.getvalue()
