import search_engine
import summarizer
import renamer
import organizer
import duplicate_finder
import knowledge_base
import vector_store
import command_interpreter

import ui_search_panel
import ui_summarize_panel
import ui_rename_panel
import ui_organize_panel
import ui_duplicates_panel
import ui_knowledge_base_panel
import ui_main_window
import styles

import sys
from PyQt6.QtWidgets import QApplication

def build_main_window() -> ui_main_window.MainWindow:
    # creates the main window and swaps every placeholder for the real panel
    window = ui_main_window.MainWindow()

    real_panels = [
        ui_search_panel.SearchPanel(),
        ui_summarize_panel.SummarizePanel(),
        ui_rename_panel.RenamePanel(),
        ui_organize_panel.OrganizePanel(),
        ui_duplicates_panel.DuplicatesPanel(),
        ui_knowledge_base_panel.KnowledgeBasePanel(),
    ]

    for index, panel in enumerate(real_panels):
        old_widget = window.content_stack.widget(index)
        window.content_stack.removeWidget(old_widget)
        old_widget.deleteLater()
        window.content_stack.insertWidget(index, panel)

    window.content_stack.setCurrentIndex(0)

    return window


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(styles.get_stylesheet())

    window = build_main_window()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()