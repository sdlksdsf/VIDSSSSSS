import sys
from PIL import Image
# usage: sheet.py out.jpg frame frame ...
ims=[Image.open(f"/tmp/frames/{int(n):05d}.jpg").resize((270,480)) for n in sys.argv[2:]]
cols=min(len(ims),5); rows=(len(ims)+cols-1)//cols
sh=Image.new('RGB',(cols*270,rows*480))
for k,im in enumerate(ims): sh.paste(im,((k%cols)*270,(k//cols)*480))
sh.save(sys.argv[1],quality=85)
