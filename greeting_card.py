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

def render_card(text, flow_id='1', variant=0, recipient_name=''):
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
    # Opaque ink panel keeps variable-length greetings readable over every illustration.
    o.rounded_rectangle((88,390,992,1145),radius=34,fill=accent+'ff')
    o.rounded_rectangle((104,406,976,1129),radius=26,outline='#d9b76f',width=2)
    image=Image.alpha_composite(image,overlay);d=ImageDraw.Draw(image)
    ink='#fff7e7';gold='#f0d697'
    def center(y,label,face,color):
        d.text(((1080-d.textlength(label,font=face))/2,y),label,font=face,fill=color)
    recipient = 'For ' + card_text(recipient_name) if recipient_name else 'MADE JUST FOR YOU'
    for size in range(29,15,-1):
        face=font(size)
        if d.textlength(recipient,font=face)<=780:break
    center(445,recipient,face,gold)
    center(505,'Happy New Year',font(55,True),ink)
    center(567,'2027',font(82,True),gold)
    d.line((410,685,670,685),fill=gold,width=2)
    for size in range(34,17,-1):
        face=font(size,True);lines=wrap(d,text,face,750)
        step=math.ceil(size*1.45)
        if len(lines)*step<=290:break
    else:raise ValueError('Greeting does not fit the card')
    top=720+(290-len(lines)*step)//2
    for line in lines:
        center(top,line,face,ink)
        top+=step
    if fid in {'3','5'}:
        center(1033,'AN IMAGINARY MESSAGE · JUST FOR FUN',font(16),gold)
    center(1086,'Made with Digital Catalyst',font(19),gold)
    data=BytesIO();image.convert('RGB').save(data,format='JPEG',quality=90,optimize=True)
    return data.getvalue()
