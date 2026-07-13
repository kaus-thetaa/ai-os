import organizer
import command_interpreter
import file_scanner

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QTextEdit, QFileDialog
)


class OrganizePanel(QWidget):
    def __init__(self):
        super().__init__()

        # holds the parsed plan waiting for confirmation
        self.pending_plan = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("organize a folder")
        layout.addWidget(title)

        path_row = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("paste a folder path here")
        path_row.addWidget(self.path_input)

        browse_button = QPushButton("browse folder")
        browse_button.clicked.connect(self._browse_folder)
        path_row.addWidget(browse_button)

        layout.addLayout(path_row)

        self.default_organize_button = QPushButton("organize by type")
        self.default_organize_button.clicked.connect(self._run_default_organize)
        layout.addWidget(self.default_organize_button)

        command_label = QLabel("or type a custom instruction")
        layout.addWidget(command_label)

        command_row = QHBoxLayout()

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("example: separate images and videos into two folders")
        command_row.addWidget(self.command_input)

        self.plan_button = QPushButton("plan command")
        self.plan_button.clicked.connect(self._plan_command)
        command_row.addWidget(self.plan_button)

        layout.addLayout(command_row)

        self.confirm_button = QPushButton("confirm and execute")
        self.confirm_button.clicked.connect(self._execute_command)
        self.confirm_button.setEnabled(False)
        layout.addWidget(self.confirm_button)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

    def _browse_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "select a folder")
        if folder_path:
            self.path_input.setText(folder_path)

    def _get_target_folder(self) -> str:
        return self.path_input.text().strip()

    def _run_default_organize(self) -> None:
        # runs the built in category sort immediately, no confirmation needed
        folder_text = self._get_target_folder()
        if not folder_text:
            self.result_area.setPlainText("please enter a folder path")
            return

        self.default_organize_button.setEnabled(False)
        self.default_organize_button.setText("organizing...")

        try:
            result = organizer.organize_by_default_categories(folder_text)
            lines = [f"files moved: {result['files_moved']}", f"files skipped: {result['files_skipped']}", ""]
            for name, destination in result["moves"]:
                lines.append(f"{name}  ->  {destination}/")
            self.result_area.setPlainText("\n".join(lines))
        except organizer.OrganizerError as error:
            self.result_area.setPlainText(f"failed - {error}")

        self.default_organize_button.setEnabled(True)
        self.default_organize_button.setText("organize by type")

    def _plan_command(self) -> None:
        # parses the instruction into a plan but does not execute it yet
        folder_text = self._get_target_folder()
        instruction_text = self.command_input.text().strip()

        if not folder_text or not instruction_text:
            self.result_area.setPlainText("please enter both a folder path and an instruction")
            return

        full_instruction = f"go to {folder_text} and {instruction_text}"

        self.plan_button.setEnabled(False)
        self.plan_button.setText("thinking...")
        self.confirm_button.setEnabled(False)
        self.pending_plan = None

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        try:
            plan = command_interpreter.parse_command(full_instruction)
            self.pending_plan = plan
            self.result_area.setPlainText(f"planned action\n\n{plan}\n\nreview this plan then click confirm and execute")
            self.confirm_button.setEnabled(True)
        except command_interpreter.CommandInterpreterError as error:
            self.result_area.setPlainText(f"failed - {error}")

        self.plan_button.setEnabled(True)
        self.plan_button.setText("plan command")

    def _execute_command(self) -> None:
        # this is the only place the planned action actually runs
        if self.pending_plan is None:
            return

        self.confirm_button.setEnabled(False)
        self.confirm_button.setText("executing...")

        try:
            result = command_interpreter.execute_plan(self.pending_plan)
            self.result_area.setPlainText(f"done\n\n{result}")
        except command_interpreter.CommandInterpreterError as error:
            self.result_area.setPlainText(f"failed - {error}")

        self.pending_plan = None
        self.confirm_button.setText("confirm and execute")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import styles

    app = QApplication(sys.argv)
    app.setStyleSheet(styles.get_stylesheet())

    panel = OrganizePanel()
    panel.resize(700, 500)
    panel.show()

    sys.exit(app.exec())