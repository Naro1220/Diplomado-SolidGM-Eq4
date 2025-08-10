import json
import sys
import re

from nvme_wrapper import NvmeCommands
from log_manager import LogManager

#Aqui se importan los test cases
from id_ctrl_test import TestIdCtrl

#AGREGAR ESTOS CUANDO ESTEN LISTOS LOS TESTCASES
'''from tests.id_ns_test import TestIdNS
from tests.smart_log_test import TestSmartLog'''

#from unit_tests.test_read_write import TestReadWrite
#from unit_tests.dummy_test import DummyTest

#Define set of available tests
tests_pool = {"test_id_ctrl": TestIdCtrl
              #"test_id_ns": TestIdNS
              #"test_smart_log": TestSmartLog
              }

class TestManager(object):
    def __init__(self, serial_number, testname):
        self.serial_number = serial_number
        self.testname = testname
        self.nvme = None
        self.physical_path = None
        self.logger = LogManager(self.testname).get_logger()
        self.test = None

        if self.initialize() is None:
            self.logger.error(f"Unable to get Physical Path for SN: {self.serial_number}")
            return
        
        '''if testname not in tests_pool:
            test_list = list(tests_pool.keys())
            self.logger.error(f"Test {testname} was not found. Tests Available: {test_list}")
            self.logger.error(f"Make sure the test you are trying to execute has been defined.")
            return
        self.test = tests_pool[self.testname](self.logger, self.nvme)'''

    def get_device_path(self):
        output = self.nvme.list(json_output=True)
        if output:
            for device in output.get("Devices", []):
                if device.get("SerialNumber") == self.serial_number:
                    full_path = device.get("DevicePath")
                    if full_path:
                        #Quitar el namespace
                        return re.sub(r"n\d+$", "", full_path)
        return None

    def initialize(self):
        # Construir e inicializar wappers, etc..
        #Se inicializa el wrapepr de forma temporal
        self.nvme = NvmeCommands("/dev/nvme0", self.logger)

        self.physical_path = self.get_device_path()
        if not self.physical_path:
            self.logger.error(f"Device with SN {self.serial_number} not found.")
            return None
        self.nvme.device = self.physical_path

        
        if self.testname not in tests_pool:
            test_list = list(tests_pool.keys())
            self.logger.error(f"Unknown test name: {self.testname}")
            self.logger.info(f"Tests Available: {test_list}")
            self.logger.info(f"Make sure the test you are trying to execute has been defined.")
            return None
        
        self.test = tests_pool[self.testname](self.logger, self.nvme)
        return self.test

    def drive_check(self, discovery):
        # Proceso de discovery del drive y sanidad del drive
        if discovery:
            stage = "Pre-Check"
        else:
            stage = "Post-Check"
        
        self.logger.info(f"[====== Start {stage} Drive Status ======]")
        output = self.nvme.id_ctrl(json_output=True, vendor=True)
        if not output:
            self.logger.error("Failed to retrieve controller info.")
        sn = output.get("sn", "Unknown")
        mn = output.get("mn", "Unknown")
        fw = output.get("fr", "Unknown")
        health = output.get("health", "Unknown")
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
        # Logar un mensaje de inicio, correr la prueba y logar el final de la pureba
        if self.test:
            self.logger.info(f"[====== Start Test: {self.testname} ======]")
            self.test.run()
            self.logger.info(f"[====== End test:   {self.testname} ======]")
        else:
            self.logger.error("No test defined.")

    def set_final_result(self):
        # Zona de validacion de resultados y log de resultados
        self.logger.info(f"================================")
        if (self.test.errors == 0):
            self.logger.info(f"[====== TEST PASSED ======]")
        else:
            self.logger.info(f"[====== TEST FAILED ======]")
        self.logger.info(f"================================")

#PRUEBAS
my_test = TestManager("PHA4314100BJ15PDGN", "test_id_ctrl")
if my_test is not None:
    my_test.drive_check(discovery=True)
    my_test.run()
    my_test.set_final_result()
    my_test.drive_check(discovery=False)

