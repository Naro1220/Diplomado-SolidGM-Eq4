import json
from log_manager import LogManager
from nvme_wrapper import NvmeCommands

## Datos de nuestro NVME controller
DEVICE = "/dev/nvme0"
NVME = "nvme"

## Datos del resultado del comando id-ctrl que debemos ignorar
IGNORE_LIST = ['sn', 'fguid', 'unvmcap', 'subnqn']

##Leemos el archivo json del resultado esperado
ruta_json = 'expected_log.json'

try:
    ##Si logra leerlo, lo guardara en la variable EXPECTED_LOG
    with open(ruta_json, 'r') as archivo_json:
        EXPECTED_LOG = json.load(archivo_json)
except FileNotFoundError:
    ##Sino encuentra el archivo, arroja el siguiente error
    print(f"Error: El archivo {ruta_json} no se encontró.")

## Clase para hacer la prueba
class TestIdCtrl():

  ## Da nuestro logger y las funciones de NVME a la clase
  def __init__(self, logger, nvme):
    self.logger = logger
    self.nvme = nvme
        
  def run(self):
    error_count = 0
    ## Manda el comando id-ctrl en formato json al controlador y guarda el diccionario
    found_log = self.nvme.id_ctrl(json_output=True)
    self.logger.info("Using id_ctrl command...")

    ## Informa si el comando se ejecuto correctamente
    if found_log != None:
      self.logger.info("Command Succeeded")
    else:
      self.logger.error("Command Failed")
      return None
    
    ## Valida ambos logs y regresa la cantidad de errores que hubo (-1 sino pudo validad, 0 o mas si hubo)
    error_count = self.validate(EXPECTED_LOG, found_log)
    return error_count

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
    
## Inicia el logger y las funciones en un objeto      
##test = LogManager("test_id_control")
##logger = test.get_logger()
##nvme = NvmeCommands(device = DEVICE, logger = logger)

## Crea un objeto con las funciones de esta prueba, y lo corre
##id_ctrl_test = TestIdCtrl(logger,nvme)
##errors = id_ctrl_test.run()
##print(errors)


