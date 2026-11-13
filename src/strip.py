import sys; sys.path.insert(0,'src')
import film
from PIL import Image
ts=[float(x) for x in sys.argv[2:]]
ims=[film.frame(t).resize((270,480)) for t in ts]
cols=min(len(ims),6); rows=(len(ims)+cols-1)//cols
sh=Image.new('RGB',(cols*270,rows*480))
for k,im in enumerate(ims): sh.paste(im,((k%cols)*270,(k//cols)*480))
sh.save(sys.argv[1],quality=85)
