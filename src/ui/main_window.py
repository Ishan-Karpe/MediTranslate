"""
src/ui/main_window.py
Main application window container.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
    QStatusBar, QMessageBox
)
from PySide6.QtGui import QAction
from ui.scanner_tab import ScannerTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediTranslate - Medical Document Translator")
        self.setMinimumSize(1000, 700)
        
        # Setup Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Setup Tabs
        self.tabs = QTabWidget()
        self.scanner_tab = ScannerTab()
        self.tabs.addTab(self.scanner_tab, "Scan Document")
        main_layout.addWidget(self.tabs)
        
        # Setup Menu
        self._setup_menu()
        
        # Setup Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        
        new_action = QAction("New Scan", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_scan)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _new_scan(self):
        self.scanner_tab.reset_state()
        self.status_bar.showMessage("New scan started")

    def _show_about(self):
        QMessageBox.about(self, "About MediTranslate", "<h2>MediTranslate v1.0</h2><p>Built by Ishan Karpe</p>")