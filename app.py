import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
							QTextEdit, QLabel, QHBoxLayout, QPushButton)
from PyQt6.QtCore import Qt, QTimer
import language_tool_python
import re

class GrammarCheckerApp(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Advanced Grammar Checker")
		self.setMinimumSize(1200, 800)
		
		# Initialize the language tool with all rules enabled
		self.tool = language_tool_python.LanguageTool('en-US', config={'maxSpellingSuggestions': 10})
		
		# Enhanced punctuation rules
		self.punctuation_rules = {
			r'\s+\.': '.',  # Remove space before period
			r'\s+,': ',',   # Remove space before comma
			r'[\.,]\s*[\.,]+': '.',  # Fix multiple periods/commas
			r'\s+(?=[\.,:;!?])': '',  # Remove spaces before punctuation
			r'(?<=[\.!?])\s*(?=[a-zA-Z])': ' ',  # Ensure space after sentence-ending punctuation
			r'(?<=\w),(?=\w)': ', ',  # Ensure space after comma between words
			r'(?<=\w)(?=[A-Z])': '. ',  # Add period before capital letters that likely start new sentences
			r'(?<=\w)\s+(?=[,])': '',  # Remove spaces before commas
			r'(?<=\d)\s+(?=[,\.])\s*(?=\d)': '',  # Fix spacing in numbers
			r'(?<=[a-z])\s*\n\s*(?=[a-z])': ' ',  # Join broken sentences
		}
		
		# Initialize stay-on-top state
		self.stay_on_top = False
		
		# Create main widget and layout
		main_widget = QWidget()
		self.setCentralWidget(main_widget)
		main_layout = QVBoxLayout(main_widget)
		
		# Create toolbar with stay-on-top toggle
		toolbar_layout = QHBoxLayout()
		self.stay_on_top_button = QPushButton("📌 Stay on Top: Off")
		self.stay_on_top_button.setCheckable(True)
		self.stay_on_top_button.clicked.connect(self.toggle_stay_on_top)
		self.stay_on_top_button.setStyleSheet("""
			QPushButton {
				background-color: #f0f0f0;
				border: 1px solid #ccc;
				border-radius: 4px;
				padding: 5px 10px;
				font-size: 12px;
			}
			QPushButton:checked {
				background-color: #0078d4;
				color: white;
				border-color: #0078d4;
			}
		""")
		toolbar_layout.addWidget(self.stay_on_top_button)
		toolbar_layout.addStretch()
		main_layout.addLayout(toolbar_layout)
		
		# Create content layout
		content_layout = QHBoxLayout()
		
		# Create left side (input) layout
		left_layout = QVBoxLayout()
		input_label = QLabel("Type your text here:")
		self.input_text = QTextEdit()
		self.input_text.setPlaceholderText("Start typing here...")
		left_layout.addWidget(input_label)
		left_layout.addWidget(self.input_text)
		
		# Create right side (output) layout
		right_layout = QVBoxLayout()
		output_label = QLabel("Corrected text:")
		self.output_text = QTextEdit()
		self.output_text.setReadOnly(True)
		right_layout.addWidget(output_label)
		right_layout.addWidget(self.output_text)
		
		# Add layouts to content layout
		content_layout.addLayout(left_layout)
		content_layout.addLayout(right_layout)
		
		# Add content layout to main layout
		main_layout.addLayout(content_layout)
		
		# Setup timer for continuous checking
		self.timer = QTimer()
		self.timer.setSingleShot(True)
		self.timer.timeout.connect(self.check_grammar)
		
		# Store previous text for comparison
		self.previous_text = ""
		
		# Connect text change to timer
		self.input_text.textChanged.connect(self.start_timer)
		
		# Apply styling
		# Add toggle_stay_on_top method
		def toggle_stay_on_top(self):
			"""Toggle the stay-on-top state of the window"""
			self.stay_on_top = not self.stay_on_top
			if self.stay_on_top:
				self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
				self.stay_on_top_button.setText("📌 Stay on Top: On")
			else:
				self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
				self.stay_on_top_button.setText("📌 Stay on Top: Off")
			self.show()  # Need to show the window again after changing flags
		
		self.setStyleSheet("""
			QMainWindow {
				background-color: #f5f5f5;
			}
			QTextEdit {
				background-color: white;
				border: 2px solid #666;
				border-radius: 4px;
				padding: 12px;
				font-size: 16px;
				color: #333;
				selection-background-color: #0078d4;
				selection-color: white;
				line-height: 1.6;
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
		""")
	
	def start_timer(self):
		"""Start timer with shorter delay for more responsive corrections"""
		self.timer.start(300)  # Reduced to 300ms for more immediate feedback
	
	def fix_text_structure(self, text):
		"""Comprehensive text structure fixes"""
		# Store cursor position
		cursor = self.input_text.textCursor()
		self.previous_cursor = cursor.position()
		
		# Basic cleanup
		text = text.strip()
		if not text:
			return text
		
		# Fix multiple spaces
		text = re.sub(r'\s+', ' ', text)
		
		# Apply punctuation rules
		for pattern, replacement in self.punctuation_rules.items():
			text = re.sub(pattern, replacement, text)
		
		# Ensure proper sentence capitalization
		sentences = text.split('. ')
		corrected_sentences = []
		for sentence in sentences:
			if sentence:
				# Capitalize first letter of each sentence
				sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
				corrected_sentences.append(sentence)
		
		text = '. '.join(corrected_sentences)
		
		# Ensure final punctuation
		if text and not text[-1] in '.!?':
			text += '.'
		
		return text

	def check_grammar(self):
		"""Enhanced grammar checking with continuous analysis"""
		try:
			input_text = self.input_text.toPlainText()
			if not input_text.strip():
				self.output_text.clear()
				return
			
			# Skip if text hasn't changed
			if input_text == self.previous_text:
				return
			
			# First apply structural fixes
			structured_text = self.fix_text_structure(input_text)
			
			# Apply grammar corrections with enhanced settings
			matches = self.tool.check(structured_text)
			
			# Sort matches by offset to process from end to beginning
			matches.sort(key=lambda x: x.offset, reverse=True)
			
			corrected_text = structured_text
			for match in matches:
				if match.replacements:
					# Apply the correction
					start = match.offset
					end = start + match.errorLength
					corrected_text = corrected_text[:start] + match.replacements[0] + corrected_text[end:]
			
			# Final structure cleanup
			final_text = self.fix_text_structure(corrected_text)
			
			# Store current text for comparison
			self.previous_text = input_text
			
			# Update output
			self.output_text.setPlainText(final_text)
			
		except Exception as e:
			self.output_text.setPlainText(f"Error checking grammar: {str(e)}")

def main():
	app = QApplication(sys.argv)
	window = GrammarCheckerApp()
	window.show()
	sys.exit(app.exec())

if __name__ == '__main__':
	main()
