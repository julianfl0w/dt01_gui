# Sample Kivy app demonstrating the working of Box layout

 

# imports

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

 

class jButton(Button):
	def __init__(self, text, app_inst):
		super().__init__(text = text, background_color = [0,0,0,0])
		selected = False
		self.app_inst = app_inst

# Boxlayout is the App class

class BoxLayoutDemo(App):
	def filecallback(self, instance):
		print('The button <%s> is being pressed' % instance.text)
		print(instance.app_inst)
		for button in instance.app_inst.button_files:
			button.selected = False
			button.background_color = [0,0,0,0]
		instance.background_color = [1,1,1,1]

	def foldercallback(self, instance):
		print('The button <%s> is being pressed' % instance.text)
		print(instance.app_inst)
		for button in instance.app_inst.button_folders:
			button.selected = False
			button.background_color = [0,0,0,0]
		instance.background_color = [1,1,1,1]

	def build(self):

		FILES_PER_SCREEN = 4
		
		self.folderbox   = BoxLayout(orientation='vertical')
		self.button_folders   = [jButton(text="Folder", app_inst = self) for i in range(FILES_PER_SCREEN)]
		for button in self.button_folders:
			button.bind(on_press=self.foldercallback)
			self.folderbox.add_widget(button )
		self.foldercallback(self.button_folders[0]) #select the first one
			
		self.filebox   = BoxLayout(orientation='vertical')
		self.button_files   = [jButton(text="File", app_inst = self) for i in range(FILES_PER_SCREEN)]
		for button in self.button_files:
			button.bind(on_press=self.filecallback)
			self.filebox.add_widget(button )
		self.filecallback(self.button_files[0]) #select the first one
		
		
		self.navbox    = BoxLayout(orientation='horizontal')
		button_scroll_folder_up   = jButton(text="UP", app_inst = self)
		button_scroll_folder_down = jButton(text="DOWN", app_inst = self)
		button_scroll_file_up     = jButton(text="UP", app_inst = self)
		button_scroll_file_down   = jButton(text="DOWN", app_inst = self)
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

 