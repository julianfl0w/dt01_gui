import os
from PIL import Image, ImageDraw, ImageFont

# make sure you have the fonts locally in a fonts/ directory
georgia_bold = 'fonts/georgia_bold.ttf'
georgia_bold_italic = 'fonts/georgia_bold_italic.ttf'

# W, H = (1280, 720) # image size
W, H = (720, 405) # image size
txt = 'Hello Petar this is my test image' # text to render
background = (0,164,201) # white
fontsize = 35
font = ImageFont.truetype(georgia_bold_italic, fontsize)

image = Image.new('RGBA', (W, H), background)
draw = ImageDraw.Draw(image)

# w, h = draw.textsize(txt) # not that accurate in getting font size
w, h = font.getsize(txt)

draw.text(((W-w)/2,(H-h)/2), txt, fill='white', font=font)
# draw.text((10, 0), txt, (0,0,0), font=font)
# img_resized = image.resize((188,45), Image.ANTIALIAS)

save_location = os.getcwd()

# img_resized.save(save_location + '/sample.jpg')
image.save(save_location + '/sample.png')
