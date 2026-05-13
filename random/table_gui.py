import sys
import csv
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.inputLine = QLineEdit()
        self.addButton = QPushButton('Add')
        self.resetButton = QPushButton('Reset')
        self.exportCSVButton = QPushButton('Export to CSV')
        self.exportXLSXButton = QPushButton('Export to XLSX')
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Value', 'Square', 'Cube'])

        self.addButton.clicked.connect(self.on_add_clicked)
        self.resetButton.clicked.connect(self.reset_table)
        self.exportCSVButton.clicked.connect(self.export_to_csv)
        self.exportXLSXButton.clicked.connect(self.export_to_xlsx)

        layout.addWidget(self.inputLine)
        layout.addWidget(self.addButton)
        layout.addWidget(self.resetButton)
        layout.addWidget(self.exportCSVButton)
        layout.addWidget(self.exportXLSXButton)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.setWindowTitle('Square and Cube Table')
        self.show()

    def on_add_clicked(self):
        value = self.inputLine.text()
        if value.isdigit():
            value_int = int(value)
            square = value_int ** 2
            cube = value_int ** 3

            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(value))
            self.table.setItem(row_position, 1, QTableWidgetItem(str(square)))
            self.table.setItem(row_position, 2, QTableWidgetItem(str(cube)))

    def reset_table(self):
        self.table.setRowCount(0)

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV(*.csv)")
        if path:
            with open(path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Value', 'Square', 'Cube'])
                for row in range(self.table.rowCount()):
                    row_data = []
                    for column in range(self.table.columnCount()):
                        item = self.table.item(row, column)
                        row_data.append(item.text() if item else '')
                    writer.writerow(row_data)

    def export_to_xlsx(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files(*.xlsx)")
        if path:
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for column in range(self.table.columnCount()):
                    item = self.table.item(row, column)
                    row_data.append(item.text() if item else '')
                data.append(row_data)

            df = pd.DataFrame(data, columns=['Value', 'Square', 'Cube'])
            df.to_excel(path, index=False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
