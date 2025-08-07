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

        if self.initialize() is None:
            self.logger.error(f"Unable to get Physical Path for SN: {self.serial_number}")
            return
        
        if testname not in tests_pool:
            test_list = list(tests_pool.keys())
            self.logger.error(f"Test {testname} was not found. Tests Available: {test_list}")
            self.logger.error(f"Make sure the test you are trying to execute has been defined.")
            return
        self.test = tests_pool[self.testname](self.logger, self.nvme)

        def initialize(self):
        # Construir e inicializar wappers, etc..
        pass

        def run(self):
            # Logar un mensaje de inicio, correr la prueba y logar el final de la pureba
            pass

        def set_final_result(self):
            # Zona de validacion de resultados y log de resultados
            pass

        def drive_check(self, discovery=True):
            # Proceso de discovery del drive y sanidad del drive
            pass

        def get_device_path(self, serial_number, nvme_list):
            pass

#my_test = TestManager("PHA42142004Y1P2A", "test_read_write")
#if my_test.test is not None:
#    my_test.drive_check(discovery=True)
#    my_test.run()
#    my_test.set_final_result()
#    my_test.drive_check(discovery=False)
