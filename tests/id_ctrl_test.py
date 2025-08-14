import json
from logger.log_manager import LogManager
from nvme.nvme_wrapper import NvmeCommands

## NVME controller data
DEVICE = "/dev/nvme0"
NVME = "nvme"

#Results of id-ctrl command to ignore 
IGNORE_LIST = ['sn', 'fguid', 'unvmcap', 'subnqn']

class TestIdCtrl():

  ## Da nuestro logger y las funciones de NVME a la clase
  def __init__(self, logger, nvme, admin, log_path="tests/expected_log.json"):
    self.logger = logger
    self.nvme = nvme
    self.admin = admin
    self.errors = 0 #Error count
    self.expected_log = None

    #Get the expected json file 
    try:
      with open(log_path, 'r') as archivo_json:
        self.expected_log = json.load(archivo_json)
      self.logger.debug(f"Expected log loaded from {log_path}")
    except FileNotFoundError:
      self.logger.error(f"Expected log file not found: {log_path}")
    except json.JSONDecodeError as e:
      self.logger.error(f"Error decoding JSON from {log_path}: {e}")


  def run(self):

    if self.expected_log is None:
      self.logger.error("No expected log loaded. Cannot run validation.")
      return False

    ## Manda el comando id-ctrl en formato json al controlador y guarda el diccionario
    found_log = self.nvme.id_ctrl(json_output=True)
    self.logger.info("Using id_ctrl command...")

    ## Informa si el comando se ejecuto correctamente
    if found_log is None:
      self.logger.error("Command Failed")
      return False
    self.logger.info("Command Succeeded")
    self.errors = self.validate(self.expected_log, found_log)
    if self.errors == 0:
        self.logger.info("TEST PASSED, 0 errors")
        return True
    elif self.errors > 0:
        self.logger.info(f"TEST FAILED, {self.errors} error(s)")
        return False
    else:
        self.logger.error("ERROR: Can't validate")
        return False
      

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
        self.logger.error(f"Error: Expected {expected_log[key]}, Found {found_log[key]}")
    return count
