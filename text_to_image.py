import os
from PIL import Image, ImageDraw, ImageFont
import re 
import sys

# make sure you have the fonts locally in a fonts/ directory
pacifico = 'patches/Pacifico.ttf'

regex = re.compile('[^a-zA-Z]')
#First parameter is the replacement, second parameter is your input string
regex.sub('', 'ab3d*E')
#Out: 'abdE'

def text_to_image(txt, size = (200, 70)):
	regex = re.compile('[^a-zA-Z0-9]')
	#First parameter is the replacement, second parameter is your input string
	fileFriendly = regex.sub('', txt)
		
	colors = [(0,164,201), (164,201,0), (201,164,0)]
	
	W, H = size # image size
	fontsize = size[1] - 5
	print("font: " + pacifico)
	font = ImageFont.truetype(pacifico, fontsize)

	outName = os.path.join(sys.path[0], 'patches', fileFriendly + '__COLOR__.png')
	testName = outName.replace("__COLOR__", str(0))
	if not os.path.exists(testName):
		for i, color in enumerate(colors):
			background = color # white

			image = Image.new('RGBA', (W, H), background)
			draw = ImageDraw.Draw(image)

			# w, h = draw.textsize(txt) # not that accurate in getting font size
			w, h = font.getsize(txt)

			draw.text((10,(H-h)/2), txt, fill='white', font=font)
			# draw.text((10, 0), txt, (0,0,0), font=font)
			# img_resized = image.resize((188,45), Image.ANTIALIAS)
			
			# img_resized.save(save_location + '/sample.jpg')
			image.save(outName.replace("__COLOR__", str(i) ))
		
	return outName
	
if __name__ == "__main__":
	text_to_image("test img")
