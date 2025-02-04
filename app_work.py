import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QTextEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QStatusBar)
from PyQt6.QtGui import (QAction, QFont, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QColor)
from PyQt6.QtCore import Qt, QTimer, QRegularExpression, QSettings
from textblob import TextBlob


class SpellCheckHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Format for spelling/grammar errors (red wavy underline)
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        self.error_format.setUnderlineColor(QColor("red"))
        
        self.errors = []
        self.cache = {}  # Cache for word corrections

    def check_text(self, text):
        """Check text using TextBlob"""
        try:
            words = text.split()
            self.errors = []
            
            current_pos = 0
            for word in words:
                # Skip single letters and numbers
                if len(word) <= 1 or word.isdigit():
                    current_pos += len(word) + 1
                    continue
                    
                # Check cache first
                key = word.lower()
                if key in self.cache:
                    corrected = self.cache[key]
                else:
                    # Get correction using TextBlob
                    blob = TextBlob(word)
                    corrected = str(blob.correct())
                    self.cache[key] = corrected
                
                # If the corrected word differs from original
                if corrected.lower() != key:
                    self.errors.append((current_pos, len(word)))
                current_pos += len(word) + 1  # +1 for space
            
        except Exception as e:
            print(f"Text check error: {e}")
            self.errors = []

    def highlightBlock(self, text):
        """Highlight the block of text"""
        self.check_text(text)
        
        # Apply error formatting
        for start, length in self.errors:
            if start < len(text):
                actual_length = min(length, len(text) - start)
                self.setFormat(start, actual_length, self.error_format)


class GrammarCheckerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('TextCorrectionApp', 'Settings')
        self.always_on_top = self.settings.value('always_on_top', False, bool)
        self.load_settings()
        self.init_ui()
        self.update_window_flags()

    def update_window_flags(self):
        """Update window flags based on always-on-top setting"""
        if self.always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def load_settings(self):
        """Load application settings"""
        self.window_geometry = self.settings.value('window_geometry')
        self.font_size = self.settings.value('font_size', 11, int)  # Smaller default font
        self.auto_check_delay = self.settings.value('auto_check_delay', 500, int)  # Faster check
        self.always_on_top = self.settings.value('always_on_top', False, bool)

    def save_settings(self):
        """Save application settings"""
        self.settings.setValue('window_geometry', self.saveGeometry())
        self.settings.setValue('font_size', self.font_size)
        self.settings.setValue('auto_check_delay', self.auto_check_delay)
        self.settings.setValue('always_on_top', self.always_on_top)

    def closeEvent(self, event):
        """Override close event to save settings"""
        self.save_settings()
        super().closeEvent(event)

    def init_ui(self):
        self.setWindowTitle("Grammar Checker")
        # Apply saved window geometry if exists
        if self.window_geometry:
            self.restoreGeometry(self.window_geometry)
        else:
            self.setGeometry(100, 100, 400, 300)  # Even smaller default size

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)  # Smaller margins
        main_layout.setSpacing(4)  # Tighter spacing

        # Input section
        self.text_input = QTextEdit()
        self.text_input.setFont(QFont("Segoe UI", 10))  # Smaller font
        self.text_input.setPlaceholderText("Type or paste your text here...")
        self.text_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dadada;
                border-radius: 3px;
                padding: 4px;
                background-color: white;
                color: #333333;
                min-height: 60px;
            }
            QTextEdit:focus {
                border: 1px solid #999999;
            }
        """)
        main_layout.addWidget(self.text_input)

        # Attach enhanced highlighter
        self.highlighter = SpellCheckHighlighter(self.text_input.document())

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)  # Tighter button spacing

        # Modern minimal button style - smaller buttons
        button_style = """
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #dadada;
                padding: 4px 8px;
                border-radius: 3px;
                min-width: 60px;
                max-height: 24px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background-color: #ebebeb;
            }
        """

        # Create and style buttons
        correct_button = QPushButton("Fix")  # Shorter labels
        clear_button = QPushButton("Clear")
        copy_button = QPushButton("Copy")
        always_top_button = QPushButton("📌")  # Pin icon instead of text

        always_top_button.setCheckable(True)
        always_top_button.setChecked(self.always_on_top)

        for button in [correct_button, clear_button, copy_button, always_top_button]:
            button.setFont(QFont("Segoe UI", 9))  # Smaller font for buttons
            button.setStyleSheet(button_style)
            buttons_layout.addWidget(button)

        correct_button.clicked.connect(self.on_correct)
        clear_button.clicked.connect(self.clear_text)
        copy_button.clicked.connect(self.copy_output)
        always_top_button.clicked.connect(self.toggle_always_on_top)

        main_layout.addLayout(buttons_layout)

        # Output section
        self.text_output = QTextEdit()
        self.text_output.setFont(QFont("Segoe UI", 10))  # Smaller font
        self.text_output.setReadOnly(True)
        self.text_output.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dadada;
                border-radius: 3px;
                padding: 4px;
                background-color: #fafafa;
                color: #333333;
                min-height: 60px;
            }
        """)
        main_layout.addWidget(self.text_output)

        central_widget.setLayout(main_layout)

        # Status bar with minimal style
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("""
            QStatusBar {
                border-top: 1px solid #dadada;
                min-height: 16px;
                max-height: 16px;
                padding: 0px;
                font-size: 9px;
                color: #666666;
            }
        """)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Set up enhanced auto-correction timer
        self.correction_timer = QTimer(self)
        self.correction_timer.setSingleShot(True)
        self.correction_timer.timeout.connect(self.auto_check)
        self.text_input.textChanged.connect(self.on_text_changed)

    def toggle_always_on_top(self, checked):
        """Toggle always-on-top state"""
        self.always_on_top = checked
        self.update_window_flags()
        self.save_settings()

    def on_text_changed(self):
        """Handler for text changes"""
        self.correction_timer.start(self.auto_check_delay)  # Use saved delay
        self.statusBar.showMessage("Typing...")

    def auto_check(self):
        """Automatically check text after typing stops"""
        self.highlighter.rehighlight()
        self.statusBar.showMessage("Checked", 2000)

    def on_correct(self):
        """Enhanced text correction"""
        text = self.text_input.toPlainText().strip()
        if not text:
            self.statusBar.showMessage("Please enter text to correct", 2000)
            return
            
        try:
            # Enhanced correction with TextBlob
            blob = TextBlob(text)
            corrected = str(blob.correct())
            
            # Additional grammar improvements could be added here
            
            self.text_output.setPlainText(corrected)
            self.statusBar.showMessage("Text corrected", 2000)
            
        except Exception as e:
            self.statusBar.showMessage(f"Error: {str(e)}", 3000)

    def clear_text(self):
        """Clear both input and output fields"""
        self.text_input.clear()
        self.text_output.clear()
        self.statusBar.showMessage("Cleared", 2000)

    def copy_output(self):
        """Copy corrected text to clipboard"""
        output = self.text_output.toPlainText().strip()
        if output:
            clipboard = QApplication.clipboard()
            clipboard.setText(output)
            self.statusBar.showMessage("Text copied to clipboard!", 2000)
            QMessageBox.information(self, "Copied", "The corrected text has been copied to clipboard.")
        else:
            self.statusBar.showMessage("No text to copy", 2000)
            QMessageBox.warning(self, "Warning", "There is no corrected text to copy!")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.information(
            self,
            "About",
            "Advanced Text Correction App v2.0\n\n"
            "Features:\n"
            "- Real-time spell checking\n"
            "- Automatic text correction\n"
            "- Modern user interface\n"
            "- Fast performance\n\n"
            "Using TextBlob for intelligent text correction."
        )


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = GrammarCheckerApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Application error: {e}")
