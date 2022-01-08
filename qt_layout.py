
# imports
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
import platform
import os
import sys
import zmq
import platform
import subprocess

# fullscreen only on RPI (i use Windows otherwise)
#if platform.system() == 'Linux':
#	Window.fullscreen = True

class ActionButton(QPushButton):
	def __init__(self, text, parentLayout):
		super().__init__(text = text)
		self.parentLayout = parentLayout
		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.setFont(QFont('Arial', 30))
		
class RadioLabelButton(QPushButton):
	def __init__(self, text, parentLayout):
		super().__init__(text = text)
		selected = False
		self.parentLayout   = parentLayout
		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.setFont(QFont('Arial', 30))
		self.pressed.connect(self.select)
				
	def select(self):
		# blank buttons are unselectable
		if self.text() != "":
			print('The button <%s> is being pressed' % self.text())
			self.selected = True
			self.setStyleSheet("background-color: blue")
			self.parentLayout.anyButtonPressed(self)
		
	def deselect(self):
		self.selected = False
		self.setStyleSheet("background-color: white")

class HalfNav(QHBoxLayout):
		
	def __init__(self, parentLayout):
		super().__init__()
		self.parentLayout = parentLayout
		button_scroll_folder_up   = ActionButton(text="▲", parentLayout = self)
		button_scroll_folder_down = ActionButton(text="▼", parentLayout = self)
		exit_button           = ActionButton(text="✖", parentLayout = self)
		
		exit_button.pressed.connect          (parentLayout.exit)
		button_scroll_folder_up.pressed.connect  (parentLayout.slice.up  )
		button_scroll_folder_down.pressed.connect(parentLayout.slice.down)
		
		button_scroll_folder_up  .setFixedHeight(50)
		button_scroll_folder_down.setFixedHeight(50)
		self.addWidget(button_scroll_folder_up  )
		self.addWidget(button_scroll_folder_down)
		self.addWidget(exit_button)
		self.size_hint = (1, 0.3)
		
class NavBox(QHBoxLayout):
		
	def __init__(self, parentLayout):
		super().__init__()
		self.parentLayout = parentLayout
		button_scroll_folder_up   = ActionButton(text="▲", parentLayout = self)
		button_scroll_folder_down = ActionButton(text="▼", parentLayout = self)
		settings_button           = ActionButton(text="⚙", parentLayout = self)
		button_scroll_file_up     = ActionButton(text="▲", parentLayout = self)
		button_scroll_file_down   = ActionButton(text="▼", parentLayout = self)
		
		settings_button.pressed.connect          (parentLayout.settings)
		button_scroll_folder_up.pressed.connect  (parentLayout.folderSlice.up  )
		button_scroll_folder_down.pressed.connect(parentLayout.folderSlice.down)
		button_scroll_file_up.pressed.connect    (parentLayout.fileSlice.up    )
		button_scroll_file_down.pressed.connect  (parentLayout.fileSlice.down  )
		
		button_scroll_folder_up  .setFixedHeight(50)
		button_scroll_folder_down.setFixedHeight(50)
		button_scroll_file_up    .setFixedHeight(50)
		button_scroll_file_down  .setFixedHeight(50)
		self.addWidget(button_scroll_folder_up  )
		self.addWidget(button_scroll_folder_down)
		self.addWidget(settings_button)
		self.addWidget(button_scroll_file_up    )
		self.addWidget(button_scroll_file_down  )
		self.size_hint = (1, 0.3)

class SliceViewBase(QVBoxLayout):
		
	def __init__(self, parentLayout, items, itemsInSlice = 4):
		super().__init__()
		# make 4 buttons labelled with the first 4 items
		self.items   = items
		self.itemsInSlice = itemsInSlice
		#make sure there are at least 4 items
		while len(self.items) % itemsInSlice:
			self.items += [""]
			
		self.selectedText = ""
		self.parentLayout = parentLayout
			
	def up(self, instance = None):
		self.items = self.items[-self.itemsInSlice:] + self.items[:-self.itemsInSlice]
		self.updateButtons()
				
	def down(self, instance = None):
		self.items = self.items[self.itemsInSlice:] + self.items[:self.itemsInSlice]
		self.updateButtons()
		
	def setItems(self, items):
		self.items = items
		self.updateButtons()
		
	def setItemsFromDirectory(self, directory):
		self.basePath = directory
		self.items = [file for file in sorted(os.listdir(directory))] # if file.endswith(".json") 
		self.items = [i.replace(".json","") for i in self.items]
		#make sure there are at least 4 items
		while len(self.items) % self.itemsInSlice:
			self.items += [""]
		self.updateButtons()
		
# view a slice (subwindow) of options as clickable buttons
class SliceViewAction(SliceViewBase):
		
	def __init__(self, parentLayout, items, itemsInSlice = 4):
		super().__init__(parentLayout, items, itemsInSlice)
		
		self.buttons = [ActionButton(text=t, parentLayout = self) for t in self.items[:itemsInSlice]]
		for button in self.buttons:
			self.addWidget(button )
	
	def updateButtons(self):
		for i, button in enumerate(self.buttons):
			button.setText(self.items[i])
		
	# gets called on button selection
	def anyButtonPressed(self, instance):
		self.selectedText = instance.text()
		# call parent layout callback
		self.parentLayout.anyButtonPressed(self)
	
		
		
# view a slice (subwindow) of options as clickable buttons
class SliceViewSelect(SliceViewBase):
		
	def __init__(self, parentLayout, items, itemsInSlice = 4):
		super().__init__(parentLayout, items, itemsInSlice)
		
		self.buttons = [RadioLabelButton(text=t, parentLayout = self) for t in self.items[:itemsInSlice]]
		for button in self.buttons:
			self.addWidget(button )
	
	def updateButtons(self):
		for i, button in enumerate(self.buttons):
			button.setText(self.items[i])
			if button.text() == self.selectedText:
				button.select()
			else:
				button.deselect()
		
	# gets called on button selection
	def anyButtonPressed(self, instance):
		self.selectedText = instance.text()
		
		# deselect all other buttons
		for button in self.buttons:
			if button != instance:
				button.deselect()
				
		# call parent layout callback
		self.parentLayout.anyButtonPressed(self)

class SelectItemFromList(QVBoxLayout):
	def __init__(self, parentLayout, items, itemsInSlice = 4):
		super().__init__()
		self.parentLayout = parentLayout
		
		self.slice = SliceViewAction(self, items, itemsInSlice)
		self.slice.buttons[0].size_hint = (0.5, 1.0)
		
		self.navbox = HalfNav(self)
		self.addLayout(self.slice )
		self.addLayout(self.navbox )
		
	def exit(self, instance = None):
		self.parentLayout.hide()
		
class SSIDWindow(QWidget):
	def anyButtonPressed(self, instance):
		print(instance.text())
		pass
		#if instance == self.folderSlice:
		#	self.fileSlice.setItemsFromDirectory(os.path.join(self.folderSlice.basePath, self.folderSlice.selectedText))
		#elif instance == self.fileSlice:
		#	sendpath = os.path.join(instance.basePath, instance.selectedText) + ".json"
		#	self.socket.send_string(sendpath)
			
			
	
	def __init__(self, parent=None):
		super().__init__(parent)
		
		SSIDs = subprocess.check_output(["sudo iw dev wlan0 scan | grep 'SSID:'"], shell=True).decode(encoding='UTF-8')
		SSIDs = SSIDs.split('\n')
		SSIDs = [str(s.replace('\tSSID: ', '')) for s in SSIDs]
		SSIDs = [s for s in SSIDs if s != '']
		print(SSIDs)
		self.setLayout(SelectItemFromList(self, SSIDs))
		
	
class MainWindow(QWidget):

	def anyButtonPressed(self, instance):
		if instance == self.folderSlice:
			self.fileSlice.setItemsFromDirectory(os.path.join(self.folderSlice.basePath, self.folderSlice.selectedText))
		elif instance == self.fileSlice:
			sendpath = os.path.join(instance.basePath, instance.selectedText) + ".json"
			self.socket.send_string(sendpath)
			
			
	def settings(self, instance = None):
		if "aarch64" in platform.platform():
			self.SSIDWindow.showFullScreen()
		else:
			self.SSIDWindow.show()
		#sys.exit()
	
	def __init__(self, parent=None):
		super().__init__(parent)
		
		context = zmq.Context()
		self.socket = context.socket(zmq.PUB)
		self.socket.bind("tcp://*:5555")
		
		self.allCategoriesDir = os.path.join(sys.path[0], 'patches/')
		self.folderSlice = SliceViewSelect(self, [""]*4)
		self.folderSlice.buttons[0].size_hint = (0.5, 1.0)
		self.folderSlice.setItemsFromDirectory(self.allCategoriesDir)
		self.fileSlice   = SliceViewSelect(self, [""]*4) # start fileslice empty for now
		
		self.folderSlice.buttons[0].select() #select the first one
		self.fileSlice.buttons[0].select()  #select the first one
		
		self.navbox = NavBox(self)
   
		self.filefolderSlice   = QHBoxLayout()
		self.filefolderSlice.addLayout(self.folderSlice )
		self.filefolderSlice.addLayout(self.fileSlice )
		
		self.verticalBox	 = QVBoxLayout()
		self.verticalBox.addLayout(self.filefolderSlice )
		self.verticalBox.addLayout(self.navbox )

		self.setLayout(self.verticalBox)
		
		self.SSIDWindow = SSIDWindow()
		
		return None

if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	print(platform.platform())
	if "aarch64" in platform.platform():
		main_window.showFullScreen()
	else:
		main_window.show()
		
	sys.exit(app.exec_())

 
