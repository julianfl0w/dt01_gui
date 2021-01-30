import sys

from PyQt5.QtWidgets import (
    QApplication,
    QFormLayout,
    QGridLayout,
    QLabel,
    QScrollArea,
    QScroller,
    QWidget,
    QPushButton
)

from PyQt5.QtCore import(
    QSize
)

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        scroll_area = QScrollArea()
        layout = QGridLayout(self)
        layout.addWidget(scroll_area)

        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)

        for i in range(200):
            newButton = QPushButton('Label #{}'.format(i), self)
            buttonSize = QSize( 100, 20);
            newButton.iconSize(buttonSize)
            scroll_layout.addRow(newButton)

        scroll_area.setWidget(scroll_widget)

        QScroller.grabGesture(
            scroll_area.viewport(), QScroller.LeftMouseButtonGesture
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.showFullScreen()
    sys.exit(app.exec_())
