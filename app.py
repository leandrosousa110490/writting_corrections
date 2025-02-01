import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
							QTextEdit, QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer
import language_tool_python

class GrammarCheckerApp(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Real-time Grammar Checker")
		self.setMinimumSize(800, 600)
		
		# Initialize the language tool
		self.tool = language_tool_python.LanguageTool('en-US')
		
		# Create main widget and layout
		main_widget = QWidget()
		self.setCentralWidget(main_widget)
		layout = QHBoxLayout(main_widget)
		
		# Create left side (input) layout
		left_layout = QVBoxLayout()
		input_label = QLabel("Type your text here:")
		self.input_text = QTextEdit()
		self.input_text.setPlaceholderText("Start typing here...")  # Add placeholder text
		left_layout.addWidget(input_label)
		left_layout.addWidget(self.input_text)
		
		# Create right side (output) layout
		right_layout = QVBoxLayout()
		output_label = QLabel("Corrected text:")
		self.output_text = QTextEdit()
		self.output_text.setReadOnly(True)
		self.output_text.setPlaceholderText("Corrected text will appear here...")  # Add placeholder text
		right_layout.addWidget(output_label)
		right_layout.addWidget(self.output_text)
		
		# Add layouts to main layout
		layout.addLayout(left_layout)
		layout.addLayout(right_layout)
		
		# Setup timer for delayed checking
		self.timer = QTimer()
		self.timer.setSingleShot(True)
		self.timer.timeout.connect(self.check_grammar)
		
		# Connect text change to timer
		self.input_text.textChanged.connect(self.start_timer)
		
		# Set enhanced style
		self.setStyleSheet("""
			QMainWindow {
				background-color: #f0f0f0;
			}
			QTextEdit {
				background-color: white;
				border: 2px solid #666;
				border-radius: 4px;
				padding: 10px;
				font-size: 16px;
				color: #333;
				selection-background-color: #0078d4;
				selection-color: white;
			}
			QTextEdit:focus {
				border-color: #0078d4;
			}
			QLabel {
				font-size: 16px;
				font-weight: bold;
				color: #333;
				margin-bottom: 8px;
			}
			QTextEdit[readOnly="true"] {
				background-color: #f8f8f8;
				border-color: #999;
			}
		""")
	
	def start_timer(self):
		"""Start timer to delay grammar checking"""
		self.timer.start(1000)  # Wait for 1 second after last keystroke
	
	def check_grammar(self):
		"""Check grammar and update the output text"""
		try:
			input_text = self.input_text.toPlainText()
			if not input_text.strip():
				self.output_text.clear()
				return
				
			# Get corrections
			matches = self.tool.check(input_text)
			corrected_text = language_tool_python.utils.correct(input_text, matches)
			
			# Update output
			self.output_text.setPlainText(corrected_text)
			
		except Exception as e:
			self.output_text.setPlainText(f"Error checking grammar: {str(e)}")

def main():
	app = QApplication(sys.argv)
	window = GrammarCheckerApp()
	window.show()
	sys.exit(app.exec())

if __name__ == '__main__':
	main()
