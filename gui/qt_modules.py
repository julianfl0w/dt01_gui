
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
import json

def runCommand(cmd):
	return subprocess.check_output([cmd], shell=True).decode(encoding='UTF-8')

class ActionButton(QPushButton):
	def __init__(self, text, parentLayout, stylesheet = "text-align: left; "):
		super().__init__(text = text)
		self.parentLayout = parentLayout
		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.setFont(QFont('Arial', 30))
		self.setStyleSheet(stylesheet)
		self.pressed.connect(self.onPress)
		
		#self.setMaximumSize(480,320);
		
	def onPress(self):
		self.parentLayout.anyButtonPressed(self)
			
class RadioLabelButton(QPushButton):
	def __init__(self, text, parentLayout):
		super().__init__(text = text)
		selected = False
		self.parentLayout   = parentLayout
		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.setFont(QFont('Arial', 30))
		self.pressed.connect(self.select)
		self.setStyleSheet("text-align: left; ")
		#self.setMaximumSize(480,320);
				
	def select(self):
		# blank buttons are unselectable
		if self.text() != "":
			print('The button <%s> is being pressed' % self.text())
			self.selected = True
			self.setStyleSheet("text-align: left; background-color: lightblue")
			self.parentLayout.anyButtonPressed(self)
		
	def deselect(self):
		self.selected = False
		self.setStyleSheet("text-align: left; background-color: white")

class HalfNav(QHBoxLayout):
		
	def __init__(self, parentLayout, size_hint=(0.333, 0.3)):
		super().__init__()
		self.parentLayout = parentLayout
		button_scroll_folder_up   = ActionButton(text="▲", parentLayout = self, stylesheet = "")
		button_scroll_folder_down = ActionButton(text="▼", parentLayout = self, stylesheet = "")
		exit_button               = ActionButton(text="✖", parentLayout = self, stylesheet = "")
		
		exit_button.pressed.connect              (parentLayout.exit)
		button_scroll_folder_up.pressed.connect  (parentLayout.slice.up  )
		button_scroll_folder_down.pressed.connect(parentLayout.slice.down)
		
		button_scroll_folder_up  .setFixedHeight(50)
		button_scroll_folder_down.setFixedHeight(50)
		self.addWidget(button_scroll_folder_up  )
		self.addWidget(button_scroll_folder_down)
		self.addWidget(exit_button)
		self.size_hint = size_hint
	
	def anyButtonPressed(self, instance):
		pass
	
	
class NavBox(QHBoxLayout):
		
	def __init__(self, parentLayout):
		super().__init__()
		self.parentLayout = parentLayout
		button_scroll_folder_up   = ActionButton(text="▲", parentLayout = self, stylesheet = "")
		button_scroll_folder_down = ActionButton(text="▼", parentLayout = self, stylesheet = "")
		settings_button           = ActionButton(text="⚙", parentLayout = self, stylesheet = "")
		self.wifi_button          = ActionButton(text="◍", parentLayout = self, stylesheet = "")
		#self.wifi_button          = ActionButton(text="W", parentLayout = self, stylesheet = "")
		button_scroll_file_up     = ActionButton(text="▲", parentLayout = self, stylesheet = "")
		button_scroll_file_down   = ActionButton(text="▼", parentLayout = self, stylesheet = "")
		
		settings_button.pressed.connect          (parentLayout.settings)
		button_scroll_folder_up.pressed.connect  (parentLayout.folderSlice.up  )
		button_scroll_folder_down.pressed.connect(parentLayout.folderSlice.down)
		button_scroll_file_up.pressed.connect    (parentLayout.fileSlice.up    )
		button_scroll_file_down.pressed.connect  (parentLayout.fileSlice.down  )
		
		button_scroll_folder_up  .setFixedHeight(50)
		button_scroll_folder_down.setFixedHeight(50)
		button_scroll_file_up    .setFixedHeight(50)
		button_scroll_file_down  .setFixedHeight(50)
		
		#button_scroll_folder_up  .setMaximumSize(480/7, 50)
		#button_scroll_folder_down.setMaximumSize(480/7, 50)
		#button_scroll_file_up    .setMaximumSize(480/7, 50)
		#button_scroll_file_down  .setMaximumSize(480/7, 50)
		#settings_button          .setMaximumSize(480/7, 50)
		#self.wifi_button         .setMaximumSize(480/7, 50)
		
		self.addWidget(button_scroll_folder_up  )
		self.addWidget(button_scroll_folder_down)
		self.addWidget(settings_button)
		self.addWidget(self.wifi_button)
		self.addWidget(button_scroll_file_up    )
		self.addWidget(button_scroll_file_down  )
		#self.setMaximumSize(480,320);
		self.size_hint = (1, 0.3)
		
	def anyButtonPressed(self, instance):
		pass
	

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
		self.parentLayout.anyButtonPressed(instance)
	
		
		
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
		self.parentLayout.anyButtonPressed(instance)

class SelectItemFromList(QVBoxLayout):
	def __init__(self, parentLayout, items, itemsInSlice = 4, size_hint=(1.0, 1.0)):
		super().__init__()
		self.parentLayout = parentLayout
		
		self.slice = SliceViewAction(self, items, itemsInSlice)
		#self.slice.buttons[0].size_hint = size_hint
		#self.size_hint = size_hint
		
		self.navbox = HalfNav(self)
		self.addLayout(self.slice )
		self.addLayout(self.navbox )
		
	def anyButtonPressed(self, instance):
		self.parentLayout.anyButtonPressed(instance)
	
	def exit(self, instance = None):
		self.parentLayout.hide()