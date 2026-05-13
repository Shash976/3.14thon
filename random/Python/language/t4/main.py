import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMainWindow, QSizePolicy
import gettext

lang="en"
lang_translations = gettext.translation('base', localedir='locales', languages=[lang])
lang_translations.install()
_ = lang_translations.gettext
class MyGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(_("PyQt5 GUI with Labels and Buttons"))
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create labels and buttons with long texts
        for i in range(25):
            label_text = _("Label {number} with a long text that doesn't fit in one line").format(number=i+1)
            button_text = _("Button {number} with a long text").format(number=i+1)

            label = QLabel(label_text)
            button = QPushButton(button_text)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.clicked.connect(lambda state, i=i: self.button_clicked(i + 1))

            layout.addWidget(label)
            layout.addWidget(button)

        central_widget.setLayout(layout)

    def button_clicked(self, button_number):
        print(_("Button {button_number} clicked!").format(button_number=button_number))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_gui = MyGUI()
    my_gui.show()
    sys.exit(app.exec_())
