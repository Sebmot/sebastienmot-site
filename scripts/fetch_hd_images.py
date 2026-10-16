#!/usr/bin/env python3
"""Remplace les images de posts par la plus haute résolution LinkedIn (feedshare-image-high-res) si une version plus grande et identique existe. Usage : python scripts/fetch_hd_images.py"""
import json,re,urllib.request,io
from PIL import Image,ImageChops,ImageStat
UA={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36'}
def get(u):return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20).read()
for p in json.load(open('posts.json'))['posts']:
  if not p.get('image'):continue
  cur=Image.open(p['image']).convert('RGB');html=get(p['url']).decode('utf8','ignore')
  urls={u.replace('&amp;','&') for u in re.findall(r'https://media\.licdn\.com/dms/image/[^"\s]*feedshare[^"\s]*',html)}
  best=None
  for u in urls:
    try:im=Image.open(io.BytesIO(get(u))).convert('RGB')
    except Exception:continue
    if abs(im.width/im.height-cur.width/cur.height)>0.03:continue
    d=sum(ImageStat.Stat(ImageChops.difference(im.resize((64,64)),cur.resize((64,64)))).mean)/3
    if d<18 and (not best or im.width>best[1].width):best=(u,im,d)
  print(p['image'],cur.size,'->',(best[1].size,round(best[2],1)) if best else None)
  if best and best[1].width>cur.width:
    ext=p['image'].rsplit('.',1)[1].lower()
    if ext in('jpg','jpeg'):best[1].save(p['image'],quality=88,optimize=True,progressive=True)
    else:best[1].save(p['image'],optimize=True)
