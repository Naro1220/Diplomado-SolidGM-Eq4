from logger.log_manager import LogManager
from nvme.nvme_wrapper import NvmeCommands
from nvme.admin_passthru_wrapper import AdminCommands

## Data of our NVME controller
DEVICE = "/dev/nvme0"
NVME = "nvme"
MEDIA_ERRORS_TRESHOLDS = 0
POWER_ON_HOURS_TRESHOLDS = 1000
PERCENTAGE_USAGE_TRESHOLDS = 100
N = 151
##Class to test the smart_log command of the NVME controller
class test_smart_log():
  ## Gives our logger and the functions of NVME to the class
  def __init__(self, admin, logger, nvme):
    self.admin = admin
    self.logger = logger
    self.nvme = nvme
  
  def run(self):

    ## Send the command samrt_log in format json to the controller and save the dictionary
    found_log = self.admin.smart_log(json_output=True)
    self.logger.debug("Using smart_log command...")

    errors = 0
    ## Informs about media errors
    if found_log["media_errors"] == 0:
      self.logger.info("There no exist media errors in the NVME controller")
    else:
      self.logger.error("There are media errors in the NVME controller")
      errors += 1

    ## Informs about power on hours
    if found_log["power_on_hours"] < POWER_ON_HOURS_TRESHOLDS:
      self.logger.info("Power on hours are below the threshold")
    else:
      self.logger.error("Power on hours are above the threshold")
      errors += 1

    ## Informs about temperature 
    temperature_device = found_log["temperature"] 
    self.logger.info(f"The device temperature is {temperature_device}k")
    
    ## Informs about percentage usage
    if found_log["percentage_usage"] < PERCENTAGE_USAGE_TRESHOLDS:
      self.logger.info("Percentage usage is below the threshold")
    else:
      self.logger.error("Percentage usage is above the threshold")
      errors += 1
    
    ## Initial value of host read commands 
    host_read_commands_init = found_log['host_read_commands']
    ## Initial value of host write commands 
    host_write_commands_init = found_log['host_write_commands']
    ## Initial value of critical warning
    critical_warning_init = found_log['critical_warning']

    for i in range(N):
      self.nvme.write(nsid=1, start_block=0, block_count=0, data_size=512, input_file=i)
      self.nvme.read(nsid=1, start_block=0, block_count=0, data_size=512)

    ## Change temperature threshold and critical warning ------MISSING------
    

    ## Take final snapshot of the smart log command using admin-passthru
    found_log = self.admin.smart_log(json_output=True)
    self.logger.debug("Using smart_log command after operations...")

    ## Verify that the host_read_commands field has incremented N times in the final snapshot
    if found_log['host_read_commands'] == host_read_commands_init + N:
      self.logger.info(f"Host read commands have incremented: {N} times")
    else:
      self.logger.error("Host read commands did not increment as expected")
      errors += 1
    
    ## Verify that the host_write_commands field has incremented N times in the final snapshot
    if found_log['host_write_commands'] == host_write_commands_init + N:
      self.logger.info(f"Host write commands have incremented: {N} times")
    else:
      self.logger.error("Host write commands did not increment as expected")
      errors += 1    
    
    ## validate that the critical warning has changed
    if found_log['critical_warning'] != critical_warning_init:
      self.logger.info("Critical warning has changed as expected")
    else:
      self.logger.error("Critical warning did not change as expected")
      errors += 1

    ## Check if any errors were logged
    if errors == 0:
      self.logger.info("PASSED: No errors found in smart_log test")
    else:
      self.logger.error(f"FAILED: {errors} errors found in smart_log test")
    return errors
