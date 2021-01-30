import sys
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from text_to_image import *

allpatches = dict()
last_released = 0
BUTTON_WIDTH  = 200
BUTTON_HEIGHT = 50

class MainWindow(QWidget):

	global allpatches
	def showReleased(self):
		global allpatches
		sender = self.sender()
		my_button, colorTuple, x = allpatches[id(sender)]
		
		sender.setIcon(QIcon(colorTuple[2]))
		sender.setIconSize(QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
		
		global last_released
		allpatches[id(my_button)] = (my_button, colorTuple, 2)
		# apply patch now
		last_released = id(sender)
		
	def showPressed(self):
		global last_released
		sender = self.sender()
		my_button, colorTuple, x = allpatches[id(sender)]
		sender.setIcon(QIcon(colorTuple[1]))
		sender.setIconSize(QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
		allpatches[id(sender)] = (sender, colorTuple, 1)
		
		# apply patch now
		try: 
			my_button, colorTuple, x = allpatches[last_released]
			my_button.setIcon(QIcon(colorTuple[0]))
			x = 0
			allpatches[id(my_button)] = (my_button, colorTuple, x)
		except:
			pass
		
		#for key, value in allpatches.items():
		#	my_button, colorTuple, x = value
		#	if id(my_button) == id(sender):
		#		continue
		#	if x != 0:
		#		my_button.setIcon(QIcon(colorTuple[0]))
		#		x = 0
		#		allpatches[id(my_button)] = (my_button, colorTuple, x)
		
	def __init__(self, parent=None):
		super().__init__(parent)
		scroll_area = QScrollArea()
		#scroll_area.setMinimumWidth(3000)
		layout = QGridLayout(self)
		layout.addWidget(scroll_area)

		scroll_widget = QWidget()
		scroll_layout = QFormLayout(scroll_widget)
		
		global allpatches

		for i in range(30):
		
			buttonLabel = 'Label{}'.format(i)
			labelImage = text_to_image(buttonLabel)
			_icon = QIcon(labelImage.replace("__COLOR__", '0'))
			my_button = QPushButton()
			my_button.setIcon(_icon)
			my_button.setIconSize(QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
			my_button.pressed.connect(self.showPressed) 
			my_button.released.connect(self.showReleased) 
			scroll_layout.addRow(my_button)
			colorTuple = (labelImage.replace("__COLOR__", '0'), labelImage.replace("__COLOR__", '1'), labelImage.replace("__COLOR__", '2'))
			allpatches[id(my_button)] = [my_button, colorTuple, 0]

		scroll_area.setWidget(scroll_widget)

		QScroller.grabGesture(
			scroll_area.viewport(), QScroller.LeftMouseButtonGesture
		)
		
		
if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.showFullScreen()
	sys.exit(app.exec_())
