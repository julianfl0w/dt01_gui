import sys
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import * 
from PyQt5.QtCore import * 
from text_to_image import *

class MainWindow(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		scroll_area = QScrollArea()
		scroll_area.setMinimumWidth(3000)
		layout = QGridLayout(self)
		layout.addWidget(scroll_area)

		scroll_widget = QWidget()
		scroll_layout = QFormLayout(scroll_widget)

		for i in range(50):
		
			buttonLabel = 'Label #{}'.format(i)
			labelImage = text_to_image(buttonLabel)
			_icon = QIcon(labelImage)
			my_button = QPushButton()
			my_button.setIcon(_icon)
			my_button.setIconSize(QSize(720, 70))
			scroll_layout.addRow(my_button)

		scroll_area.setWidget(scroll_widget)

		QScroller.grabGesture(
			scroll_area.viewport(), QScroller.LeftMouseButtonGesture
		)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	main_window = MainWindow()
	main_window.showFullScreen()
	sys.exit(app.exec_())
