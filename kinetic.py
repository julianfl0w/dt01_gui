#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from text_to_image import *

dirButtons = dict()
fileButtons = dict()
dir_last_released = 0
file_last_released = 0
BUTTON_WIDTH  = 200
BUTTON_HEIGHT = 50

		
class JulianButton(QPushButton):

	def __init__(self, name, parentLayout, childLayout, index):
		super().__init__()
		labelImage = text_to_image(name, size=(BUTTON_WIDTH, BUTTON_HEIGHT))
		_icon = QIcon(labelImage.replace("__COLOR__", '0'))
		self.setIcon(_icon)
		self.setIconSize(QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
		self.parentLayout = parentLayout
		self.childLayout  = childLayout
		self.colorTuple = (labelImage.replace("__COLOR__", '0'), labelImage.replace("__COLOR__", '1'), labelImage.replace("__COLOR__", '2'))
		self.activeColor = 0
		self.i = index
		parentLayout.addRow(self)
			
	def setColor(self, color):
		if self.activeColor != color:
			self.setIcon(QIcon(self.colorTuple[color]))
			self.activeColor = 0
			
class MainWindow(QWidget):

	global dirButtons
	def dirReleased(self):
		sender = self.sender()
		
		sender.setIcon(QIcon(self.colorTuple[2]))
		sender.setIconSize(QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
		
		self.activeColor = 2
		# apply patch now
		global dir_last_released
		dir_last_released = id(sender)
			
	
	def dirPressed(self):
		global dir_last_released
		sender = self.sender()
		
		for k in range(sender.parentLayout.rowCount()):
			sender.parentLayout.itemAt(k).widget().setColor(0)
		
		sender.setIcon(QIcon(sender.colorTuple[1]))
		sender.setIconSize(QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
		sender.activeColor = 1
		
		self.Stack.setCurrentIndex(sender.i)
		dir_last_released = id(sender)
		

	def patchPressed(self):
		global patch_last_released
		sender = self.sender()
		
		for k in range(sender.parentLayout.rowCount()):
			sender.parentLayout.itemAt(k).widget().setColor(0)
		
		sender.setIcon(QIcon(sender.colorTuple[1]))
		sender.setIconSize(QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
		sender.activeColor = 1
		
		patch_last_released = id(sender)
		
	def __init__(self, parent=None):
		super().__init__(parent)
		self.folderScroll = QScrollArea()
		self.Stack = QStackedWidget (self)
		self.hlayout = QHBoxLayout(self)
		self.hlayout.addWidget(self.folderScroll)

		self.folderScroll_widget = QWidget()
		self.folderScroll_layout = QFormLayout(self.folderScroll_widget)
		
		dirno = 0
		for i, x in enumerate(os.walk(os.path.join(sys.path[0], 'patches/'))):
			# 0th return is some meta bullshit	
			if i == 0: 
				continue
			buttonLabel = os.path.basename(x[0]) 

			#each directory gets a self.fileScroll
			self.fileScroll = QScrollArea()
			self.fileScroll_widget = QWidget()
			self.fileScroll_layout = QFormLayout(self.fileScroll_widget)
			self.fileScroll.setWidget(self.fileScroll_widget)
			self.fileScroll.setContentsMargins(0, 0, 0, 0)
			
			#my_button.released.connect(self.dirReleased) 
			dirButton = JulianButton(buttonLabel, self.folderScroll_layout, self.fileScroll_widget, i-1)
			dirButton.pressed.connect(self.dirPressed) 
			
			for j, file in enumerate(os.listdir(x[0])):
				if file.endswith(".json"):
					buttonLabel = file.replace('.json', '') 
					patchButton = JulianButton(buttonLabel, self.fileScroll_layout, None, j)
					patchButton.pressed.connect(self.patchPressed) 
					
			self.Stack.addWidget (self.fileScroll_widget)
			
			
		self.folderScroll.setWidget(self.folderScroll_widget)
		self.folderScroll.setContentsMargins(0, 0, 0, 0)
		
		self.hlayout.addWidget(self.Stack)
		
		QScroller.grabGesture(
			self.folderScroll.viewport(), QScroller.LeftMouseButtonGesture
		)
		
		
if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.showFullScreen()
	sys.exit(app.exec_())
