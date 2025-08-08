from logger.log_manager import LogManager
from nvme.nvme_wrapper import NvmeCommands

## Datos de nuestro NVME controller
DEVICE = "/dev/nvme0"
NVME = "nvme"

## Datos del resultado del comando id-ctrl que debemos ignorar
IGNORE_LIST = ['sn', 'fguid', 'unvmcap', 'subnqn']

##Resultado de otro NVME controller para comparar
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

## Clase para hacer la prueba
class TestIdCtrl():

  ## Da nuestro logger y las funciones de NVME a la clase
  def __init__(self, logger, nvme):
    self.logger = logger
    self.nvme = nvme
        
  def run(self):

    ## Manda el comando id-ctrl en formato json al controlador y guarda el diccionario
    found_log = self.nvme.id_ctrl(json_output=True)
    self.logger.info("Using id_ctrl command...")

    ## Informa si el comando se ejecuto correctamente
    if found_log != None:
      self.logger.info("Command Succeeded")
    return found_log

  def validate(self, expected_log, found_log):

    ## Inicia una cuenta en 0 para los errores y comprueba si los 2 diccionarios son del mismo tamaño
    count = 0
    if (len(expected_log) != len(found_log)):
      return -1
    
    ## Consigue las claves de los diccionarios, los guarda en una lista y elimina las claves que ignoraremos
    keys = list(expected_log.keys())
    for i in range(4):
      keys.remove(IGNORE_LIST[i])

    ## Se mueve de clave en clave, comprueba si los valores son iguales y en dado caso de que no sea asi, lo remarca y lo madnda la cantidad de errores
    for key in keys:
      if expected_log[key] != found_log[key]:
        count += 1
        self.logger.errr(f"Error: Expected {expected_log[key]}, Found {found_log[key]}")
    return count
    
## Inicia el logger y las funciones en un objeto      
test = LogManager("test_id_control")
logger = test.get_logger()
nvme = NvmeCommands(device = DEVICE, logger = logger)

## Crea un objeto con las funciones de esta prueba, y lo corre
id_ctrl_test = TestIdCtrl(logger,nvme)
found_log = id_ctrl_test.run()

## Checa si hubo algun error al ejecutar el comando
if found_log == None:
  logger.error("ERROR in command")

## Compara ambos diccionarios, ve si hubo errores al comparar, o si hubo errores por diferencia de datos
else:
  errors = id_ctrl_test.validate(EXPECTED_LOG,found_log)
  if errors == 0:
    logger.info("TEST PASSED, 0 errors")
  elif errors > 0:
    logger.info(f"TEST FAILED, {errors} error(s)")
  else:
    logger.error("ERROR: Can't validate")

