import duplicate_finder
import file_scanner

import sys
from pathlib import Path
from send2trash import send2trash
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QFileDialog
)
from PyQt6.QtCore import Qt

class DuplicatesPanel(QWidget):
    def __init__(self):
        super().__init__()

        # keeps track of which files can still be deleted, keyed by list item
        self.deletable_paths = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("find duplicate files")
        layout.addWidget(title)

        path_row = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("paste a folder path here")
        path_row.addWidget(self.path_input)

        browse_button = QPushButton("browse folder")
        browse_button.clicked.connect(self._browse_folder)
        path_row.addWidget(browse_button)

        layout.addLayout(path_row)

        self.find_button = QPushButton("find duplicates")
        self.find_button.clicked.connect(self._run_find)
        layout.addWidget(self.find_button)

        self.status_label = QLabel()
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

        self.results_list = QListWidget()
        layout.addWidget(self.results_list)

        self.delete_button = QPushButton("send selected to recycle bin")
        self.delete_button.clicked.connect(self._delete_selected)
        layout.addWidget(self.delete_button)

    def _browse_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "select a folder")
        if folder_path:
            self.path_input.setText(folder_path)

    def _run_find(self) -> None:
        # scans the folder and lists every duplicate group found
        folder_text = self.path_input.text().strip()
        if not folder_text:
            self.status_label.setText("please enter a folder path")
            return

        self.find_button.setEnabled(False)
        self.find_button.setText("scanning...")
        self.results_list.clear()
        self.deletable_paths = {}

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            groups = duplicate_finder.find_duplicates(folder_text, recursive=False)
            wasted = duplicate_finder.get_total_wasted_space(groups)

            if not groups:
                self.status_label.setText("no duplicates found")
            else:
                readable_wasted = file_scanner.format_file_size(wasted)
                self.status_label.setText(f"{len(groups)} duplicate group(s) found, {readable_wasted} could be freed")

                for group in groups:
                    keep_path = group["suggested_keep"]

                    keep_item = QListWidgetItem(f"keep:  {Path(keep_path).name}")
                    self.results_list.addItem(keep_item)

                    for file_path in group["files"]:
                        if file_path == keep_path:
                            continue

                        item = QListWidgetItem(f"duplicate:  {Path(file_path).name}")
                        item.setCheckState(Qt_Unchecked)
                        self.results_list.addItem(item)
                        self.deletable_paths[id(item)] = file_path

        except duplicate_finder.DuplicateFinderError as error:
            self.status_label.setText(f"failed - {error}")

        self.find_button.setEnabled(True)
        self.find_button.setText("find duplicates")

    def _delete_selected(self) -> None:
        # sends every checked duplicate to the recycle bin, never permanent delete
        deleted_count = 0
        failed_count = 0

        for index in range(self.results_list.count()):
            item = self.results_list.item(index)

            if id(item) not in self.deletable_paths:
                continue

            if item.checkState() != Qt_Checked:
                continue

            file_path = self.deletable_paths[id(item)]

            try:
                send2trash(file_path)
                deleted_count += 1
            except Exception:
                failed_count += 1

        self.status_label.setText(f"sent {deleted_count} file(s) to recycle bin, {failed_count} failed")

        if deleted_count > 0:
            self._run_find()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    import styles

    Qt_Checked = Qt.CheckState.Checked
    Qt_Unchecked = Qt.CheckState.Unchecked

    app = QApplication(sys.argv)
    app.setStyleSheet(styles.get_stylesheet())

    panel = DuplicatesPanel()
    panel.resize(700, 500)
    panel.show()

    sys.exit(app.exec())