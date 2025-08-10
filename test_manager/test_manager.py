import json
import sys

from logger.log_manager import TestLogger
from nvme.nvme_wrapper import NvmeCommands

#Aqui se importan los test cases
from tests.id_ctrl_test import TestIdCtrl
from tests.id_ns_test import TestIdNS
from tests.smart_log_test import TestSmartLog

#from unit_tests.test_read_write import TestReadWrite
#from unit_tests.dummy_test import DummyTest

#Define set of available tests
tests_pool = {"test_id_ctrl": TestIdCtrl,
              "test_id_ns": TestIdNS,
              "test_smart_log": TestSmartLog
              }

class TestManager(object):
    def __init__(self, serial_number, testname):
        self.serial_number = serial_number
        self.testname = testname
        self.nvme = None
        self.physical_path = None
        self.logger = TestLogger(self.testname).initialize_logger()
        self.test = None

        '''if self.initialize() is None:
            self.logger.error(f"Unable to get Physical Path for SN: {self.serial_number}")
            return
        
        if testname not in tests_pool:
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
                    return device.get("DevicePath")
        return None

    def initialize(self):
        # Construir e inicializar wappers, etc..
        self.nvme = NvmeCommands(self.logger, nvme_cli="nvme")
        self.physical_path = self.get_device_path()
        if not self.physical_path:
            self.logger.error(f"Device with SN {self.serial_number} not found.")
            raise Exception("Device path not found.")
        self.nvme.device = self.physical_path
        
        if self.testname not in tests_pool:
            test_list = list(tests_pool.keys())
            self.logger.error(f"Unknown test name: {self.testname}")
            self.logger.info(f"Tests Available: {test_list}")
            self.logger.warning(f"Make sure the test you are trying to execute has been defined.")
            return
        
        self.test = tests_pool[self.testname](self.logger, self.nvme)
        '''if self.testname == "id_ctrl":
            self.test = TestIdCtrl(self.logger, self.nvme)
        elif self.testname == "id_ns":
            self.test = TestIdNS(self.logger, self.nvme)
        elif self.testname == "smart_log":
            self.test = TestSmartLog(self.logger, self.nvme)
        else:
            self.logger.error(f"Unknown test name: {self.testname}")
            raise Exception("Invalid test name")'''

    def drive_check(self, discovery=True):
        # Proceso de discovery del drive y sanidad del drive
        if discovery:
            stage = "Pre-Check"
        else:
            stage = "Post-Check"
        
        self.logger.debug(f"[====== Start {stage} Drive Status ======]")
        output = self.nvme.id_ctrl(json_output=True)
        if not output:
            self.logger.error("Failed to retrieve controller info.")
            raise Exception("Drive check failed.")
        sn = output.get("sn", "Unknown")
        mn = output.get("mn", "Unknown")
        fw = output.get("fr", "Unknown")
        health = output.get("ctrlr_health", {}).get("health_status", "Unknown")

        if not discovery and health.lower() != "healthy":
            self.logger.error("Drive is not healthy. Aborting test.")
            raise Exception("Drive health check failed.")

        self.logger.info(f"SN: {sn}, Model: {mn}, FW: {fw}, Health: {health}")
        self.logger.debug(f"[====== End {stage} Drive Status ======]")

        #if not discovery and health.lower() != "healthy":
        #    self.logger.error("Drive is not healthy. Aborting test.")
        #    raise Exception("Drive health check failed.")

    def run(self):
        # Logar un mensaje de inicio, correr la prueba y logar el final de la pureba
        if self.test:
            self.logger.debug(f"[====== Start Test: {self.testname} ======]")
            self.test.run()
            self.logger.debug(f"[====== End test:   {self.testname} ======]")
        else:
            self.logger.error("No test defined.")

    def set_final_result(self):
        # Zona de validacion de resultados y log de resultados
        self.logger.debug(f"================================")
        if all(self.test.final_result):
            self.logger.debug(f"[====== TEST PASSED ======]")
        else:
            self.logger.debug(f"[====== TEST FAILED ======]")
        self.logger.debug(f"================================")

#my_test = TestManager("PHA42142004Y1P2A", "test_read_write")
#if my_test.test is not None:
# CREO QUE FALTARIA AQUI EL initialize()
#    my_test.drive_check(discovery=True)
#    my_test.run()
#    my_test.set_final_result()
#    my_test.drive_check(discovery=False)

