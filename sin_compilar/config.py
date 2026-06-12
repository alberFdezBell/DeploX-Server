import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QFileDialog, QMessageBox, QListWidget,
    QListWidgetItem, QGroupBox, QGraphicsOpacityEffect,
    QCheckBox, QComboBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QCloseEvent

from utils import (
    load_config, save_config, add_program, remove_program
)

# Configuración de rutas para recursos del sistema
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "DeploXServer.ico")


# --- DIÁLOGOS DE LA INTERFAZ ---

class ProgramDialog(QDialog):
    """Ventana emergente para añadir o editar un programa individual."""
    def __init__(self, current_name="", current_path="", is_edit=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Configuración" if is_edit else "Añadir Nuevo Programa")
        self.setMinimumWidth(500)
        self.old_name = current_name  # Guardamos el nombre original por si se edita

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Campo: Nombre del programa
        layout.addWidget(QLabel("Nombre del programa:"))
        self.name_input = QLineEdit(current_name)
        self.name_input.setPlaceholderText("Ej: Google Chrome")
        layout.addWidget(self.name_input)

        # Campo: Ruta del ejecutable con botón de búsqueda
        layout.addWidget(QLabel("Ruta del ejecutable:"))
        exe_layout = QHBoxLayout()
        
        self.exe_input = QLineEdit(current_path)
        self.exe_input.setPlaceholderText(r"Ej: R:\Servidor\programas\Chrome\chrome.exe")
        exe_layout.addWidget(self.exe_input)
        
        btn_select_exe = QPushButton("Explorar")
        btn_select_exe.clicked.connect(self.select_exe_file)
        exe_layout.addWidget(btn_select_exe)
        layout.addLayout(exe_layout)

        # Botones de acción (Guardar / Cancelar)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        btn_save = QPushButton("Guardar Cambios" if is_edit else "Añadir Programa")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold; 
                padding: 8px 16px; border: none; border-radius: 4px;
            }
            QPushButton:hover { background-color: #43a047; }
        """)
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d; color: #ffffff; font-weight: bold;
                padding: 8px 16px; border: none; border-radius: 4px;
            }
            QPushButton:hover { background-color: #4a4a4a; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        actions_layout.addWidget(btn_save)
        actions_layout.addWidget(btn_cancel)
        layout.addLayout(actions_layout)

    def select_exe_file(self):
        """Abre el explorador de archivos nativo para buscar el .exe."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar ejecutable", "", "Executables (*.exe);;All Files (*)")
        if file_path:
            self.exe_input.setText(file_path)

    def get_data(self):
        """Retorna los datos limpios introducidos en el formulario."""
        return {
            "name": self.name_input.text().strip(),
            "path": self.exe_input.text().strip()
        }


class GroupDialog(QDialog):
    """Ventana emergente para agrupar programas con opciones de filtrado."""
    def __init__(self, all_programs, current_name="", selected_programs=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Grupo de Programas")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        
        self.all_programs = all_programs
        self.selected_programs = selected_programs if selected_programs else []

        layout = QVBoxLayout(self)
        
        # Campo: Nombre del grupo
        layout.addWidget(QLabel("Nombre del Grupo:"))
        self.name_input = QLineEdit(current_name)
        self.name_input.setPlaceholderText("Ej: Desarrollo, Diseño, Oficina...")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Filtrar y Seleccionar Programas:"))
        
        # Barra de búsqueda y filtro por estado
        filter_layout = QHBoxLayout()
        
        self.search_program = QLineEdit()
        self.search_program.setPlaceholderText("Buscar por nombre...")
        self.search_program.textChanged.connect(self.filter_programs)
        filter_layout.addWidget(self.search_program, 2)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Añadidos", "No añadidos"])
        self.status_filter.currentIndexChanged.connect(self.filter_programs)
        filter_layout.addWidget(self.status_filter, 1)
        
        layout.addLayout(filter_layout)

        # Lista de programas disponibles (con Checkboxes)
        self.programs_list = QListWidget()
        layout.addWidget(self.programs_list)
        
        self.checkbox_map = {}  # Mapeo interno para acceder rápido a los elementos de la lista
        self.populate_programs()

        # Botones de acción
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        btn_save = QPushButton("Guardar Grupo")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #007acc; color: white; font-weight: bold; 
                padding: 8px 16px; border: none; border-radius: 4px;
            }
            QPushButton:hover { background-color: #0062a3; }
        """)
        btn_save.clicked.connect(self.accept)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d; color: #ffffff; font-weight: bold;
                padding: 8px 16px; border: none; border-radius: 4px;
            }
            QPushButton:hover { background-color: #4a4a4a; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        actions_layout.addWidget(btn_save)
        actions_layout.addWidget(btn_cancel)
        layout.addLayout(actions_layout)

    def populate_programs(self):
        """Llena la lista insertando un QCheckBox dentro de cada fila."""
        for p in self.all_programs:
            p_name = p.get("name", "")
            item = QListWidgetItem(self.programs_list)
            checkbox = QCheckBox(p_name)
            
            if p_name in self.selected_programs:
                checkbox.setChecked(True)
                
            checkbox.stateChanged.connect(self.filter_programs)
                
            item.setSizeHint(checkbox.sizeHint())
            self.programs_list.addItem(item)
            self.programs_list.setItemWidget(item, checkbox)
            self.checkbox_map[p_name] = (item, checkbox)

    def filter_programs(self, *args):
        """Filtra dinámicamente la lista según el texto de búsqueda y el checkbox de estado."""
        search_text = self.search_program.text().lower().strip()
        filter_mode = self.status_filter.currentText()

        for p_name, (item, checkbox) in self.checkbox_map.items():
            matches_search = search_text in p_name.lower()
            is_checked = checkbox.isChecked()
            
            if filter_mode == "Añadidos":
                matches_status = is_checked
            elif filter_mode == "No añadidos":
                matches_status = not is_checked
            else:
                matches_status = True
                
            # Oculta el elemento de la lista si no cumple los filtros aplicados
            item.setHidden(not (matches_search and matches_status))

    def get_data(self):
        """Retorna el nombre del grupo y la lista de programas marcados."""
        checked_programs = [name for name, (_, cb) in self.checkbox_map.items() if cb.isChecked()]
        return {
            "name": self.name_input.text().strip(),
            "programs": checked_programs
        }


# --- COMPONENTES PERSONALIZADOS ---

class GenericRowWidget(QWidget):
    """Fila personalizada para las listas. Muestra texto y revela botones al pasar el ratón."""
    edit_clicked = Signal(dict)
    delete_clicked = Signal(str)

    def __init__(self, name, description, data_payload, parent=None):
        super().__init__(parent)
        self.item_name = name
        self.payload = data_payload

        self.setAttribute(Qt.WA_Hover, True)  # Necesario para capturar enterEvent/leaveEvent

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # Contenedor para el bloque de texto (Título y Subtítulo)
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.lbl_title = QLabel(f"<div style='color: #ffffff; font-weight: bold;'>{name}</div>")
        text_layout.addWidget(self.lbl_title)

        # Truco visual: Si no hay descripción (ej. en Grupos), forzamos un spacer del mismo tamaño
        # para que todas las filas de la app midan exactamente lo mismo y no se deforme la UI.
        if description and description.strip():
            self.lbl_desc = QLabel(f"<div style='color: #b3b3b3; font-size: 12px;'>{description}</div>")
            text_layout.addWidget(self.lbl_desc)
        else:
            self.spacer_desc = QWidget()
            self.spacer_desc.setFixedHeight(16)
            text_layout.addWidget(self.spacer_desc)

        layout.addWidget(text_container, 1, Qt.AlignVCenter)

        # Contenedor de botones (Editar / Eliminar)
        self.button_container = QWidget()
        btn_layout = QHBoxLayout(self.button_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        btn_layout.setAlignment(Qt.AlignVCenter)

        base_button_style = """
            QPushButton {
                font-family: 'Segoe UI Emoji', 'Arial', sans-serif;
                font-size: 14px; 
                background-color: transparent; 
                border: none;
                border-radius: 4px;
            }
        """

        self.btn_edit = QPushButton("⚙\uFE0E")
        self.btn_edit.setFixedSize(30, 30)
        self.btn_edit.setStyleSheet(base_button_style + """
            QPushButton { color: #b3b3b3; }
            QPushButton:hover { color: #ffffff; background-color: #3d3d3d; }
        """)
        self.btn_edit.clicked.connect(lambda: self.edit_clicked.emit(self.payload))
        btn_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("🗑\uFE0E")
        self.btn_delete.setFixedSize(30, 30)
        self.btn_delete.setStyleSheet(base_button_style + """
            QPushButton { color: #b3b3b3; }
            QPushButton:hover { color: #ffffff; background-color: #FF4552; }
        """)
        self.btn_delete.clicked.connect(lambda: self.delete_clicked.emit(self.item_name))
        btn_layout.addWidget(self.btn_delete)

        layout.addWidget(self.button_container, 0, Qt.AlignVCenter)
        self.button_container.setVisible(False)  # Ocultos por defecto

    # Control del comportamiento Hover (Efecto Spotify / Discord)
    def enterEvent(self, event):
        self.button_container.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.button_container.setVisible(False)
        super().leaveEvent(event)


# --- VENTANA PRINCIPAL ---

class ConfigApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeploX Server - Administrador")
        self.setMinimumSize(800, 700) 

        # Carga inicial y limpieza del JSON de configuración
        self.data = load_config()
        if "server" in self.data:
            del self.data["server"]
        if "groups" not in self.data:
            self.data["groups"] = []

        self.init_ui()
        self.refresh_program_list()
        self.refresh_groups_list()

    def init_ui(self):
        container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # Panel Izquierdo/Superior: Sección de Programas
        programs_group = QGroupBox("Programas")
        programs_layout = QVBoxLayout()

        btn_add_program = QPushButton("Añadir Programa")
        btn_add_program.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; font-weight: bold; 
                padding: 8px; border: none; border-radius: 4px;
            }
            QPushButton:hover { background-color: #448246; }
        """)
        btn_add_program.clicked.connect(self.open_add_program_menu)
        programs_layout.addWidget(btn_add_program)

        self.program_list = QListWidget()
        self.program_list.setSelectionMode(QListWidget.NoSelection)
        self.program_list.setStyleSheet(self.get_list_stylesheet())
        programs_layout.addWidget(self.program_list)

        programs_group.setLayout(programs_layout)
        main_layout.addWidget(programs_group)

        # Panel Derecho/Inferior: Sección de Grupos
        groups_group = QGroupBox("Grupos de Aplicaciones")
        groups_layout = QVBoxLayout()

        btn_add_group = QPushButton("Añadir Nuevo Grupo")
        btn_add_group.setStyleSheet("""
            QPushButton {
                background-color: #007acc; color: white; font-weight: bold;
                padding: 8px; border: none; border-radius: 4px;
            }
            QPushButton:hover { background-color: #0062a3; }
        """)
        btn_add_group.clicked.connect(self.open_add_group_menu)
        groups_layout.addWidget(btn_add_group)

        self.groups_list = QListWidget()
        self.groups_list.setSelectionMode(QListWidget.NoSelection)
        self.groups_list.setStyleSheet(self.get_list_stylesheet())
        groups_layout.addWidget(self.groups_list)

        groups_group.setLayout(groups_layout)
        main_layout.addWidget(groups_group)

        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def get_list_stylesheet(self):
        """Estilo CSS oscuro compartido para los QListWidget."""
        return """
            QListWidget {
                background-color: #1e1e1e; border: 1px solid #333333; border-radius: 4px; outline: 0;
            }
            QListWidget::item { border-bottom: 1px solid #2d2d2d; background-color: transparent;} 
            QListWidget::item:hover { background-color: #2d2d2d; }
        """

    # --- LÓGICA DE PROGRAMAS ---

    def open_add_program_menu(self):
        """Muestra el diálogo para registrar un nuevo programa con validaciones de ruta."""
        dialog = ProgramDialog(is_edit=False, parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            name = new_data["name"]
            exe_path = new_data["path"]

            if not name or not exe_path:
                QMessageBox.warning(self, "Error", "Nombre y ruta del ejecutable son requeridos")
                return

            if not os.path.exists(exe_path):
                QMessageBox.warning(self, "Error", f"El archivo no existe:\n{exe_path}")
                return

            self.data = add_program(self.data, name, exe_path, None)
            self.clean_and_save()
            self.refresh_program_list()
            self.animate_last_item_entry(self.program_list)

    def open_edit_menu(self, current_data):
        """Gestiona la edición de un programa y actualiza las referencias dentro de los grupos."""
        dialog = ProgramDialog(current_name=current_data["name"], current_path=current_data["path"], is_edit=True, parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            if not new_data["name"] or not new_data["path"] or not os.path.exists(new_data["path"]):
                QMessageBox.warning(self, "Error", "Verifica que los datos y la ruta del archivo sean válidos.")
                return

            # Para renombrar de forma segura: eliminamos el viejo e insertamos el nuevo
            self.data = remove_program(self.data, dialog.old_name)
            self.data = add_program(self.data, new_data["name"], new_data["path"], None)
            
            # Actualiza el nombre modificado dentro de cualquier grupo existente
            for g in self.data.get("groups", []):
                g["programs"] = [new_data["name"] if x == dialog.old_name else x for x in g["programs"]]

            self.clean_and_save()
            self.refresh_program_list()
            self.refresh_groups_list()

    def refresh_program_list(self):
        """Sincroniza la lista visual de programas con los datos del JSON."""
        self.program_list.clear()
        for program in self.data.get("programs", []):
            name = program.get("name", "Unknown")
            path = program.get("path", "N/A")

            item = QListWidgetItem()
            row_widget = GenericRowWidget(name, path, {"name": name, "path": path})
            row_widget.edit_clicked.connect(self.open_edit_menu)
            row_widget.delete_clicked.connect(self.confirm_delete_program)

            self.program_list.addItem(item)
            self.program_list.setItemWidget(item, row_widget)
            item.setSizeHint(row_widget.sizeHint())

    def confirm_delete_program(self, program_name):
        """Elimina un programa del sistema y limpia su rastro en los grupos."""
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar permanentemente '{program_name}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.data = remove_program(self.data, program_name)
            for g in self.data.get("groups", []):
                if program_name in g["programs"]:
                    g["programs"].remove(program_name)
            self.clean_and_save()
            self.refresh_program_list()
            self.refresh_groups_list()

    # --- LÓGICA DE GRUPOS ---

    def open_add_group_menu(self):
        """Muestra el formulario para crear un grupo nuevo controlando duplicados."""
        dialog = GroupDialog(all_programs=self.data.get("programs", []), parent=self)
        if dialog.exec() == QDialog.Accepted:
            res = dialog.get_data()
            if not res["name"]:
                QMessageBox.warning(self, "Error", "El grupo necesita un nombre.")
                return
            
            if any(g["name"].lower() == res["name"].lower() for g in self.data["groups"]):
                QMessageBox.warning(self, "Error", "Ya existe un grupo con ese nombre.")
                return

            self.data["groups"].append(res)
            self.clean_and_save()
            self.refresh_groups_list()
            self.animate_last_item_entry(self.groups_list)

    def open_edit_group_menu(self, group_payload):
        """Abre la configuración del grupo seleccionado para redefinir sus miembros o nombre."""
        dialog = GroupDialog(
            all_programs=self.data.get("programs", []),
            current_name=group_payload["name"],
            selected_programs=group_payload["programs"],
            parent=self
        )
        if dialog.exec() == QDialog.Accepted:
            res = dialog.get_data()
            if not res["name"]:
                return
            
            for g in self.data["groups"]:
                if g["name"] == group_payload["name"]:
                    g["name"] = res["name"]
                    g["programs"] = res["programs"]
                    break

            self.clean_and_save()
            self.refresh_groups_list()

    def refresh_groups_list(self):
        """Sincroniza la lista visual de grupos con el estado actual del backend."""
        self.groups_list.clear()
        for group in self.data.get("groups", []):
            g_name = group.get("name", "Sin Nombre")
            desc = ""  # Forzado en blanco para delegar el alto al spacer del widget

            item = QListWidgetItem()
            row_widget = GenericRowWidget(g_name, desc, group)
            row_widget.edit_clicked.connect(self.open_edit_group_menu)
            row_widget.delete_clicked.connect(self.confirm_delete_group)

            self.groups_list.addItem(item)
            self.groups_list.setItemWidget(item, row_widget)
            item.setSizeHint(row_widget.sizeHint())

    def confirm_delete_group(self, group_name):
        """Elimina la agrupación sin afectar a los programas individuales."""
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar el grupo '{group_name}'?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.data["groups"] = [g for g in self.data.get("groups", []) if g["name"] != group_name]
            self.clean_and_save()
            self.refresh_groups_list()

    # --- EFECTOS VISUALES Y CONTROL DE SALIDA ---

    def animate_last_item_entry(self, list_widget):
        """Efecto de interpolación (Fade-in) suave para nuevos elementos de la lista."""
        if list_widget.count() == 0:
            return
        last_item = list_widget.item(list_widget.count() - 1)
        last_widget = list_widget.itemWidget(last_item)
        if not last_widget:
            return

        opacity_effect = QGraphicsOpacityEffect(last_widget)
        last_widget.setGraphicsEffect(opacity_effect)

        self.entry_anim = QPropertyAnimation(opacity_effect, b"opacity")
        self.entry_anim.setDuration(600)
        self.entry_anim.setStartValue(0.0)
        self.entry_anim.setEndValue(1.0)
        self.entry_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.entry_anim.start()

    def clean_and_save(self):
        """Sanitiza el diccionario antes de volcarlo al disco duro."""
        if "server" in self.data:
            del self.data["server"]
        save_config(self.data)

    def closeEvent(self, event: QCloseEvent):
        """Evita cierres accidentales si hay diálogos o subventanas colgadas en segundo plano."""
        opened_windows = QApplication.topLevelWidgets()
        visible_windows = [w for w in opened_windows if w.isVisible()]
        
        if len(visible_windows) >= 2:
            reply = QMessageBox.question(
                self, 
                "Confirmar salida", 
                "Tienes varias ventanas abiertas. ¿Estás seguro de que quieres cerrar el programa?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                event.accept()  
            else:
                event.ignore()  
        else:
            event.accept()  


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigApp()
    window.show()
    sys.exit(app.exec())