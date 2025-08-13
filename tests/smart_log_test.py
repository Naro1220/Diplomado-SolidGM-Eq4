import re
from logger.log_manager import LogManager
from nvme.nvme_wrapper import NvmeCommands
from nvme.admin_passthru_wrapper import AdminCommands

## Data of our NVME controller
DEVICE = "/dev/nvme0"
NVME = "nvme"
MEDIA_ERRORS_TRESHOLDS = 0
POWER_ON_HOURS_TRESHOLDS = 1000
PERCENTAGE_USAGE_TRESHOLDS = 100
N = 140
FID = "0x4"
FID_INT = 0x4
TMP_INIT = 0x155
MESSAGE = '/root/repos/Diplomado-SolidGM-Eq4/tests/TEXT.txt'
##Class to test the smart_log command of the NVME controller
class TestSmartLog():
  ## Gives our logger and the functions of NVME to the class
    def __init__(self, logger, nvme, admin):
        self.admin = admin
        self.logger = logger
        self.nvme = nvme
        self.errors = 0
    def run(self):

        ## Send the command samrt_log in format json to the controller and save the dictionary
        found_log = self.admin.smart_log()
        self.logger.info("Using smart_log command...")
        
        ## Informs about media errors
        if found_log["mdie"] == 0:
            self.logger.info("There no exist media errors in the NVME controller")
        else:
            self.logger.error("There are media errors in the NVME controller")
            self.errors += 1

        ## Informs about power on hours
        if found_log["poh"] < POWER_ON_HOURS_TRESHOLDS:
            self.logger.info("Power on hours are below the threshold")
        else:
            self.logger.error("Power on hours are above the threshold")
            self.errors += 1

        ## Informs about temperature 
        initial_temperature = self.extract_temp(self.nvme.get_feature(fid = FID))
        self.logger.info(f"The device temperature is {initial_temperature} K")
        
        ## Informs about percentage usage
        if found_log["pused"] < PERCENTAGE_USAGE_TRESHOLDS:
            self.logger.info("Percentage usage is below the threshold")
        else:
            self.logger.error("Percentage usage is above the threshold")
            self.errors += 1
        
        ## Initial value of host read commands 
        host_read_commands_init = found_log["hrc"]
        ## Initial value of host write commands 
        host_write_commands_init = found_log["hwc"]
        ## Initial value of critical warning
        critical_warning_init = found_log["cw"]

        for i in range(N):
            self.nvme.write(nsid=1, start_block=0, block_count=0, data_size=512, input_file=MESSAGE)
            self.nvme.read(nsid=1, start_block=0, block_count=0, data_size=512)

        ## Change temperature threshold and critical warning ------MISSING------
        self.admin.set_feature(fid=FID_INT,value=0x55)

        ## Take final snapshot of the smart log command using admin-passthru
        found_log = self.admin.smart_log()
        self.logger.info("Using smart_log command after operations...")

        ## Verify that the host_read_commands field has incremented N times in the final snapshot
        self.errors += self.validate(found_log,host_read_commands_init,host_write_commands_init,critical_warning_init, N)

        ## Check if any errors were logged
        if self.errors == 0:
            self.logger.info("PASSED: No errors found in smart_log test")
        else:
            self.logger.error(f"FAILED: {self.errors} errors found in smart_log test")
            
        self.admin.set_feature(fid=FID_INT,value=TMP_INIT)
        return self.errors
    
    def extract_temp(self, text):
        
        # Busca cualquier número seguido de "K" y extrae solo el número
        coincidencia = re.search(r'\b(\d+(?:\.\d+)?)\s*K\b', text)
        if coincidencia:
            return coincidencia.group(1)  # Devuelve solo el número como string, ej. "343"
        return None
    
    def validate(self,found_log,hrc,hwc,cw,n):
        
        errors = 0
        if found_log["hrc"] == hrc + n:
            self.logger.info(f"Host read commands have incremented: {n} times")
        else:
            self.logger.error("Host read commands did not increment as expected")
            errors += 1
        
        ## Verify that the host_write_commands field has incremented N times in the final snapshot
        if found_log["hwc"] == hwc + n:
            self.logger.info(f"Host write commands have incremented: {n} times")
        else:
            self.logger.error("Host write commands did not increment as expected")
            errors += 1    
        
        ## validate that the critical warning has changed
        if found_log["cw"] != cw:
            self.logger.info("Critical warning has changed as expected")
        else:
            self.logger.error("Critical warning did not change as expected")
            errors += 1
            
        return errors
