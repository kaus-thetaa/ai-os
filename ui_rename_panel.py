import renamer
import file_scanner

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QFileDialog
)


class RenamePanel(QWidget):
    def __init__(self):
        super().__init__()

        # holds the pending suggestions before they are applied
        self.pending_suggestions = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("rename files based on content")
        layout.addWidget(title)

        path_row = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("paste a folder path here")
        path_row.addWidget(self.path_input)

        browse_button = QPushButton("browse folder")
        browse_button.clicked.connect(self._browse_folder)
        path_row.addWidget(browse_button)

        layout.addLayout(path_row)

        self.suggest_button = QPushButton("suggest names")
        self.suggest_button.clicked.connect(self._run_suggestions)
        layout.addWidget(self.suggest_button)

        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

        self.apply_button = QPushButton("apply all renames")
        self.apply_button.clicked.connect(self._apply_renames)
        self.apply_button.setEnabled(False)
        layout.addWidget(self.apply_button)

        self.status_label = QLabel()
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

    def _browse_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "select a folder")
        if folder_path:
            self.path_input.setText(folder_path)

    def _run_suggestions(self) -> None:
        # generates suggestions only, does not touch any files yet
        folder_text = self.path_input.text().strip()
        if not folder_text:
            self.status_label.setText("please enter a folder path")
            return

        folder = Path(folder_text)
        if not folder.exists() or not folder.is_dir():
            self.status_label.setText(f"'{folder_text}' does not exist or is not a folder")
            return

        self.suggest_button.setEnabled(False)
        self.suggest_button.setText("thinking...")
        self.results_list.clear()
        self.pending_suggestions = []

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            all_files = file_scanner.list_files_in_folder(str(folder), recursive=False)
        except file_scanner.FileScannerError as error:
            self.status_label.setText(f"failed - {error}")
            self.suggest_button.setEnabled(True)
            self.suggest_button.setText("suggest names")
            return

        for file_path in all_files:
            file_type = file_scanner.classify_file_type(str(file_path))
            if file_type != "text":
                continue

            try:
                suggested_name = renamer.suggest_filename(str(file_path))
            except renamer.RenamerError:
                continue

            if suggested_name == file_path.name:
                continue

            self.pending_suggestions.append({
                "original_path": str(file_path),
                "original_name": file_path.name,
                "suggested_name": suggested_name,
            })

            item_text = f"{file_path.name}  ->  {suggested_name}"
            self.results_list.addItem(QListWidgetItem(item_text))

        if self.pending_suggestions:
            self.status_label.setText(f"{len(self.pending_suggestions)} suggestion(s) ready, review then apply")
            self.apply_button.setEnabled(True)
        else:
            self.status_label.setText("no rename suggestions found for this folder")
            self.apply_button.setEnabled(False)

        self.suggest_button.setEnabled(True)
        self.suggest_button.setText("suggest names")

    def _apply_renames(self) -> None:
        # this is the only place actual renaming happens on disk
        self.apply_button.setEnabled(False)
        self.apply_button.setText("applying...")

        renamed_count = 0
        failed_count = 0

        for suggestion in self.pending_suggestions:
            try:
                renamer.rename_file(suggestion["original_path"], suggestion["suggested_name"])
                renamed_count += 1
            except renamer.RenamerError:
                failed_count += 1

        self.status_label.setText(f"renamed {renamed_count} file(s), {failed_count} failed")
        self.results_list.clear()
        self.pending_suggestions = []
        self.apply_button.setEnabled(False)
        self.apply_button.setText("apply all renames")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import styles

    app = QApplication(sys.argv)
    app.setStyleSheet(styles.get_stylesheet())

    panel = RenamePanel()
    panel.resize(700, 500)
    panel.show()

    sys.exit(app.exec())
    