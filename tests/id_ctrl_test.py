from logger.log_manager import LogManager
from nvme_wrapper import NvmeCommands

DEVICE = "/dev/nvme0"
NVME = "nvme"

class TestIdCtrl():
  def __init__(self, logger, nvme):
    self.logger = logger
    self.nvme = nvme
        
  def run(self):
    cmd = self.nvme.id_ctrl(json_output=True)
    self.logger.debug("Using id_ctrl command...")
    if cmd != None:
      self.logger.debug("Command Succeeded")
    return cmd

  def validate(self, json, cmd):
    count = 0
    if (len(json) != len(cmd)):
      self.logger.debug("ERROR: Can't validate")
      return None
    for key in json:
      if key == "sn" or key == "fguid" or key == "unvmcap" or key == "subnqn":
        pass
      if json[key] != cmd[key]:
        count++
        self.logger.debug(f"Error: Expected {json[key]}, Found {cmd[key]}")
      return count;
    
      
test = TestLogger("test_id_control")
logger = testLogger.initialize_logger()
nvme = NvmeCommands(logger, device = DEVICE, nvme_cli = NVME)
id_ctrl_test = TestIdCtrl(logger,nvme)
console = id_ctrl_test.run()
if console == None:
  logger.debug("ERROR in command")
  return 0
errors = id_ctrl_test.validate(json,cmd)
if errors == 0:
  logger.debug("TEST PASSED, 0 errors")
else:
  logger.debug(f"TEST FAILED, {errors} error(s)")
return 0  

        
