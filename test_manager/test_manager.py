import json
import sys
import re

from nvme.nvme_wrapper import NvmeCommands
from logger.log_manager import LogManager
from nvme.admin_passthru_wrapper import AdminCommands

#Test Case imports
from tests.id_ctrl_test import TestIdCtrl
from tests.id_ns_test import TestIdNs
from tests.smart_log_test import TestSmartLog

#Define set of available tests
tests_pool = {"test_id_ctrl": TestIdCtrl,
              "test_id_ns": TestIdNs,
              "test_smart_log": TestSmartLog
              }

class TestManager(object):
    '''TestManagegr coordinates the execution of NVMe test cases
    Atributes:
            serial number (str): SSD's serial number provided by user
            testname (str): Name of the test case (In tests pool)
            nvme (obj): Instance of the NVMeCommands Class
            physical path (str): Controller device path
            logger (obj): Instance of the LogManager Class
            admin (obj): Instance of the AdminCommands Class
            test (obj): Instance of the corresponding Test Case Class'''
    
    def __init__(self, serial_number, testname):
        '''Initializes the Test Manager and prepares the environment
        Args:
            serial_number (str): SSD's serial number to target
            testname (str): Name of the test case
        '''
        
        self.serial_number = serial_number
        self.testname = testname
        self.nvme = None
        self.physical_path = None
        self.logger = LogManager(self.testname).get_logger()
        self.admin = None
        self.test = None

        #If initialization fails (invalid SN or test name), the object may not be ready to run tests.
        if self.initialize() is None:
            self.logger.error(f"Unable to initialize")
            return None

    def get_device_path(self):
        '''Retrieve the NVMe device's controller path without namespace suffix.
        Uses nvme list in JSON format to match the device's serial number.'''

        output = self.nvme.list(json_output=True)
        if output:
            for device in output.get("Devices", []):
                if device.get("SerialNumber") == self.serial_number:
                    full_path = device.get("DevicePath")
                    if full_path:
                        #Regular Expression: Remove the namespace suffix
                        return re.sub(r"n\d+$", "", full_path)
        return None

    def initialize(self):
        '''Define and initialize wrappers, etc...
        -Create NVme Commands instance with no device
        -Retrieve and set the physical path of the device
        -Validate that the test name exist in tests_pool
        -Create an AdminCommands instance
        -Initialize the test case with logger, NVMe, and Admin instances'''

        #Create NVMe wrapper without device (will be assigned after physical path)
        self.nvme = NvmeCommands(self.physical_path, self.logger)

        #Get physical path of the ssd
        self.physical_path = self.get_device_path()
        if not self.physical_path:
            self.logger.error(f"Device with SN {self.serial_number} not found.")
            return None

        #Update device with discovered device path
        self.nvme.device = self.physical_path

        #Validate that testcase name exists
        if self.testname not in tests_pool:
            test_list = list(tests_pool.keys())
            self.logger.error(f"Unknown test name: {self.testname}")
            self.logger.info(f"Tests Available: {test_list}")
            self.logger.info(f"Make sure the test you are trying to execute has been defined.")
            return None
        
        #Initialize the instance of AddminCommands Class
        self.admin = AdminCommands(self.physical_path,self.logger)
        #Update test case and initialize it with instances of logger, nvme and admin classes
        self.test = tests_pool[self.testname](self.logger, self.nvme, self.admin)
        return self.test

    def drive_check(self, discovery):
        '''Performs a health check of the NVME drive
        Executes nvme id-ctrl with vendor option
        Args:
            discovery(bool): True - Pre-Check  /  False - Post-Check'''
        if discovery:
            stage = "Pre-Check"
            if self.physical_path is None:
                self.logger.error("Device not found. It is not possible to make a drive Pre check")
                return
        else:
            stage = "Post-Check"
            if self.physical_path is None:
                self.logger.error("Device not found. It is not possible to make a drive Post check")
                return

        self.logger.info(f"[====== Start {stage} Drive Status ======]")
        #Execute id ctrl command with vendor parameter (solidigm)
        output = self.nvme.id_ctrl(json_output=True, vendor=True)
        if not output:
            self.logger.error("Failed to retrieve controller info.")
            return
        sn = output.get("sn", "Unknown")
        mn = output.get("mn", "Unknown")
        fw = output.get("fr", "Unknown")
        health = output.get("health", "Unknown")
        #Cleaning the health field
        health = health.replace("\x00", "")

        if health.lower().strip() == "healthy":
            self.logger.info(f"SN: {sn}, FW: {fw}, Health: {health}, Model: {mn}")
            self.logger.info(f"[====== End {stage} Drive Status ======]")
        else:
            if discovery:
                self.logger.error("Drive health unknown during Pre-Check.")
                self.logger.error("Drive is not healthy. Aborting test.")
                return
            else:
                self.logger.error("Drive health unknown during Post-Check.")
                self.logger.error("Drive is not healthy. Aborting test.")
                return
        
    def run(self):
        #Show a start message, run the selected test and show a end test message
        if self.test:
            self.logger.info(f"[====== Start Test: {self.testname} ======]")
            self.test.run()
            self.logger.info(f"[====== End test:   {self.testname} ======]")
            return True
        else:
            self.logger.error("No test defined.")
            return None

    def set_final_result(self):
        '''Log the Final test result based on the test's error count'''
        self.logger.info(f"================================")
        if (self.test.errors == 0):
            self.logger.info(f"[====== TEST PASSED ======]")
        else:
            self.logger.info(f"[====== TEST FAILED ======]")
        self.logger.info(f"================================")

