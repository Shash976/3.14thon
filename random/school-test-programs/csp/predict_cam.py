import sys
from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os
from model_def import *
import numpy as np
from cv2 import imdecode
from image_analysis import *

class Detecholine(QWidget):
    def __init__(self):
        super().__init__() 
# Prediction tab
        self.prediction_layout = QVBoxLayout()
        
        # Loading the XLSX File
        self.prediction_file_input = QLineEdit()
        self.prediction_browse_file_btn = QPushButton("Browse")
        self.prediction_browse_file_btn.clicked.connect(lambda:(self.browse(self.prediction_file_input, file_types=[("Excel", "*.xlsx"), ("Pickle", "*.pkl")])))
        self.prediction_hbox1 = QHBoxLayout()
        self.prediction_hbox1.addWidget(self.prediction_file_input)
        self.prediction_hbox1.addWidget(self.prediction_browse_file_btn)
        self.prediction_layout.addLayout(self.prediction_hbox1)

        self.prediction_reagent_label = QLabel("Reagent: ")
        self.prediction_reagent_dropdown = QComboBox()
        self.prediction_reagent_dropdown.addItems(["Auto Detect", "Luminol"])
        self.prediction_hbox3 = QHBoxLayout()
        self.prediction_hbox3.addWidget(self.prediction_reagent_label)
        self.prediction_hbox3.addWidget(self.prediction_reagent_dropdown)
        self.prediction_hbox3.setAlignment(Qt.AlignLeft)
        self.prediction_layout.addLayout(self.prediction_hbox3)

        self.prediction_load_file_btn = QPushButton("Load model(s) from file")
        self.prediction_load_file_btn.clicked.connect(self.load_models)
        self.prediction_layout.addWidget(self.prediction_load_file_btn)
        
        #SELECTING WHETHER TO USE IMAGE OR MANUAL VALUE
        self.select_input_method_label = QLabel("Select input method")
        self.select_input_method = QComboBox()
        self.select_input_method.addItems(["Path to an image or GIF", "Manual"])
        self.set_input_method_btn = QPushButton("Set Input Method")
        self.set_input_method_btn.clicked.connect(self.set_prediction_input_method)
        self.prediction_hbox4 = QHBoxLayout()
        self.prediction_hbox4.addWidget(self.select_input_method_label)
        self.prediction_hbox4.addWidget(self.select_input_method)
        self.prediction_hbox4.addWidget(self.set_input_method_btn)
        self.prediction_layout.addLayout(self.prediction_hbox4)

        #ENTER MANUALLY
        self.prediction_enter_manually_label = QLabel("Enter X-Value")
        self.prediction_x_val_entry = QLineEdit()
        self.prediction_hbox5 = QHBoxLayout()
        self.prediction_hbox5.addWidget(self.prediction_enter_manually_label)
        self.prediction_hbox5.addWidget(self.prediction_x_val_entry)
        self.prediction_layout.addLayout(self.prediction_hbox5)

        #LOADING THE IMAGE
        self.prediction_image_input = QLineEdit()
        self.prediction_image_input.setVisible(False)
        self.prediction_image_browse_btn = QPushButton("Browse")
        self.prediction_image_browse_btn.clicked.connect(lambda:(self.browse(self.prediction_image_input, file_types=[("Images", "*.jpg"),("Images", "*.png"),("Images", "*.jpeg"),("GIF", "*.gif")])))
        self.prediction_image_browse_btn.setVisible(False)
        self.prediction_hbox2 = QHBoxLayout()
        self.prediction_hbox2.addWidget(self.prediction_image_input)
        self.prediction_hbox2.addWidget(self.prediction_image_browse_btn)
        self.prediction_layout.addLayout(self.prediction_hbox2)

        #PREDICT
        self.prediction_load_and_predict_btn = QPushButton("Predict")
        self.prediction_load_and_predict_btn.setVisible(False)
        self.prediction_load_and_predict_btn.clicked.connect(self.load_and_predict)
        self.prediction_layout.addWidget(self.prediction_load_and_predict_btn)
        
        # RESETTING and DOWNLOAD
        self.results_label = QLabel("")
        self.results_label.setVisible(False)
        self.download_results_tn = QPushButton("Download Results")
        self.download_results_tn.setVisible(False)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(lambda:self.reset_tab(self.prediction_layout))
        self.reset_button.setVisible(False)
        self.prediction_vbox3 = QVBoxLayout()
        self.prediction_vbox3.addWidget(self.results_label)
        self.prediction_vbox3.addWidget(self.download_results_tn)
        self.prediction_vbox3.addWidget(self.reset_button)
        self.prediction_layout.addLayout(self.prediction_vbox3)

        self.setLayout(self.prediction_layout)


    def browse(self, input_element, is_file=True, file_types=[("Excel Files", "*.xlsx")]):
        if is_file == True:
            path, _ = QFileDialog.getOpenFileName(self, filter=";;".join([f"{desc} ({ext})" for desc, ext in file_types]))
        else:
            path = QFileDialog.getExistingDirectory(self, "Select Folder")
        input_element.setText(path)

    def load_models(self):
        if os.path.exists(self.load_models_input.text().strip()) and self.load_models_input.text().strip().endswith(".xlsx"):
            self.load_models_input.setDisabled(True)
            self.load_elements(self.prediction_hbox4)
        else:
            pass
            #.setText("Please enter a valid filepath")

    def load_elements(self, layout, exempt_list=[]):
        exempt_list = [] if len(exempt_list) == 0 else exempt_list
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget= item.widget()
            if widget != None:
                if widget not in exempt_list:
                    widget.setVisible(True)
                    widget.setDisabled(False)
            elif widget == None:
                if item not in exempt_list:
                    self.load_elements(item, exempt_list)

    def set_prediction_input_method(self):
        self.select_input_method.setDisabled(True)
        if "image" in self.select_input_method.currentText().strip().lower():
            self.load_elements(self.prediction_hbox2)
        else:
            self.load_elements(self.prediction_hbox5)
        self.prediction_load_and_predict_btn.setVisible(True)

    def load_and_predict(self):
        x_val = None
        if "image" in self.select_input_method.currentText().lower():
            if os.path.exists(self.prediction_image_input.text()) and self.prediction_image_input.text().lower().endswith((".gif",".jpg", ".jpeg", ".png")):
                self.prediction_image_input.setDisabled(True)
                image_path = self.prediction_image_input.text()
                reagent = self.prediction_reagent_dropdown.currentText()
                self.prediction_reagent_dropdown.setDisabled(True)
                if image_path.endswith(".gif"):
                    from image_analysis import getFrame
                    image = getFrame(image_path)
                else:
                    image = imdecode(np.fromfile(image_path, dtype=np.uint8), -1)
                if "auto" in reagent.lower():
                    for r in Reagent.reagents:
                        x_val, area, _ = getPlainMean(image, r.name)
                        if x_val>0 and area > 1000:
                            reagent = r.name
                            break
                else:
                    x_val,_,_ = getPlainMean(image, reagent)
            else:
                #.setText("Please enter a valid Image Path.")
                return
        else:
            from image_analysis import is_float
            if is_float(self.prediction_x_val_entry.text()):
                x_val = float(self.prediction_x_val_entry.text())
            else:
                #.setText("Please enter a valid number")
                return
        if x_val != None:
            from prediction import predict_value, load, download_predictions
            loaded_models = load(self.prediction_file_input.text().strip())
            predictions, label_text = predict_value(x_val, loaded_models)
            self.results_label.setText(f"At Intensity of {x_val}, the predicted Concentrations are \n{label_text}" )
            self.download_results_tn.clicked.connect(lambda:(download_predictions(x_val, predictions, parentPath=self.prediction_file_input.text().strip()))) #.setText("Downloaded")))
            self.load_elements(self.prediction_vbox3) #.setText("Done")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Detecholine()
    window.show()
    print("WTAT UUOIBO")
    sys.exit(app.exec_())
