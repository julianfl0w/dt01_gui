#!/usr/bin/env python3
import sys
import os
import zmq
import cv2
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from text_to_image import *

import subprocess
dirButtons = dict()
fileButtons = dict()
dir_last_released = 0
file_last_released = 0
BUTTON_WIDTH  = 200
BUTTON_HEIGHT = 50

		
class JulianButton(QPushButton):

	def __init__(self, name, parentLayout, childLayout, index, path, socket = None):
		super().__init__()
		self.i = index
		self.socket = socket
		self.path = path
		os.makedirs("images", exist_ok=True)
		imageFilename = os.path.join("images", path, ".png")
		labelImage = text_to_image(name, size=(BUTTON_WIDTH, BUTTON_HEIGHT))	
		_icon = QIcon(labelImage.replace("__COLOR__", '0'))
		self.setIcon(_icon)
		self.setIconSize(QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
		self.parentLayout = parentLayout
		self.childLayout  = childLayout
		self.colorTuple = (labelImage.replace("__COLOR__", '0'), labelImage.replace("__COLOR__", '1'), labelImage.replace("__COLOR__", '2'))
		self.activeColor = 0
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
		sender.socket.send_string(sender.path)
		
		print(sender.path)
		
		bs = subprocess.check_output(["ps -aef | grep python"], shell=True).decode('utf-8')
		if bs.count('\n') < 4:
			os.system("sudo taskset 0x00000004 sudo python3 /home/pi/dt01_gui/patch.py &")
		
	def __init__(self, parent=None):
		super().__init__(parent)
		self.Stack = QStackedWidget (self)
		self.hlayout = QHBoxLayout(self)
		
		self.folderScroll = QScrollArea()
		self.folderScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.folderScroll.horizontalScrollBar().setEnabled(False);
		self.hlayout.addWidget(self.folderScroll)
		self.folderScroll_widget = QWidget()
		self.folderScroll_layout = QFormLayout(self.folderScroll_widget)
		self.folderScroll.setContentsMargins(0, 0, 0, 0)
		QScroller.grabGesture(
			self.folderScroll.viewport(), QScroller.LeftMouseButtonGesture
		)
		
		context = zmq.Context()
		socket = context.socket(zmq.PUB)
		socket.bind("tcp://*:5555")
		
		#os.system("sudo taskset 0x00000004 sudo python3 /home/pi/dt01_gui/patch.py &")
		
		dirno = 0
		allPatchesDir = os.path.join(sys.path[0], 'dx7_patches/')
		for dirno, dirname in enumerate(sorted(os.listdir(allPatchesDir))):
		
			# for now
			#if dirno > 10:
			#	break
			print("dirname:"  + dirname)
			buttonLabel = os.path.basename(dirname) 

			#each directory gets a self.fileScroll
			self.fileScroll = QScrollArea()
			self.fileScroll_widget = QWidget()
			self.fileScroll_layout = QFormLayout(self.fileScroll_widget)
			self.fileScroll.setWidget(self.fileScroll_widget)
			self.fileScroll.setContentsMargins(0, 0, 0, 0)
			
			QScroller.grabGesture(
				self.fileScroll.viewport(), QScroller.LeftMouseButtonGesture
			)
			
			#my_button.released.connect(self.dirReleased) 
			dirButton = JulianButton(buttonLabel, self.folderScroll_layout, self.fileScroll_widget, dirno, dirname)
			dirButton.pressed.connect(self.dirPressed) 
			
			
			i = 0
			for file in os.listdir(os.path.join(allPatchesDir, dirname)):
				if file.endswith(".json"):
					filepath    = os.path.join(allPatchesDir, dirname, file)
					buttonLabel = file.replace('.json', '') 
					patchButton = JulianButton(buttonLabel, self.fileScroll_layout, self.fileScroll_widget, i, filepath, socket)
					i+=1
					patchButton.pressed.connect(self.patchPressed) 
					
			self.Stack.addWidget (self.fileScroll_widget)
			
		# set the widget after it has been set up
		self.folderScroll.setWidget(self.folderScroll_widget)
		
		self.hlayout.addWidget(self.Stack)
		
		
		
if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.showFullScreen()
	sys.exit(app.exec_())
