"""Create honest illustrated product placeholders. Replace images/<id>.png with authorized product photos."""
import math
from pathlib import Path
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

COLORS={'white':'#f0efec','black':'#292b30','blue':'#668bb6','beige':'#cbb89e','grey':'#969a9d','brown':'#79543d','navy':'#293c62','gold':'#bd9b4a','silver':'#a4a9b1'}
OUT=Path('images');OUT.mkdir(exist_ok=True)
for _,row in pd.read_csv('catalog.csv').iterrows():
    im=Image.new('RGB',(480,550),'#eeeae5');d=ImageDraw.Draw(im)
    col=COLORS.get(str(row.color),'#aaa19a');cat=row.category
    d.rounded_rectangle((32,32,448,518),radius=20,fill='#faf9f7')
    if cat in ('top','outerwear'):
        d.polygon([(145,138),(193,111),(287,111),(335,138),(405,224),(352,264),(316,220),(322,426),(158,426),(164,220),(128,264),(75,224)],fill=col,outline='#9d9890',width=4)
        d.line([(193,111),(240,171),(287,111)],fill='#9d9890',width=4)
        if cat=='outerwear':d.line([(240,171),(240,426)],fill='#9d9890',width=5)
    elif cat=='bottom':
        d.polygon([(149,118),(331,118),(343,426),(260,426),(240,241),(220,426),(137,426)],fill=col,outline='#9d9890',width=4)
        d.line([(149,163),(331,163)],fill='#9d9890',width=4)
    elif cat=='shoes':
        for shift in [0,165]:
            d.rounded_rectangle((70+shift,280,226+shift,355),radius=25,fill=col,outline='#9d9890',width=4)
            d.rounded_rectangle((66+shift,341,232+shift,366),radius=9,fill='#d7d2cc')
    else:
        d.ellipse((139,162,341,366),outline=col,width=28)
        d.ellipse((205,223,275,293),fill='#faf9f7')
    d.text((48,466),str(row['name'])[:31],fill='#33312f')
    im.save(OUT/f'{int(row.id)}.png')
print('Generated illustrated placeholders for every catalog item.')
