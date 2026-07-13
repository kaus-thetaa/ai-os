import summarizer
import config

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QTextEdit, QFileDialog
)


class SummarizePanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("summarize a file or folder")
        layout.addWidget(title)

        path_row = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("paste a file or folder path here")
        path_row.addWidget(self.path_input)

        browse_file_button = QPushButton("browse file")
        browse_file_button.clicked.connect(self._browse_file)
        path_row.addWidget(browse_file_button)

        browse_folder_button = QPushButton("browse folder")
        browse_folder_button.clicked.connect(self._browse_folder)
        path_row.addWidget(browse_folder_button)

        layout.addLayout(path_row)

        self.summarize_button = QPushButton("summarize")
        self.summarize_button.clicked.connect(self._run_summary)
        layout.addWidget(self.summarize_button)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

    def _browse_file(self) -> None:
        # opens the native file picker and fills the path box
        file_path, _ = QFileDialog.getOpenFileName(self, "select a file")
        if file_path:
            self.path_input.setText(file_path)

    def _browse_folder(self) -> None:
        # opens the native folder picker and fills the path box
        folder_path = QFileDialog.getExistingDirectory(self, "select a folder")
        if folder_path:
            self.path_input.setText(folder_path)

    def _run_summary(self) -> None:
        # decides file vs folder and calls the right summarizer function
        path_text = self.path_input.text().strip()
        if not path_text:
            self.result_area.setPlainText("please enter a file or folder path")
            return

        path = Path(path_text)
        if not path.exists():
            self.result_area.setPlainText(f"'{path_text}' does not exist")
            return

        self.summarize_button.setEnabled(False)
        self.summarize_button.setText("summarizing...")
        self.result_area.setPlainText("working on it, this can take a moment")

        # process pending ui events so the message above actually shows
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            if path.is_file():
                summary = summarizer.summarize_file(str(path))
                self.result_area.setPlainText(summary)
            else:
                result = summarizer.summarize_folder(str(path), recursive=False)
                output_lines = [
                    "overview",
                    result["folder_summary"],
                    "",
                    f"files found: {result['total_files_found']}",
                    f"files skipped: {result['files_skipped']}",
                    "",
                    "individual file summaries",
                ]
                for file_name, file_summary in result["file_summaries"].items():
                    output_lines.append(f"\n{file_name}")
                    output_lines.append(file_summary)

                self.result_area.setPlainText("\n".join(output_lines))

        except summarizer.SummarizerError as error:
            self.result_area.setPlainText(f"failed - {error}")

        self.summarize_button.setEnabled(True)
        self.summarize_button.setText("summarize")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import styles

    app = QApplication(sys.argv)
    app.setStyleSheet(styles.get_stylesheet())

    panel = SummarizePanel()
    panel.resize(700, 500)
    panel.show()

    sys.exit(app.exec())