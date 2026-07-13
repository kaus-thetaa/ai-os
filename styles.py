import config


def get_stylesheet() -> str:
    # returns the full qss stylesheet string for the whole app
    return f"""

    QMainWindow {{
        background-color: {config.UI_BACKGROUND_COLOR};
    }}

    QWidget {{
        background-color: {config.UI_BACKGROUND_COLOR};
        color: {config.UI_TEXT_COLOR};
        font-family: {config.UI_FONT_FAMILY};
        font-size: {config.UI_FONT_SIZE_NORMAL}pt;
    }}

    QLabel {{
        background-color: transparent;
        color: {config.UI_TEXT_COLOR};
    }}

    QLabel[secondary="true"] {{
        color: {config.UI_TEXT_COLOR};
        font-size: {config.UI_FONT_SIZE_SMALL}pt;
    }}

    QPushButton {{
        background-color: {config.UI_BACKGROUND_COLOR};
        color: {config.UI_TEXT_COLOR};
        border: 1px solid {config.UI_BORDER_COLOR};
        padding: 6px 12px;
    }}

    QPushButton:hover {{
        border: 1px solid {config.UI_ACCENT_COLOR};
    }}

    QPushButton:pressed {{
        background-color: {config.UI_BORDER_COLOR};
    }}

    QPushButton:disabled {{
        color: {config.UI_BORDER_COLOR};
        border: 1px solid {config.UI_BORDER_COLOR};
    }}

    QLineEdit {{
        background-color: {config.UI_BACKGROUND_COLOR};
        color: {config.UI_TEXT_COLOR};
        border: 1px solid {config.UI_BORDER_COLOR};
        padding: 6px;
    }}

    QLineEdit:focus {{
        border: 1px solid {config.UI_ACCENT_COLOR};
    }}

    QTextEdit {{
        background-color: {config.UI_BACKGROUND_COLOR};
        color: {config.UI_TEXT_COLOR};
        border: 1px solid {config.UI_BORDER_COLOR};
    }}

    QListWidget {{
        background-color: {config.UI_BACKGROUND_COLOR};
        color: {config.UI_TEXT_COLOR};
        border: 1px solid {config.UI_BORDER_COLOR};
    }}

    QListWidget::item {{
        padding: 6px;
        border-bottom: 1px solid {config.UI_BORDER_COLOR};
    }}

    QListWidget::item:selected {{
        background-color: {config.UI_BORDER_COLOR};
        color: {config.UI_ACCENT_COLOR};
    }}

    QFrame#sidebar {{
        background-color: {config.UI_BACKGROUND_COLOR};
        border-right: 1px solid {config.UI_BORDER_COLOR};
    }}

    QPushButton#sidebarButton {{
        background-color: {config.UI_BACKGROUND_COLOR};
        color: {config.UI_TEXT_COLOR};
        border: none;
        text-align: left;
        padding: 10px 14px;
    }}

    QPushButton#sidebarButton:hover {{
        background-color: {config.UI_BORDER_COLOR};
    }}

    QPushButton#sidebarButton:checked {{
        background-color: {config.UI_BORDER_COLOR};
        color: {config.UI_ACCENT_COLOR};
        border-left: 2px solid {config.UI_ACCENT_COLOR};
    }}

    QScrollBar:vertical {{
        background-color: {config.UI_BACKGROUND_COLOR};
        width: 10px;
        border: none;
    }}

    QScrollBar::handle:vertical {{
        background-color: {config.UI_BORDER_COLOR};
        min-height: 20px;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QProgressBar {{
        background-color: {config.UI_BACKGROUND_COLOR};
        border: 1px solid {config.UI_BORDER_COLOR};
        text-align: center;
        color: {config.UI_TEXT_COLOR};
    }}

    QProgressBar::chunk {{
        background-color: {config.UI_ACCENT_COLOR};
    }}

    """


if __name__ == "__main__":
    print("styles.py self-test")
    print("-" * 50)

    stylesheet = get_stylesheet()
    print(f"stylesheet length: {len(stylesheet)} characters")

    if config.UI_BACKGROUND_COLOR in stylesheet:
        print("ok - background color present in stylesheet")
    else:
        print("mismatch - background color missing")

    if config.UI_FONT_FAMILY in stylesheet:
        print("ok - font family present in stylesheet")
    else:
        print("mismatch - font family missing")

    print("-" * 50)
    print("styles.py self-test complete")