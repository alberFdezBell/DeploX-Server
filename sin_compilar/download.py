import sys
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QMessageBox, QListWidget, QListWidgetItem, QLineEdit,
    QMenu, QDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QClipboard

from utils import load_config, run_program, copy_exe_to_downloads

# Rutas base para no depender de dónde se ejecute el script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "DeploXServer.ico")


# ==============================================================================
# VISTA: Ventana emergente para copiar la ruta del ejecutable
# ==============================================================================
class PathDialog(QDialog):
    def __init__(self, program_name, program_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Ruta de {program_name}")
        self.setMinimumWidth(450)
        self.program_path = program_path

        # Hoja de estilos para mantener la estética oscura (Dark Mode)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: #ffffff; }
            QLabel { color: #b3b3b3; font-size: 12px; }
            QLineEdit {
                background-color: #2d2d2d; border: 1px solid #333333; border-radius: 4px;
                color: #ffffff; padding: 6px; font-family: 'Consolas', monospace;
            }
            QPushButton {
                background-color: #2196f3; color: white; font-weight: bold; border: none; border-radius: 4px; padding: 8px;
            }
            QPushButton:hover { background-color: #1e88e5; }
            QPushButton#btn_close { background-color: #3d3d3d; color: #ffffff; }
            QPushButton#btn_close:hover { background-color: #4d4d4d; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        layout.addWidget(QLabel("Ubicación del archivo ejecutable en el servidor:"))
        self.path_input = QLineEdit(self.program_path)
        self.path_input.setReadOnly(True)  # Evitamos que el usuario la modifique sin querer
        layout.addWidget(self.path_input)

        actions_layout = QHBoxLayout()
        btn_copy = QPushButton("📋 Copiar Ruta")
        btn_copy.clicked.connect(self.copy_to_clipboard)
        actions_layout.addWidget(btn_copy)

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btn_close")
        btn_close.clicked.connect(self.accept)
        actions_layout.addWidget(btn_close)

        layout.addLayout(actions_layout)

    # Interactuamos con el portapapeles del sistema operativo
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.program_path)
        QMessageBox.information(self, "Copiado", "La ruta se ha copiado al portapapeles.")


# ==============================================================================
# COMPONENTE: Fila personalizada para la lista de programas
# ==============================================================================
class ClientProgramRowWidget(QWidget):
    # Canal para avisar a la ventana principal de que el usuario ha hecho algo aquí
    action_triggered = Signal(str, dict)

    def __init__(self, program: dict, parent=None):
        super().__init__(parent)
        self.program = program
        self.setMouseTracking(True)  # Necesario para capturar cuando el ratón entra/sale de la fila

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        name = program.get("name", "Unknown")
        self.lbl_info = QLabel(f"<b style='font-size: 14px; color: #ffffff;'>{name}</b>")
        layout.addWidget(self.lbl_info, 1)

        # Botón de ejecución rápida (Se oculta/muestra con el hover del ratón)
        self.btn_run = QPushButton("▶")
        self.btn_run.setFixedSize(30, 30)
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setToolTip("Ejecutar programa")
        self.btn_run.setStyleSheet("""
            QPushButton {
                font-size: 14px; color: #4caf50; background-color: transparent; border: none; border-radius: 4px;
            }
            QPushButton:hover { background-color: #2e7d32; color: #ffffff; }
        """)
        self.btn_run.clicked.connect(self.emit_run_action)
        self.btn_run.hide()  
        layout.addWidget(self.btn_run)

        # Botón para desplegar el menú de opciones extra
        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setFixedSize(30, 30)
        self.btn_menu.setCursor(Qt.PointingHandCursor)
        self.btn_menu.setStyleSheet("""
            QPushButton {
                font-size: 16px; font-weight: bold; color: #b3b3b3; background-color: transparent; border: none; border-radius: 4px;
            }
            QPushButton:hover { background-color: #333333; color: #ffffff; }
        """)
        self.btn_menu.clicked.connect(self.show_options_menu)
        layout.addWidget(self.btn_menu)

    def emit_run_action(self):
        self.action_triggered.emit("run", self.program)

    # Efecto visual: Mostramos el botón "Play" solo si el ratón está encima de la fila
    def enterEvent(self, event):
        self.btn_run.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn_run.hide()
        super().leaveEvent(event)

    # Menú contextual que aparece justo debajo del botón de los tres puntos
    def show_options_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #252526; color: #ffffff; border: 1px solid #333333; padding: 4px; }
            QMenu::item { padding: 6px 20px 6px 10px; border-radius: 4px; }
            QMenu::item:selected { background-color: #37373d; }
        """)

        action_download = menu.addAction("Descargar")
        action_path = menu.addAction("Mostrar Ruta")

        selected_action = menu.exec(self.btn_menu.mapToGlobal(self.btn_menu.rect().bottomLeft()))

        if selected_action == action_download:
            self.action_triggered.emit("download", self.program)
        elif selected_action == action_path:
            self.action_triggered.emit("show_path", self.program)


# ==============================================================================
# APLICACIÓN PRINCIPAL: Panel de control del Cliente
# ==============================================================================
class DownloadApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeploX Server - Cliente")
        self.setMinimumSize(750, 550)

        # Cargamos los datos del JSON (vía utils)
        self.data = load_config()

        # Configuración para la animación del spinner (simulación de carga de catálogo)
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.animate_spinner)
        
        # Temporizador para controlar cuánto dura el efecto visual de "Cargando"
        self.process_timer = QTimer(self)
        self.process_timer.setSingleShot(True)
        self.process_timer.timeout.connect(self.finish_refresh_catalog)

        # Inicializamos la interfaz y pintamos los datos
        self.init_ui()
        self.update_group_combobox()
        self.load_programs()

    def init_ui(self):
        # Paleta de colores oscuros inspirada en entornos como VS Code
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #1e1e1e; 
            }
            QLabel { 
                color: #ffffff; 
            }
            QLineEdit#search_input {
                background-color: #252526; 
                border: 1px solid #333333; 
                border-radius: 4px;
                color: #ffffff; 
                padding: 0px 10px; 
                font-size: 13px;
                min-height: 30px;
                max-height: 30px;
            }
            QLineEdit#search_input:focus { 
                border: 1px solid #007acc; 
            }
            
            QLineEdit::clear-button {
                background-color: transparent;
                border-radius: 2px;
                padding: 2px;
                margin-right: 4px; 
            }
            QLineEdit::clear-button:hover {
                background-color: #333333;
            }
            QLineEdit::clear-button:pressed {
                background-color: #444444;
            }
            
            QComboBox#group_filter {
                background-color: #252526; 
                border: 1px solid #333333; 
                border-radius: 4px;
                color: #ffffff; 
                padding-left: 8px;
                font-size: 13px;
                min-height: 30px;
                max-height: 30px;
                min-width: 160px;
            }
            QComboBox#group_filter::drop-down {
                border: none;
                background: transparent;
            }
            QComboBox#group_filter::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #b3b3b3;
                margin-right: 8px;
            }
            QPushButton#btn_refresh {
                background-color: #333333; 
                color: #ffffff; 
                border: 1px solid #555555; 
                border-radius: 4px;
                padding: 0px 12px; 
                font-weight: 500; 
                font-size: 13px; 
                min-height: 30px;
                max-height: 30px;
                min-width: 85px;
            }
            QPushButton#btn_refresh:hover { 
                background-color: #444444; 
                border-color: #007acc; 
            }
            QPushButton#btn_refresh:disabled { 
                background-color: #252526; 
                color: #007acc; 
                border-color: #333333; 
            }
        """)

        container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # --- Zona Superior: Filtros y Búsqueda ---
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search_input")
        self.search_bar.setPlaceholderText("Buscar programa por nombre...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self.filter_programs)
        search_layout.addWidget(self.search_bar, 2)

        self.group_filter = QComboBox()
        self.group_filter.setObjectName("group_filter")
        self.group_filter.currentIndexChanged.connect(self.filter_programs)
        search_layout.addWidget(self.group_filter, 1)

        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.setObjectName("btn_refresh")
        self.btn_refresh.clicked.connect(self.start_refresh_catalog)
        search_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(search_layout)

        # --- Zona Central: Lista de elementos ---
        self.program_list_widget = QListWidget()
        self.program_list_widget.setSelectionMode(QListWidget.NoSelection)
        self.program_list_widget.setStyleSheet("""
            QListWidget { background-color: #121212; border: 1px solid #2d2d2d; border-radius: 6px; outline: 0; }
            QListWidget::item { border-bottom: 1px solid #1e1e1e; background-color: transparent; }
            QListWidget::item:hover { background-color: #1a1a1a; }
        """)
        
        self.program_list_widget.itemDoubleClicked.connect(self.on_item_double_click)
        main_layout.addWidget(self.program_list_widget)

        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.setFocus()

    # Rellenamos el ComboBox con las categorías del JSON de configuración
    def update_group_combobox(self):
        self.group_filter.blockSignals(True)  # Apagamos señales para evitar llamadas en bucle al borrar
        self.group_filter.clear()
        
        self.group_filter.addItem("Todos los programas", None)
        
        for group in self.data.get("groups", []):
            g_name = group.get("name")
            g_progs = group.get("programs", [])
            self.group_filter.addItem(g_name, g_progs)  # Guardamos la lista de nombres como UserData
            
        self.group_filter.blockSignals(False)

    # Inyecta los programas del JSON dentro del QListWidget usando las filas personalizadas
    def load_programs(self):
        self.program_list_widget.clear()
        programs = self.data.get("programs", [])

        # Si el JSON está vacío, mostramos un aviso amigable en pantalla
        if not programs:
            item = QListWidgetItem()
            empty_label = QLabel("No hay programas registrados en el sistema")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #555555; font-size: 14px; font-weight: bold; padding: 30px;")
            item.setSizeHint(empty_label.sizeHint())
            self.program_list_widget.addItem(item)
            self.program_list_widget.setItemWidget(item, empty_label)
            return

        # Generamos una celda interactiva por cada programa
        for program in programs:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, program) # Nos guardamos el diccionario entero para usarlo después
            
            row_widget = ClientProgramRowWidget(program, self)
            row_widget.action_triggered.connect(self.handle_menu_actions)
            
            item.setSizeHint(row_widget.sizeHint())
            self.program_list_widget.addItem(item)
            self.program_list_widget.setItemWidget(item, row_widget)

    # Dispara los temporizadores para simular el feedback visual de carga
    def start_refresh_catalog(self):
        self.btn_refresh.setEnabled(False)
        self.spinner_index = 0
        self.loading_timer.start(800 // len(self.spinner_frames)) 
        self.process_timer.start(800)

    # Va cambiando el carácter de texto para dar el efecto de spinner cargando
    def animate_spinner(self):
        frame = self.spinner_frames[self.spinner_index]
        self.btn_refresh.setText(f"{frame} Cargando")
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)

    # Finaliza la carga, relee el JSON y restaura la selección del filtro del usuario
    def finish_refresh_catalog(self):
        self.loading_timer.stop()
        
        # Truco: Guardamos qué grupo estaba mirando el usuario para no descolocarle la interfaz
        current_group_text = self.group_filter.currentText()
        
        self.data = load_config()
        self.update_group_combobox()
        
        # Intentamos restaurar el grupo previo si sigue existiendo en el nuevo JSON
        index = self.group_filter.findText(current_group_text)
        if index != -1:
            self.group_filter.blockSignals(True)
            self.group_filter.setCurrentIndex(index)
            self.group_filter.blockSignals(False)
            
        self.load_programs()
        self.filter_programs()  # Mantiene vivos los filtros de texto y categoría activos
        
        self.btn_refresh.setText("Actualizar")
        self.btn_refresh.setEnabled(True)

    def execute_program_logic(self, program):
        if program:
            exe_path = program.get("path")
            if exe_path and os.path.exists(exe_path):
                if not run_program(exe_path):
                    QMessageBox.critical(self, "Error", f"No se pudo ejecutar: {exe_path}")
            else:
                QMessageBox.warning(self, "Error", "Archivo ejecutable no encontrado en la ruta establecida.")

    # Doble clic en cualquier parte de la fila = Lanzar el ejecutable directamente
    def on_item_double_click(self, item):
        program = item.data(Qt.UserRole)
        self.execute_program_logic(program)

    # Centralizador de las acciones que emiten los componentes de las filas
    def handle_menu_actions(self, action_type, program):
        if action_type == "run":
            self.execute_program_logic(program)
        elif action_type == "download":
            self.download_exe(program)
        elif action_type == "show_path":
            dialog = PathDialog(program.get("name", "Programa"), program.get("path", "N/A"), self)
            dialog.exec()

    # Filtro en tiempo real: Oculta o muestra filas según el buscador y la categoría
    def filter_programs(self, *args):
        search_text = self.search_bar.text().lower().strip()
        selected_group_programs = self.group_filter.currentData() 
        
        for i in range(self.program_list_widget.count()):
            item = self.program_list_widget.item(i)
            program_data = item.data(Qt.UserRole)
            
            if program_data:
                name = program_data.get("name", "")
                matches_search = search_text in name.lower()
                
                matches_group = True
                if selected_group_programs is not None:
                    # El grupo guarda los nombres válidos; comprobamos si este programa pertenece a él
                    matches_group = name in selected_group_programs
                
                # Qt se encarga de reajustar el scroll automáticamente al ocultar items
                item.setHidden(not (matches_search and matches_group))

    # Permite al usuario clonar el archivo remoto en su carpeta local seleccionada
    def download_exe(self, program):
        exe_path = program.get("path")
        if not exe_path or not os.path.exists(exe_path):
            QMessageBox.warning(self, "Error", "El archivo ejecutable no existe o no está accesible.")
            return

        downloads_folder = str(Path.home() / "Downloads")
        filename = os.path.basename(exe_path)

        # Abrimos el explorador nativo del sistema para elegir la ruta de guardado
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar ejecutable", os.path.join(downloads_folder, filename), "Executable Files (*.exe);;All Files (*)"
        )
        if not file_path:
            return  # El usuario canceló el diálogo de guardado

        try:
            dest = copy_exe_to_downloads(exe_path, os.path.basename(file_path))
            if dest:
                QMessageBox.information(self, "OK", f"Descargado exitosamente:\n{dest}")
            else:
                raise Exception("Error al clonar el archivo binario.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo descargar: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloadApp()
    window.show()
    sys.exit(app.exec())