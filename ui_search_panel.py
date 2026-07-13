import search_engine
import config

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel
)
from PyQt6.QtCore import Qt
class SearchPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("search files")
        layout.addWidget(title)

        top_row = QHBoxLayout()

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("search using plain english")
        self.query_input.returnPressed.connect(self._run_search)
        top_row.addWidget(self.query_input)

        self.search_button = QPushButton("search")
        self.search_button.clicked.connect(self._run_search)
        top_row.addWidget(self.search_button)

        layout.addLayout(top_row)

        status_row = QHBoxLayout()

        self.status_label = QLabel()
        self.status_label.setProperty("secondary", "true")
        self._update_index_status()
        status_row.addWidget(self.status_label)

        status_row.addStretch()

        self.index_button = QPushButton("index downloads")
        self.index_button.clicked.connect(self._run_indexing)
        status_row.addWidget(self.index_button)

        layout.addLayout(status_row)

        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

    def _update_index_status(self) -> None:
        # shows how many files are currently searchable
        try:
            status = search_engine.get_index_status()
            self.status_label.setText(f"indexed files: {status['total_indexed_files']}")
        except search_engine.SearchEngineError:
            self.status_label.setText("index status unavailable")

    def _run_indexing(self) -> None:
        # indexes the downloads folder and updates the status line
        self.index_button.setEnabled(False)
        self.index_button.setText("indexing...")

        try:
            result = search_engine.index_folder(str(config.DOWNLOADS_DIR), recursive=False)
            self._update_index_status()
        except search_engine.SearchEngineError as error:
            self.status_label.setText(f"indexing failed: {error}")

        self.index_button.setEnabled(True)
        self.index_button.setText("index downloads")

    def _run_search(self) -> None:
        # runs a search and fills the results list
        query = self.query_input.text().strip()
        if not query:
            return

        self.search_button.setEnabled(False)
        self.search_button.setText("searching...")
        self.results_list.clear()

        try:
            results = search_engine.search_files(query, max_results=10)

            if not results:
                self.results_list.addItem("no results found")
            else:
                for result in results:
                    preview = result["content_preview"]
                    text = (
                        f"{result['file_name']}  "
                        f"(relevance {result['relevance_score']})\n"
                        f"{preview}"
                    )
                    item = QListWidgetItem(text)
                    self.results_list.addItem(item)

        except search_engine.SearchEngineError as error:
            self.results_list.addItem(f"search failed: {error}")

        self.search_button.setEnabled(True)
        self.search_button.setText("search")


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    import styles

    app = QApplication(sys.argv)
    app.setStyleSheet(styles.get_stylesheet())

    panel = SearchPanel()
    panel.resize(700, 500)
    panel.show()

    sys.exit(app.exec())