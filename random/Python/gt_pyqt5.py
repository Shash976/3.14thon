import sys
import gettext
import googletrans
from PyQt5 import QtCore, QtGui, QtWidgets

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.translator = googletrans.Translator()
        self.current_language = gettext.translation().gettext("current_language")

        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("My Application")

        self.label = QtWidgets.QLabel("Hello, world!", self)
        self.label.setGeometry(QtCore.QRect(100, 100, 200, 20))

        self.languageComboBox = QtWidgets.QComboBox(self)
        self.languageComboBox.setGeometry(QtCore.QRect(100, 150, 200, 20))
        self.languageComboBox.addItem("English")
        self.languageComboBox.addItem("French")
        self.languageComboBox.addItem("Spanish")
        self.languageComboBox.currentIndexChanged.connect(self.on_language_changed)

        self.translateButton = QtWidgets.QPushButton("Translate", self)
        self.translateButton.setGeometry(QtCore.QRect(100, 200, 200, 20))
        self.translateButton.clicked.connect(self.on_translate_clicked)

        self.show()

    def on_language_changed(self, index):
        self.current_language = self.languageComboBox.itemData(index, QtCore.Qt.UserRole)[0]

    def on_translate_clicked(self):
        text = self.label.text()
        translated_text = translate_text(text, source_language='en', target_language=self.current_language)
        self.label.setText(translated_text)

def translate_text(text, source_language=None, target_language='en'):
    """
    Translates text from one language to another using Google Translate.
    """
    if source_language is None:
        source_language = translator.detect(text).lang

    translation = translator.translate(text, src=source_language, dest=target_language)
    return translation.text

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    translator = gettext.translation('myapp', 'locales')
    translator.install()
    window = MainWindow()
    sys.exit(app.exec_())
