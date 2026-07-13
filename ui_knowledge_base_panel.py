import knowledge_base
import vector_store

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QFileDialog
)


class KnowledgeBasePanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("knowledge base")
        layout.addWidget(title)

        path_row = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("paste a folder path here")
        path_row.addWidget(self.path_input)

        browse_button = QPushButton("browse folder")
        browse_button.clicked.connect(self._browse_folder)
        path_row.addWidget(browse_button)

        layout.addLayout(path_row)

        self.build_button = QPushButton("build knowledge base")
        self.build_button.clicked.connect(self._run_build)
        layout.addWidget(self.build_button)

        self.status_label = QLabel()
        self.status_label.setProperty("secondary", "true")
        self._update_status()
        layout.addWidget(self.status_label)

        query_row = QHBoxLayout()

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("search across pdfs, docx, and text files")
        self.query_input.returnPressed.connect(self._run_search)
        query_row.addWidget(self.query_input)

        self.search_button = QPushButton("search")
        self.search_button.clicked.connect(self._run_search)
        query_row.addWidget(self.search_button)

        layout.addLayout(query_row)

        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

    def _update_status(self) -> None:
        # shows how many files are currently in the shared vector store
        try:
            count = vector_store.get_item_count()
            self.status_label.setText(f"indexed items: {count}")
        except vector_store.VectorStoreError:
            self.status_label.setText("index status unavailable")

    def _browse_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "select a folder")
        if folder_path:
            self.path_input.setText(folder_path)

    def _run_build(self) -> None:
        # reads pdfs, docx, and text files and adds them to the shared index
        folder_text = self.path_input.text().strip()
        if not folder_text:
            self.status_label.setText("please enter a folder path")
            return

        self.build_button.setEnabled(False)
        self.build_button.setText("building...")

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            result = knowledge_base.build_knowledge_base(folder_text, recursive=False)
            self.status_label.setText(
                f"indexed {result['files_indexed']} of {result['total_files_found']} files, "
                f"{result['files_skipped']} skipped"
            )
        except knowledge_base.KnowledgeBaseError as error:
            self.status_label.setText(f"failed - {error}")

        self.build_button.setEnabled(True)
        self.build_button.setText("build knowledge base")

    def _run_search(self) -> None:
        # searches the shared vector store across every indexed file type
        query = self.query_input.text().strip()
        if not query:
            return

        self.search_button.setEnabled(False)
        self.search_button.setText("searching...")
        self.results_list.clear()

        try:
            raw_results = vector_store.search_similar(query, max_results=10)

            if not raw_results:
                self.results_list.addItem("no results found")
            else:
                for result in raw_results:
                    distance = result["distance"]
                    relevance = round(1.0 / (1.0 + distance), 4)
                    preview = result["text"][:200].replace("\n", " ").strip()

                    text = f"{result['metadata']['file_name']}  (relevance {relevance})\n{preview}"
                    self.results_list.addItem(QListWidgetItem(text))

        except vector_store.VectorStoreError as error:
            self.results_list.addItem(f"search failed - {error}")

        self.search_button.setEnabled(True)
        self.search_button.setText("search")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import styles

    app = QApplication(sys.argv)
    app.setStyleSheet(styles.get_stylesheet())

    panel = KnowledgeBasePanel()
    panel.resize(700, 500)
    panel.show()

    sys.exit(app.exec())