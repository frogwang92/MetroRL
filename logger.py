import logging
from pathlib import Path

class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit=None):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        if self.text_edit:
            self.text_edit.appendPlainText(msg)

def setup_logger(name: str, log_file: str = None, level=logging.INFO, text_edit=None):
    """Set up logger with consistent formatting"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log file specified
    if log_file:
        log_path = Path('logs')
        log_path.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_path / log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # QTextEdit handler for GUI
    if text_edit:
        gui_handler = QTextEditLogger(text_edit)
        gui_handler.setFormatter(formatter)
        logger.addHandler(gui_handler)
        
    return logger

def add_logger_to_gui(logger, text_edit):
    """Add logger to GUI"""
    gui_handler = QTextEditLogger(text_edit)
    logger.addHandler(gui_handler)

logger = setup_logger('main', 'simulation.log')