
import os
os.environ['KIVY_WINDOW'] = 'egl_rpi'
os.environ['KIVY_WINDOW'] = 'sdl2'
# imports
from kivy.logger import Logger, LOG_LEVELS
Logger.setLevel(LOG_LEVELS["debug"])
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window
import platform
import sys
import zmq


# fullscreen only on RPI (i use Windows otherwise)
if platform.system() == 'Linux':
        pass
        #Window.fullscreen = True

FILES_PER_SCREEN = 4

class jButton(Button):
	def __init__(self, text, app_inst):
		super().__init__(text = text, background_color = [0,0,0,0], background_down = "green")
		selected = False
		self.app_inst = app_inst

# Boxlayout is the App class

class BoxLayoutDemo(App):
	def filecallback(self, instance):
		if instance.text == "":
			return
		print('The button <%s> is being pressed' % instance.text)
		print(instance.app_inst)
		for button in instance.app_inst.button_files:
			button.selected = False
			button.background_color = [0,0,0,0]
		instance.selected = True
		instance.background_color = [1,1,1,1]
		
		sendpath = os.path.join(instance.app_inst.allPatchesDir, instance.text)
		instance.app_inst.socket.send_string(sendpath)

	def foldercallback(self, instance):
		if instance.text == "":
			return
		print('The button <%s> is being pressed' % instance.text)
		print(instance.app_inst)
		for button in instance.app_inst.button_folders:
			button.selected = False
			button.background_color = [0,0,0,0]
		instance.selected = True
		instance.background_color = [1,1,1,1]
		
		instance.app_inst.filelist = [file for file in os.listdir(os.path.join(instance.app_inst.allPatchesDir, instance.text)) if file.endswith(".json") ]
		while len(instance.app_inst.filelist) % FILES_PER_SCREEN:
			instance.app_inst.filelist += [""]
		for i, button in enumerate(instance.app_inst.button_files):
			button.text = instance.app_inst.filelist[i].replace(".json","")
		
	def filesUp(self, instance):
		instance.app_inst.filelist = instance.app_inst.filelist[-FILES_PER_SCREEN:] + instance.app_inst.filelist[:-FILES_PER_SCREEN]
		for i, button in enumerate(instance.app_inst.button_files):
			button.selected = False
			button.background_color = [0,0,0,0]
			button.text = instance.app_inst.filelist[i].replace(".json","")
		self.filecallback(instance.app_inst.button_files[0])

	def filesDown(self, instance):
		instance.app_inst.filelist = instance.app_inst.filelist[FILES_PER_SCREEN:] + instance.app_inst.filelist[:FILES_PER_SCREEN]
		for i, button in enumerate(instance.app_inst.button_files):
			button.selected = False
			button.background_color = [0,0,0,0]
			button.text = instance.app_inst.filelist[i].replace(".json","")
		self.filecallback(instance.app_inst.button_files[0])

	def foldersUp(self, instance):
		instance.app_inst.categories = instance.app_inst.categories[-FILES_PER_SCREEN:] + instance.app_inst.categories[:-FILES_PER_SCREEN]
		for i, button in enumerate(instance.app_inst.button_folders):
			button.selected = False
			button.background_color = [0,0,0,0]
			button.text = instance.app_inst.categories[i].replace(".json","")
		self.foldercallback(instance.app_inst.button_folders[0])

	def foldersDown(self, instance):
		instance.app_inst.categories = instance.app_inst.categories[FILES_PER_SCREEN:] + instance.app_inst.categories[:FILES_PER_SCREEN]
		for i, button in enumerate(instance.app_inst.button_folders):
			button.selected = False
			button.background_color = [0,0,0,0]
			button.text = instance.app_inst.categories[i].replace(".json","")
		self.foldercallback(instance.app_inst.button_folders[0])


	def build(self):

		context = zmq.Context()
		self.socket = context.socket(zmq.PUB)
		self.socket.bind("tcp://*:5555")
		
		self.allPatchesDir = os.path.join(sys.path[0], 'dx7_patches/')
		self.categories = os.listdir(self.allPatchesDir)
		while len(self.categories) % FILES_PER_SCREEN:
			self.categories += [""]
				
		self.folderbox   = BoxLayout(orientation='vertical')
		self.button_folders   = [jButton(text=self.categories[i], app_inst = self) for i in range(FILES_PER_SCREEN)]
		for button in self.button_folders:
			button.bind(on_press=self.foldercallback)
			self.folderbox.add_widget(button )
			
		self.filebox   = BoxLayout(orientation='vertical')
		self.button_files   = [jButton(text="File", app_inst = self) for i in range(FILES_PER_SCREEN)]
		for button in self.button_files:
			button.bind(on_press=self.filecallback)
			self.filebox.add_widget(button )
			
		self.foldercallback(self.button_folders[0]) #select the first one
		self.filecallback(self.button_files[0]) #select the first one
		
		
		button_scroll_folder_up   = jButton(text="UP", app_inst = self)
		button_scroll_folder_up.bind(on_press=self.foldersUp)
		button_scroll_folder_down = jButton(text="DOWN", app_inst = self)
		button_scroll_folder_down.bind(on_press=self.foldersDown)
		
		button_scroll_file_up   = jButton(text="UP", app_inst = self)
		button_scroll_file_up.bind(on_press=self.filesUp)
		button_scroll_file_down = jButton(text="DOWN", app_inst = self)
		button_scroll_file_down.bind(on_press=self.filesDown)
		
		self.navbox    = BoxLayout(orientation='horizontal')
		self.navbox.add_widget(button_scroll_folder_up  )
		self.navbox.add_widget(button_scroll_folder_down)
		self.navbox.add_widget(button_scroll_file_up    )
		self.navbox.add_widget(button_scroll_file_down  )
		self.navbox.size_hint = (1, 0.3)

   
		self.filefolderbox   = BoxLayout(orientation='horizontal')
		self.filefolderbox.add_widget(self.folderbox )
		self.filefolderbox.add_widget(self.filebox )
		
		self.verticalBox	 = BoxLayout(orientation='vertical')
		self.verticalBox.add_widget(self.filefolderbox )
		self.verticalBox.add_widget(self.navbox )

		return self.verticalBox

# Instantiate and run the kivy app

if __name__ == '__main__':

	BoxLayoutDemo().run()

 
