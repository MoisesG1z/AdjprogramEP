import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QTabWidget, QLabel,
                             QPushButton, QTextEdit, QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt
from usb_manager import EpsonUSBManager

class AdjProgramApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Declaración de atributos de instancia en __init__ para buenas prácticas
        self.printer_list = None
        self.btn_detect = None
        self.tabs = None
        self.tab_status = None
        self.tab_maintenance = None
        self.tab_pads = None
        self.tab_errors = None
        self.lbl_status = None
        self.btn_nozzle = None
        self.pad_progress = None
        self.btn_read_pads = None
        self.error_display = None
        self.btn_diagnose = None

        self.setWindowTitle("Epson L-Series Management Utility")
        self.resize(800, 600)

        # Gestor USB
        self.usb_manager = EpsonUSBManager()

        # Configuración del widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout principal dividido en dos
        self.main_layout = QHBoxLayout(self.central_widget)

        self.setup_left_panel()
        self.setup_right_panel()

    def setup_left_panel(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Impresoras Detectadas:"))
        self.printer_list = QListWidget()
        self.printer_list.setMaximumWidth(220)
        self.printer_list.addItem("Haga clic en 'Detectar'...")
        layout.addWidget(self.printer_list)

        self.btn_detect = QPushButton("Detectar Impresoras USB")
        self.btn_detect.clicked.connect(self.detect_printers)
        layout.addWidget(self.btn_detect)

        self.main_layout.addLayout(layout)

    def detect_printers(self):
        self.printer_list.clear()
        self.printer_list.addItem("Buscando...")
        QApplication.processEvents()

        success, message = self.usb_manager.find_and_connect()
        
        self.printer_list.clear()
        if success:
            product_id = hex(self.usb_manager.device.idProduct)
            self.printer_list.addItem(f"Epson Conectada (ID: {product_id})")
            self.lbl_status.setText(f"Estado: <b>Conectada (ID: {product_id})</b>")
            QMessageBox.information(self, "Detección Exitosa", message)
        else:
            self.printer_list.addItem("Ninguna impresora detectada.")
            self.lbl_status.setText("Estado: <b>Desconectada</b>")
            QMessageBox.warning(self, "Detección Fallida", message)

    def setup_right_panel(self):
        self.tabs = QTabWidget()

        self.tab_status = QWidget()
        self.tab_maintenance = QWidget()
        self.tab_pads = QWidget()
        self.tab_errors = QWidget()

        self.tabs.addTab(self.tab_status, "Estado General")
        self.tabs.addTab(self.tab_maintenance, "Mantenimiento")
        self.tabs.addTab(self.tab_pads, "Almohadillas")
        self.tabs.addTab(self.tab_errors, "Analizador de Errores")

        self.setup_status_tab()
        self.setup_maintenance_tab()
        self.setup_pads_tab()
        self.setup_errors_tab()

        self.main_layout.addWidget(self.tabs)

    def setup_status_tab(self):
        layout = QVBoxLayout(self.tab_status)
        layout.addWidget(QLabel("<h2>Estado de la Impresora</h2>"))
        self.lbl_status = QLabel("Estado: <b>Desconectada</b>")
        layout.addWidget(self.lbl_status)
        layout.addStretch()

    def setup_maintenance_tab(self):
        layout = QVBoxLayout(self.tab_maintenance)
        layout.addWidget(QLabel("<h2>Herramientas de Mantenimiento</h2>"))

        self.btn_nozzle = QPushButton("Test de Inyectores")
        self.btn_nozzle.setMinimumHeight(40)
        self.btn_nozzle.clicked.connect(self.action_nozzle_check)
        
        layout.addWidget(self.btn_nozzle)
        layout.addStretch()

    def action_nozzle_check(self):
        if not self.usb_manager.device:
            QMessageBox.warning(self, "Error", "Debe detectar y conectar una impresora primero.")
            return
            
        success, msg = self.usb_manager.do_nozzle_check()
        if success:
            QMessageBox.information(self, "Test de Inyectores", "Comando enviado. Revise la impresora.")
        else:
            QMessageBox.critical(self, "Error", f"Fallo al enviar comando: {msg}")

    def setup_pads_tab(self):
        layout = QVBoxLayout(self.tab_pads)
        layout.addWidget(QLabel("<h2>Contador de Almohadillas (Waste Ink Pad)</h2>"))

        self.pad_progress = QProgressBar()
        self.pad_progress.setValue(0)
        self.pad_progress.setFormat("%p%")
        layout.addWidget(self.pad_progress)

        self.btn_read_pads = QPushButton("Leer Contador de Almohadillas")
        self.btn_read_pads.setMinimumHeight(40)
        self.btn_read_pads.clicked.connect(self.action_read_pads)
        layout.addWidget(self.btn_read_pads)
        layout.addStretch()
        
    def action_read_pads(self):
        if not self.usb_manager.device:
            QMessageBox.warning(self, "Error", "Debe detectar y conectar una impresora primero.")
            return
            
        success, val = self.usb_manager.read_waste_ink_pads()
        if success:
            self.pad_progress.setValue(val)
            QMessageBox.information(self, "Lectura Exitosa", f"El contador de almohadillas está al {val}%.")
        else:
            QMessageBox.critical(self, "Error", "No se pudo leer el contador de almohadillas.")

    def setup_errors_tab(self):
        layout = QVBoxLayout(self.tab_errors)
        layout.addWidget(QLabel("<h2>Analizador de Códigos de Error</h2>"))

        self.error_display = QTextEdit()
        self.error_display.setReadOnly(True)
        self.error_display.setHtml("<i>Haga clic en 'Analizar Impresora' para escanear posibles fallos.</i>")
        layout.addWidget(self.error_display)

        self.btn_diagnose = QPushButton("Analizar Impresora")
        self.btn_diagnose.setMinimumHeight(40)
        self.btn_diagnose.clicked.connect(self.action_analyze)
        layout.addWidget(self.btn_diagnose)

    def action_analyze(self):
        if not self.usb_manager.device:
            QMessageBox.warning(self, "Error", "Debe detectar y conectar una impresora primero.")
            return
            
        self.error_display.setHtml("<i>Enviando solicitud de diagnóstico...</i>")
        QApplication.processEvents()
        
        success, data = self.usb_manager.analyze_printer()
        
        if success:
            # Mostramos directamente el texto (data) ya que lo cambiamos a string en usb_manager.py
            self.error_display.setHtml(f"<b>Diagnóstico:</b><br>{data}<br><br>"
                                     "<i>La impresora respondió correctamente al pulso de conexión inicial.</i>")
        else:
            self.error_display.setHtml(f"<b style='color:red;'>Error al diagnosticar:</b> {data}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AdjProgramApp()
    window.show()
    sys.exit(app.exec_())