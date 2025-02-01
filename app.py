import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
							QTextEdit, QLabel, QHBoxLayout, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QClipboard
import language_tool_python
import re

class GrammarCheckerApp(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Real-time Grammar Checker")
		# Set a smaller minimum size
		self.setMinimumSize(400, 300)
		# Enable resizing
		self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
		self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
		
		# Initialize the language tool
		self.tool = language_tool_python.LanguageTool('en-US')
		
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
		main_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins for smaller window
		main_layout.setSpacing(5)  # Reduce spacing between elements
		
		# Create toolbar layout with both buttons
		toolbar_layout = QHBoxLayout()
		toolbar_layout.setSpacing(5)
		
		# Add stay-on-top toggle button
		self.stay_on_top_button = QPushButton("📌 Stay on Top: Off")
		self.stay_on_top_button.setCheckable(True)
		self.stay_on_top_button.clicked.connect(self.toggle_stay_on_top)
		self.stay_on_top_button.setStyleSheet("""
			QPushButton {
				background-color: #f0f0f0;
				border: 1px solid #ccc;
				border-radius: 4px;
				padding: 5px 10px;
				font-size: 11px;
			}
			QPushButton:checked {
				background-color: #0078d4;
				color: white;
				border-color: #0078d4;
			}
		""")
		
		# Add copy button
		self.copy_button = QPushButton("📋 Copy Corrected Text")
		self.copy_button.clicked.connect(self.copy_corrected_text)
		self.copy_button.setStyleSheet("""
			QPushButton {
				background-color: #0078d4;
				color: white;
				border: none;
				padding: 5px 10px;
				border-radius: 4px;
				font-size: 11px;
			}
			QPushButton:hover {
				background-color: #005a9e;
			}
			QPushButton:pressed {
				background-color: #004c87;
			}
		""")
		
		# Add buttons to toolbar layout
		toolbar_layout.addWidget(self.stay_on_top_button)
		toolbar_layout.addWidget(self.copy_button)
		toolbar_layout.addStretch()
		
		# Add toolbar to main layout
		main_layout.addLayout(toolbar_layout)
		
		# Create content layout
		content_layout = QHBoxLayout()
		content_layout.setSpacing(5)
		
		# Create left side (input) layout
		left_layout = QVBoxLayout()
		left_layout.setSpacing(2)
		input_label = QLabel("Type your text here:")
		self.input_text = QTextEdit()
		self.input_text.setPlaceholderText("Start typing here...")
		self.input_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
		left_layout.addWidget(input_label)
		left_layout.addWidget(self.input_text)
		
		# Create right side (output) layout
		right_layout = QVBoxLayout()
		right_layout.setSpacing(2)
		output_label = QLabel("Corrected text:")
		self.output_text = QTextEdit()
		self.output_text.setReadOnly(True)
		self.output_text.setPlaceholderText("Corrected text will appear here...")
		self.output_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
		right_layout.addWidget(output_label)
		right_layout.addWidget(self.output_text)
		
		# Add layouts to content layout with stretch factors
		content_layout.addLayout(left_layout, 1)
		content_layout.addLayout(right_layout, 1)
		
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
		
		# Set enhanced style with smaller fonts and padding for compact view
		self.setStyleSheet("""
			QMainWindow {
				background-color: #f0f0f0;
			}
			QTextEdit {
				background-color: white;
				border: 1px solid #666;
				border-radius: 3px;
				padding: 4px;
				font-size: 12px;
				color: #333;
				selection-background-color: #0078d4;
				selection-color: white;
			}
			QTextEdit:focus {
				border-color: #0078d4;
			}
			QLabel {
				font-size: 11px;
				font-weight: bold;
				color: #333;
				margin-bottom: 2px;
			}
			QTextEdit[readOnly="true"] {
				background-color: #f8f8f8;
				border-color: #999;
			}
		""")
	
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

	def copy_corrected_text(self):
		"""Copy the corrected text to clipboard"""
		corrected_text = self.output_text.toPlainText()
		if corrected_text:
			clipboard = QApplication.clipboard()
			clipboard.setText(corrected_text)
			
			# Temporarily change button text to show feedback
			original_text = self.copy_button.text()
			self.copy_button.setText("✓ Copied!")
			QTimer.singleShot(1500, lambda: self.copy_button.setText(original_text))


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
