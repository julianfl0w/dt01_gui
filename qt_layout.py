
# imports
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
import platform
import os
import sys
import zmq
import platform

# fullscreen only on RPI (i use Windows otherwise)
#if platform.system() == 'Linux':
#	Window.fullscreen = True

FILES_PER_SCREEN = 4

class jButton(QPushButton):
	def __init__(self, text, app_inst):
		super().__init__(text = text)
		selected = False
		self.app_inst = app_inst
		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.setFont(QFont('Arial', 30))

class MainWindow(QWidget):

	def filecallback(self, instance = None):
		if instance == None: instance = self.sender()
		if instance.text() == "":
			return
		print('The button <%s> is being pressed' % instance.text())
		print(instance.app_inst)
		for button in instance.app_inst.button_files:
			button.selected = False
			button.setStyleSheet("background-color: white")
		instance.selected = True
		#instance.setStyleSheet("background-color: lightblue")
		instance.setStyleSheet("background-color: blue")
		
		sendpath = os.path.join(instance.app_inst.allPatchesDir, instance.app_inst.activeFolder, instance.text()) + ".json"
		instance.app_inst.socket.send_string(sendpath)

	def foldercallback(self, instance = None):
		if instance == None: instance = self.sender()
		if instance.text() == "":
			return
		print('The button <%s> is being pressed' % instance.text())
		print(instance.app_inst)
		for button in instance.app_inst.button_folders:
			button.selected = False
			button.setStyleSheet("background-color: white")
		instance.selected = True
		#instance.setStyleSheet("background-color: lightblue")
		instance.setStyleSheet("background-color: blue")
		instance.app_inst.activeFolder = instance.text()
		instance.app_inst.filelist = [file for file in sorted(os.listdir(os.path.join(instance.app_inst.allPatchesDir, instance.text()))) if file.endswith(".json") ]
		while len(instance.app_inst.filelist) % FILES_PER_SCREEN:
			instance.app_inst.filelist += [""]
		for i, button in enumerate(instance.app_inst.button_files):
			button.setText(instance.app_inst.filelist[i].replace(".json",""))
		
	def filesUp(self, instance = None):
		if instance == None: instance = self.sender()
		instance.app_inst.filelist = instance.app_inst.filelist[-FILES_PER_SCREEN:] + instance.app_inst.filelist[:-FILES_PER_SCREEN]
		for i, button in enumerate(instance.app_inst.button_files):
			button.selected = False
			button.setStyleSheet("background-color: white")
			button.setText(instance.app_inst.filelist[i].replace(".json",""))
		self.filecallback(instance.app_inst.button_files[0])

	def filesDown(self, instance = None):
		if instance == None: instance = self.sender()
		instance.app_inst.filelist = instance.app_inst.filelist[FILES_PER_SCREEN:] + instance.app_inst.filelist[:FILES_PER_SCREEN]
		for i, button in enumerate(instance.app_inst.button_files):
			button.selected = False
			button.setStyleSheet("background-color: white")
			button.setText(instance.app_inst.filelist[i].replace(".json",""))
		self.filecallback(instance.app_inst.button_files[0])

	def foldersUp(self, instance = None):
		if instance == None: instance = self.sender()
		instance.app_inst.categories = instance.app_inst.categories[-FILES_PER_SCREEN:] + instance.app_inst.categories[:-FILES_PER_SCREEN]
		for i, button in enumerate(instance.app_inst.button_folders):
			button.selected = False
			button.setStyleSheet("background-color: white")
			button.setText(instance.app_inst.categories[i].replace(".json",""))
		self.foldercallback(instance.app_inst.button_folders[0])

	def foldersDown(self, instance = None):
		if instance == None: instance = self.sender()
		instance.app_inst.categories = instance.app_inst.categories[FILES_PER_SCREEN:] + instance.app_inst.categories[:FILES_PER_SCREEN]
		for i, button in enumerate(instance.app_inst.button_folders):
			button.selected = False
			button.setStyleSheet("background-color: white")
			button.setText(instance.app_inst.categories[i].replace(".json",""))
		self.foldercallback(instance.app_inst.button_folders[0])

	def settings(self, instance = None):
		sys.exit()


	def __init__(self, parent=None):
		super().__init__(parent)
		
		context = zmq.Context()
		self.socket = context.socket(zmq.PUB)
		self.socket.bind("tcp://*:5555")
		
		self.allPatchesDir = os.path.join(sys.path[0], 'patches/')
		self.categories = sorted(os.listdir(self.allPatchesDir))
		while len(self.categories) % FILES_PER_SCREEN:
			self.categories += [""]
				
		self.folderbox   = QVBoxLayout()
		self.button_folders   = [jButton(text=self.categories[i], app_inst = self) for i in range(FILES_PER_SCREEN)]
		for button in self.button_folders:
			button.pressed.connect(self.foldercallback)
			self.folderbox.addWidget(button )
			
		self.filebox   = QVBoxLayout()
		self.button_files   = [jButton(text="File", app_inst = self) for i in range(FILES_PER_SCREEN)]
		for button in self.button_files:
			button.pressed.connect(self.filecallback)
			self.filebox.addWidget(button )
			
		self.foldercallback(self.button_folders[0]) #select the first one
		self.filecallback(self.button_files[0]) #select the first one
		
		
		button_scroll_folder_up   = jButton(text="▲", app_inst = self)
		button_scroll_folder_up.pressed.connect(self.foldersUp)
		button_scroll_folder_down = jButton(text="▼", app_inst = self)
		button_scroll_folder_down.pressed.connect(self.foldersDown)
		
		settings_button   = jButton(text="⚙", app_inst = self)
		settings_button.pressed.connect(self.settings)
		
		button_scroll_file_up   = jButton(text="▲", app_inst = self)
		button_scroll_file_up.pressed.connect(self.filesUp)
		button_scroll_file_down = jButton(text="▼", app_inst = self)
		button_scroll_file_down.pressed.connect(self.filesDown)
		
		self.navbox    = QHBoxLayout()
		button_scroll_folder_up  .setFixedHeight(50)
		button_scroll_folder_down.setFixedHeight(50)
		button_scroll_file_up    .setFixedHeight(50)
		button_scroll_file_down  .setFixedHeight(50)
		self.navbox.addWidget(button_scroll_folder_up  )
		self.navbox.addWidget(button_scroll_folder_down)
		self.navbox.addWidget(settings_button)
		self.navbox.addWidget(button_scroll_file_up    )
		self.navbox.addWidget(button_scroll_file_down  )
		self.navbox.size_hint = (1, 0.3)

   
		self.filefolderbox   = QHBoxLayout()
		self.filefolderbox.addLayout(self.folderbox )
		self.filefolderbox.addLayout(self.filebox )
		
		self.verticalBox	 = QVBoxLayout()
		self.verticalBox.addLayout(self.filefolderbox )
		self.verticalBox.addLayout(self.navbox )

		self.setLayout(self.verticalBox)

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

 
