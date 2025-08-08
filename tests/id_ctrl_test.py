from logger.log_manager import LogManager
from nvme.nvme_wrapper import NvmeCommands

DEVICE = "/dev/nvme0"
NVME = "nvme"
IGNORE_LIST = ['sn', 'fguid', 'unvmcap', 'subnqn']
EXPECTED_LOG = {
  "vid":606,
  "ssvid":606,
  "sn":"XXXXXXXXXXXXXXXXXXXXX",
  "mn":"SOLIDIGM SBFPF2BU153T                   ",
  "fr":"6CV10100",
  "rab":0,
  "ieee":13162167,
  "cmic":0,
  "mdts":5,
  "cntlid":0,
  "ver":66560,
  "rtd3r":10000000,
  "rtd3e":9000000,
  "oaes":768,
  "ctratt":640,
  "rrls":0,
  "cntrltype":1,
  "fguid":"00000000-0000-0000-0000-00000000000",
  "crdt1":0,
  "crdt2":0,
  "crdt3":0,
  "nvmsr":1,
  "vwci":0,
  "mec":3,
  "oacs":94,
  "acl":3,
  "aerl":3,
  "frmw":24,
  "lpa":62,
  "elpe":255,
  "npss":2,
  "avscc":0,
  "apsta":0,
  "wctemp":343,
  "cctemp":353,
  "mtfa":100,
  "hmpre":0,
  "hmmin":0,
  "tnvmcap":15362991415296,
  "unvmcap":0,
  "rpmbs":0,
  "edstt":30,
  "dsto":1,
  "fwug":1,
  "kas":0,
  "hctma":0,
  "mntmt":0,
  "mxtmt":0,
  "sanicap":1610612739,
  "hmminds":0,
  "hmmaxd":0,
  "nsetidmax":0,
  "endgidmax":0,
  "anatt":0,
  "anacap":0,
  "anagrpmax":0,
  "nanagrpid":0,
  "pels":80,
  "domainid":0,
  "megcap":0,
  "sqes":102,
  "cqes":68,
  "maxcmd":0,
  "nn":128,
  "oncs":94,
  "fuses":0,
  "fna":4,
  "vwc":6,
  "awun":0,
  "awupf":0,
  "icsvscc":0,
  "nwpc":0,
  "acwu":0,
  "ocfs":0,
  "sgls":0,
  "mnan":0,
  "maxdna":0,
  "maxcna":0,
  "oaqd":0,
  "subnqn":"nqn.2023-04.com.solidigm:XXXXXXXXXXXXXXXXXXXXX  ",
  "ioccsz":0,
  "iorcsz":0,
  "icdoff":0,
  "fcatt":0,
  "msdbd":0,
  "ofcs":0,
  "psds":[
    {
      "max_power":2500,
      "max_power_scale":0,
      "non-operational_state":0,
      "entry_lat":60000,
      "exit_lat":60000,
      "read_tput":0,
      "read_lat":0,
      "write_tput":0,
      "write_lat":0,
      "idle_power":506,
      "idle_scale":2,
      "active_power":2500,
      "active_power_work":2,
      "active_scale":2
    },
    {
      "max_power":1500,
      "max_power_scale":0,
      "non-operational_state":0,
      "entry_lat":60000,
      "exit_lat":60000,
      "read_tput":0,
      "read_lat":0,
      "write_tput":0,
      "write_lat":0,
      "idle_power":506,
      "idle_scale":2,
      "active_power":1500,
      "active_power_work":2,
      "active_scale":2
    },
    {
      "max_power":1000,
      "max_power_scale":0,
      "non-operational_state":0,
      "entry_lat":60000,
      "exit_lat":60000,
      "read_tput":0,
      "read_lat":0,
      "write_tput":0,
      "write_lat":0,
      "idle_power":506,
      "idle_scale":2,
      "active_power":1000,
      "active_power_work":2,
      "active_scale":2
    }
  ]
}

class TestIdCtrl():
  def __init__(self, logger, nvme):
    self.logger = logger
    self.nvme = nvme
        
  def run(self):
    found_log = self.nvme.id_ctrl(json_output=True)
    self.logger.debug("Using id_ctrl command...")
    if found_log != None:
      self.logger.debug("Command Succeeded")
    return found_log

  def validate(self, expected_log, found_log):
    count = 0
    if (len(expected_log) != len(found_log)):
      self.logger.debug("ERROR: Can't validate")
      return None
    keys = list(expected_log.keys())
    for i in range(4):
      keys.remove(IGNORE_LIST[i])
    for key in keys:
      if expected_log[key] != found_log[key]:
        count += 1
        self.logger.debug(f"Error: Expected {expected_log[key]}, Found {found_log[key]}")
    return count
    
      
test = LogManager("test_id_control")
logger = test.get_logger()
nvme = NvmeCommands(device = DEVICE, logger = logger)
id_ctrl_test = TestIdCtrl(logger,nvme)
found_log = id_ctrl_test.run()
if found_log == None:
  logger.error("ERROR in command")
else:
  errors = id_ctrl_test.validate(EXPECTED_LOG,found_log)
  if errors == 0:
    logger.info("TEST PASSED, 0 errors")
  else:
    logger.info(f"TEST FAILED, {errors} error(s)")     

