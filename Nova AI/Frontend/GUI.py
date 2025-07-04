from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QStackedWidget, 
                           QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QFrame, QLabel, QSizePolicy, QDesktopWidget)
from PyQt5.QtGui import (QIcon, QMovie, QColor, QTextCharFormat, QFont, 
                        QPixmap, QTextBlockFormat, QPainter)
from PyQt5.QtCore import Qt, QSize, QTimer, QPoint
from dotenv import dotenv_values
import sys
import os

# Environment and Path Setup
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname")
current_dir = os.getcwd()
old_chat_message = ""
TemplipPath = rf"{current_dir}\Frontend\Files"
GraphicGUI_Path = rf"{current_dir}\Frontend\Graphics"

# Utility Functions
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ['how', 'what', 'who', 'where', 'when', 'why', 'which', 
                     'whose', 'whom', 'can you', "what's", "where's", "how's"]

    if any(word in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with open(rf"{TemplipPath}\Mic.data", "w", encoding='utf-8') as file:
        file.write(Command)

def GetMicrophoneStatus():
    with open(rf"{TemplipPath}\Mic.data", "r", encoding='utf-8') as file:
        return file.read()

def SetAssistantStatus(Status):
    with open(rf"{TemplipPath}\Status.data", "w", encoding='utf-8') as file:
        file.write(Status)

def GetAssistantStatus():
    with open(rf"{TemplipPath}\Status.data", "r", encoding='utf-8') as file:
        return file.read()

def MiButtonInitlabel():
    SetMicrophoneStatus("False")

def MiButtonClosed():
    SetMicrophoneStatus("True")

def GraphicsDirectoryPath(filename):
    return rf"{GraphicGUI_Path}\{filename}"

def TempDirectoryPath(filename):
    return rf"{TemplipPath}\{filename}"

def ShowTextToScreen(text):
    with open(rf"{TemplipPath}\Responses.data", "w", encoding='utf-8') as file:
        file.write(text)

# Chat Section Class
class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 100)
        layout.setSpacing(-100)
        
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.chat_text_edit)
        
        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                background: black;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::sub-line:vertical {
                background: black;
                subcontrol-position: top;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        self.setStyleSheet("background-color: black;")
        layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
        layout.setStretch(1, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        
        text_color = QColor(Qt.blue)
        text_format = QTextCharFormat()
        text_format.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_format)
        
        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie = QMovie(GraphicsDirectoryPath('jarvis.gif'))
        max_gif_size_W = 480
        max_gif_size_H = 270
        movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)
        
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size:16px; margin-right: 195px; border: none; margin-top: -30px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)
        layout.setSpacing(-10)
        
        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)
        self.chat_text_edit.viewport().installEventFilter(self)
        
        self.toggled = False

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        format = QTextBlockFormat()
        format.setTopMargin(10)
        format.setLeftMargin(10)
        char_format = QTextCharFormat()
        char_format.setForeground(QColor(color))
        cursor.setCharFormat(char_format)
        cursor.setBlockFormat(format)
        cursor.insertText(message + "\n")
        self.chat_text_edit.setTextCursor(cursor)

    def loadMessages(self):
        global old_chat_message
        with open(TempDirectoryPath('Responses.data'), 'r', encoding='utf-8') as file:
            messages = file.read()

        if messages is None:
            pass
        elif len(messages) <= 1:
            pass
        elif str(old_chat_message) == str(messages):
            pass
        else:
            self.addMessage(message=messages, color='White')
            old_chat_message = messages

    def SpeechRecogText(self):
        with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
            messages = file.read()
        self.label.setText(messages)

    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 60, 60)
            MiButtonInitlabel()
        else:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 60, 60)
            MiButtonClosed()
        self.toggled = not self.toggled

class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize mic state FIRST
        self.mic_active = False  # <-- THIS FIXES THE ATTRIBUTE ERROR
        
        # Transparent window settings
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        
        # Main layout with transparent margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Fully transparent edges
        
        # Central container with shadow effect
        center_container = QWidget()
        center_container.setStyleSheet("""
            background-color: rgba(0, 0, 0, 200);
            border-radius: 15px;
        """)
        
        center_layout = QVBoxLayout(center_container)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setContentsMargins(30, 30, 30, 30)  # Inner padding
        
        # GIF Display
        self.gif_label = QLabel()
        movie = QMovie(GraphicsDirectoryPath('jarvis.gif'))
        movie.setScaledSize(QSize(700, 700))  # Slightly smaller for padding
        self.gif_label.setMovie(movie)
        movie.start()
        
        # Status Label
        self.status_label = QLabel("No speech detected")
        self.status_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            background: transparent;
        """)
        
        # Mic Button (now properly initialized)
        self.mic_button = QPushButton()
        self.mic_button.setIcon(QIcon(GraphicsDirectoryPath('Mic_off.png')))
        self.mic_button.setIconSize(QSize(50, 50))
        self.mic_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 30);
                border-radius: 25px;
            }
        """)
        self.mic_button.clicked.connect(self.toggle_mic)
        
        # Add widgets
        center_layout.addWidget(self.gif_label)
        center_layout.addWidget(self.status_label)
        center_layout.addWidget(self.mic_button, 0, Qt.AlignCenter)
        
        main_layout.addWidget(center_container)

    def toggle_mic(self):
        """Working mic toggle with state tracking"""
        self.mic_active = not self.mic_active
        
        # Update icon
        icon = 'Mic_on.png' if self.mic_active else 'Mic_off.png'
        self.mic_button.setIcon(QIcon(GraphicsDirectoryPath(icon)))
        
        # Update system
        SetMicrophoneStatus("True" if self.mic_active else "False")
        self.status_label.setText("Listening..." if self.mic_active else "No speech detected")

class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        layout = QVBoxLayout()
        label = QLabel("")
        layout.addWidget(label)
        
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

# Custom Top Bar
class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.initUI()
        self.current_screen = None
        self.draggable = True
        self.offset = None
        
    def initUI(self):
        self.setFixedHeight(56)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        
        # Home Button
        home_button = QPushButton()
        home_icon = QIcon(GraphicsDirectoryPath("Home.png"))
        home_button.setIcon(home_icon)
        home_button.setText(" Home")
        home_button.setStyleSheet("height:40px; line-height:40px; background-color:white; color: black")
        home_button.clicked.connect(lambda: self.showInitialScreen())
        
        # Message Button
        message_button = QPushButton()
        message_icon = QIcon(GraphicsDirectoryPath("Chats.png"))
        message_button.setIcon(message_icon)
        message_button.setText(" Chat")
        message_button.setStyleSheet("height:40px; line-height:40px; background-color:white; color: black")
        message_button.clicked.connect(lambda: self.showMessageScreen())
        
        # Minimize Button
        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicsDirectoryPath("Minimize.png"))
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("background-color:white")
        minimize_button.clicked.connect(self.minimizeWindow)
        
        # Maximize Button
        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath("Maximize.png"))
        self.restore_icon = QIcon(GraphicsDirectoryPath("Minimize2.png"))
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color:white")
        self.maximize_button.clicked.connect(self.maximizeWindow)
        
        # Close Button
        close_button = QPushButton()
        close_icon = QIcon(GraphicsDirectoryPath("Close.png"))
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("background-color:white")
        close_button.clicked.connect(self.closeWindow)
        
        # Line Frame
        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: black;")
        
        # Title Label
        title_label = QLabel(f"{str(Assistantname).capitalize()} AI")
        title_label.setStyleSheet("color: black; font-size: 180%; background-color: white")
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        layout.addWidget(line_frame)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)
    
    def minimizeWindow(self):
        self.parent().showMinimized()
    
    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)
    
    def closeWindow(self):
        self.parent().close()
    
    def mousePressEvent(self, event):
        if self.draggable and event.button() == Qt.LeftButton:
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.draggable and self.offset and event.buttons() & Qt.LeftButton:
            self.parent().move(event.globalPos() - self.offset)
    
    def showMessageScreen(self):
        self.stacked_widget.setCurrentIndex(1)
    
    def showInitialScreen(self):
        self.stacked_widget.setCurrentIndex(0)

# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()
    
    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        
        # Create stacked widget
        self.stacked_widget = QStackedWidget()
        
        # Create screens
        self.initial_screen = InitialScreen()
        self.message_screen = MessageScreen()
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.initial_screen)
        self.stacked_widget.addWidget(self.message_screen)
        
        # Create top bar
        self.top_bar = CustomTopBar(self, self.stacked_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_bar)
        main_layout.addWidget(self.stacked_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Window size
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")

def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()