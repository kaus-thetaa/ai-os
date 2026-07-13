import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt

import config
import styles
import llm_engine


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.resize(1100, 700)
        self.setStyleSheet(styles.get_stylesheet())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        main_layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        self._build_placeholder_pages()
        self._connect_sidebar_buttons()

        # default to the first page on startup
        self.sidebar_buttons[0].setChecked(True)
        self.content_stack.setCurrentIndex(0)

    def _build_sidebar(self) -> QFrame:
        # builds the left navigation panel with one button per feature
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(0)

        title_label = QLabel(config.APP_NAME)
        title_label.setContentsMargins(14, 0, 0, 20)
        layout.addWidget(title_label)

        self.sidebar_buttons = []
        feature_names = [
            "Search",
            "Summarize",
            "Rename",
            "Organize",
            "Duplicates",
            "Knowledge Base",
        ]

        for name in feature_names:
            button = QPushButton(name)
            button.setObjectName("sidebarButton")
            button.setCheckable(True)
            layout.addWidget(button)
            self.sidebar_buttons.append(button)

        layout.addStretch()

        self.status_label = QLabel()
        self.status_label.setProperty("secondary", "true")
        self.status_label.setContentsMargins(14, 0, 0, 14)
        self._update_ollama_status()
        layout.addWidget(self.status_label)

        return sidebar

    def _update_ollama_status(self) -> None:
        # checks ollama connection and shows a small status line
        if llm_engine.is_ollama_available():
            self.status_label.setText("ollama: connected")
        else:
            self.status_label.setText("ollama: not running")

    def _build_placeholder_pages(self) -> None:
        # temporary pages until each real panel file is built
        feature_names = [
            "Search",
            "Summarize",
            "Rename",
            "Organize",
            "Duplicates",
            "Knowledge Base",
        ]

        for name in feature_names:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            label = QLabel(f"{name} panel coming soon")
            page_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
            self.content_stack.addWidget(page)

    def _connect_sidebar_buttons(self) -> None:
        # clicking a sidebar button switches the visible page
        for index, button in enumerate(self.sidebar_buttons):
            button.clicked.connect(lambda checked, i=index: self._switch_page(i))

    def _switch_page(self, index: int) -> None:
        self.content_stack.setCurrentIndex(index)

        for i, button in enumerate(self.sidebar_buttons):
            button.setChecked(i == index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())