import logging
from datetime import datetime
import os

class LogManager:
    """
    LogManager sets up a logging system that outputs logs to a timestamped file
    and optionally to the console. It is designed to be initialized per test case.

    Attributes:
        testname (str): Name of the test case, used to name the log file.
        log_to_console (bool): Whether logs should also be printed to the console.
        log_dir (str): Directory where log files will be stored.
        log_level (int): Logging level (default is logging.INFO).
        logger (logging.Logger): Configured logger instance.
    """

    def __init__(self, testname, console=True, log_dir='logs'):
        """
        Initializes the LogManager.

        Args:
            console (bool): Whether to enable logging output to the console. Default is True.
            log_dir (str): Directory path to store the log files. Default is 'logs'.
        """

        self.log_to_console = console
        self.log_dir = log_dir
        self.log_level = logging.INFO
        self.testname = testname

        # Create the specified log directory if it does not already exist.
        os.makedirs(self.log_dir, exist_ok=True)

        # Create and configure the logger instance.
        self.logger = logging.getLogger(self.testname)
        self.logger.setLevel(self.log_level)

        # Setup file and console handlers.
        self._setupLogger()

    def _setupLogger(self):
        """
        Configures logging handlers for file and optional console output.
        - File logs are stored in a timestamped file named after the test.
        - Console logs are printed in a clean format (if enabled).
        """

        # Avoid adding duplicate handlers if already configured.
        if self.logger.handlers:
            return
        
        # Generate the timestamped filename using the test name.
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file_path = os.path.join(self.log_dir, f'{self.testname}_{timestamp}.log')

        # Define a common log format.
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # File handler to write logs to a file.
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Optional: Console handler for immediate feedback in the terminal.
        if self.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        """
        Returns the configured logger instance.

        Returns:
            logging.Logger: The logger configured with file and (optional) console handlers.
        """

        return self.logger
    def info(self, msg):
        self.logger.info(msg)
        
    def error(self,msg):
        self.logger.error(msg)
