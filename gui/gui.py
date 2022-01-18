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
from qt_modules import *
from rpiWifi import *
import socket
import git
import datetime

# git stuff
repo = git.Repo("/home/pi/dtfm")
main = repo.head.reference
commitDate = str(datetime.datetime.fromtimestamp(main.commit.committed_date))

def conditionalShow(wind):
	if "aarch64" in platform.platform():
		wind.showFullScreen()
	else:
		wind.show()

class TextEntryWindow(QWidget):
	
	def centerWindow(self):
		qtRectangle = self.frameGeometry()
		centerPoint = QDesktopWidget().availableGeometry().center()
		y = centerPoint.y()
		print("y:" + str(y))
		y /= 2
		centerPoint.setY(int(y))
		qtRectangle.moveCenter(centerPoint)
		self.move(qtRectangle.topLeft())

	def returnText(self):
		self.callback(self.passwordEdit.text())
		self.exit()
		
	def btnstate(self,b):
		if b.isChecked():
			self.passwordEdit.setEchoMode(QLineEdit.Normal)
		else:
			self.passwordEdit.setEchoMode(QLineEdit.Password)
	
	def exit(self):
		os.system("killall onboard")
		#conditionalShow(self.parent)
		self.close()
		
	
	def __init__(self, essid = "wifi", parent = None, callback = None):
		print("Creating TEW")
		super().__init__(parent)
		self.parent = parent
		self.callback = callback
		self.passwordEdit = QLineEdit(self)
		self.passwordEdit.returnPressed.connect(self.returnText)
		#self.bottomHalf = QFrame(self)
		self.layout   = QVBoxLayout()
		self.label    = QLabel(self)
		self.label.setText("Enter Password for " + essid)
		
		self.showPasswordCheckBox = QCheckBox("Show Password")
		self.showPasswordCheckBox.stateChanged.connect(lambda:self.btnstate(self.showPasswordCheckBox))
		self.showPasswordCheckBox.setChecked(False)
		self.btnstate(self.showPasswordCheckBox)
		self.cancelButton = QPushButton(text="✖")
		
		self.label               .setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.passwordEdit        .setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.showPasswordCheckBox.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.cancelButton        .setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		
		self.showWithCancelLayout   = QHBoxLayout()
		self.cancelButton.pressed.connect(self.exit)
		self.showWithCancelLayout.addWidget(self.showPasswordCheckBox)
		self.showWithCancelLayout.addWidget(self.cancelButton)
		
		self.layout.addWidget(self.label       )
		self.layout.addWidget(self.passwordEdit)
		self.layout.addLayout(self.showWithCancelLayout)
		#self.layout.addWidget(self.bottomHalf)
	
		onboardPath  = "/home/pi/dtfm/gui/onboard/"
		layoutsPath  = os.path.join(onboardPath, "layouts")
		themePath    = os.path.join(onboardPath, "themes")
		layoutOption = " -l " + os.path.join(layoutsPath,"Phone")
		themeOption  = " -t " + os.path.join(themePath,"ModelM.theme")
		onboardStartCommand = "onboard " + layoutOption + themeOption + " -s 480x160 -x 0 -y 160 &"
		print(onboardStartCommand)
		os.system(onboardStartCommand)
		#os.system("xdotool search \"onboard\" windowactivate --sync &")
		self.setLayout(self.layout)
		
		self.setFixedWidth(480)
		self.setFixedHeight(160)
				
		self.centerWindow()
		
		self.setWindowFlag(Qt.FramelessWindowHint)
		print("Done Creating TEW")
		return None

class SSIDWindow(QWidget):
	def connect(self, passwd):
		ESSID = self.hostDict["ESSID"]
		while len(passwd) < 8:
			passwd += "X"
		connectToWifi(ESSID, passwd)
		self.close()

	def connectToHost(self, hostDict):
		self.hostDict = hostDict
		print(json.dumps(hostDict, indent = 4))
		if hostDict.get("Authentication Suites (1)") == "PSK":
			self.tew = TextEntryWindow(parent = None, callback = self.connect, essid = hostDict.get("ESSID")) # a window cannot have another window as parent. this kills it
			conditionalShow(self.tew )
		else:
			connectToWifi(self.hostDict["ESSID"], "", blocking = False)
		self.close()
			
	
	def anyButtonPressed(self, instance):
		print(instance.text())
		ssid, freq, address = instance.text().split("✵")
		for host in self.layout.slice.hosts:
			if address == host.get("ADDRESS"):
				self.connectToHost(host)
				break
		#if instance == self.folderSlice:
		#	self.fileSlice.setItemsFromDirectory(os.path.join(self.folderSlice.basePath, self.folderSlice.selectedText))
		#elif instance == self.fileSlice:
		#	sendpath = os.path.join(instance.basePath, instance.selectedText) + ".json"
		#	self.socket.send_string(sendpath)
			
	def scanSSIDs(self):
		
		allHosts = getAvailableNetworks()
		
		SSIDs = [hostDict.get("ESSID").replace("\"","") for hostDict in allHosts]
		FREQs = [hostDict.get("Frequency").split(" ")[0].replace("\"","") for hostDict in allHosts]
		ADDRs = [hostDict.get("ADDRESS") for hostDict in allHosts]
		#SSIDs = [s for s in SSIDs if s != ""]
		print(SSIDs)
		ssid_freq = []
		for s, f, a in zip(SSIDs, FREQs, ADDRs):
			ssid_freq += [s + "✵" + f + "✵" + a]
		self.layout.slice.setItems(ssid_freq)
		self.layout.slice.hosts=allHosts
		
	def __init__(self, parent=None):
		super().__init__(parent)
		self.layout = SelectItemFromList(self, [""])
		self.setLayout(self.layout)
		self.scanSSIDs()
		
			
		
class SettingsWindow(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(("8.8.8.8", 80))
		ipstring = s.getsockname()[0] 
		self.layout = SelectItemFromList(self, ["WiFi", ipstring, commitDate, "Reboot", "Quit"])
		self.setLayout(self.layout)
		
	def anyButtonPressed(self, instance):
		print(instance.text())
		txt = instance.text()
		if txt == "WiFi":
			SSIDWindow_inst = SSIDWindow()
			conditionalShow(SSIDWindow_inst)
		if txt == "Reboot":
			os.system("sudo reboot")
		if txt == "Quit":
			sys.exit()
		
class MainWindow(QWidget):

	def anyButtonPressed(self, instance):
		layout = instance.parentLayout
		if layout == self.folderSlice:
			self.fileSlice.setItemsFromDirectory(os.path.join(self.folderSlice.basePath, self.folderSlice.selectedText))
		elif layout == self.fileSlice:
			sendpath = os.path.join(layout.basePath, layout.selectedText) + ".json"
			self.socket.send_string(sendpath)
			
			
	def settings(self, instance = None):
		conditionalShow(SettingsWindow())
		#self.hide()
	
	def __init__(self, parent=None):
		super().__init__(parent)
		
		context = zmq.Context()
		self.socket = context.socket(zmq.PUB)
		self.socket.bind("tcp://*:5555")
		
		self.allCategoriesDir = os.path.join(sys.path[0], '..', 'patches/')
		self.folderSlice = SliceViewSelect(self, [""]*4)
		self.folderSlice.buttons[0].size_hint = (0.5, 1.0)
		self.folderSlice.buttons[0].setMaximumSize = (220, 160)
		self.folderSlice.setItemsFromDirectory(self.allCategoriesDir)
		self.fileSlice   = SliceViewSelect(self, [""]*4) # start fileslice empty for now
		self.fileSlice.buttons[0].setMaximumSize = (220, 160)
		
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
		
		return None
	def checkWifi(self):
		essid = getConnectedSSID()
		if len(essid):
			self.navbox.wifi_button.setStyleSheet("background-color: green")
		else:
			self.navbox.wifi_button.setStyleSheet("background-color: red")
		
		
def CheckReturn(retval):
	print(retval)
	
if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	#tew = TextEntryWindow(None, CheckReturn)
	#print(platform.platform())
	conditionalShow(main_window)
		
	timer = QTimer()
	#time = QTime(0, 0, 0)
	timer.timeout.connect(main_window.checkWifi)
	timer.start(2000)

	sys.exit(app.exec_())

 
