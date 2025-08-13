from nvme.admin_passthru_wrapper import AdminCommands
from logger.log_manager import LogManager
from nvme.nvme_wrapper import NvmeCommands
import subprocess
import math

## Datos de nuestro NVME controller
DEVICE = "/dev/nvme0"
NVME = "nvme"
SIZE = 1000000000
BLOCKSIZE = 512
MESSAGE = '/root/repos/Diplomado-SolidGM-Eq4/tests/TEXT.txt'
FORMAT = 0
class TestIdNs():
    
    def __init__(self, logger, nvme, admin):
        
        self.nvme = nvme
        self.admin = admin
        self.logger = logger
        self.errors = 0
        
    def run(self):
        
        # Toma una captura de id-ns antes de hacer modificaciones
        snapshot_old = self.snapshot()
        
        # Borra todas las namespaces existentes
        if not (self.nvme.delete_ns(0XFFFFFFFF)):
            self.logger.error("Delete all namespaces unsuccessful")
            self.errors += 1
            
        # Conseguimos los valores del id de la namespace creada y su nsize calculado    
        id, calc = self.nvme.create_ns(SIZE, BLOCKSIZE)  
        if id == None:
            self.logger.error("Command create-ns unsuccessful")
            self.errors += 1
            
        # Agrega un ns creada a la lista    
        if not (self.nvme.attach_ns(id)):
            self.logger.error("Command attach-ns unsuccessful")
            self.errors += 1
        
        ## Cambia el formato del tamaño de los bloques de memoria de un ns
        if not (self.change_blocksize(id, FORMAT)):
            self.logger.error("Blocksize change unsuccessful")
            self.errors += 1
        
        #Guarda el nuse antes de usar el comando write
        presnap = self.snapshot(id)
        nuse = presnap["nuse"]
        
        ## Ejecuta el comando write
        if not (self.ex_write(id, BLOCKSIZE, MESSAGE, start=0)):
            self.logger.error("Couldn't write successfully")
            self.errors += 1
        
        #Guarda la nueva informacion
        snapshot_new = self.snapshot()
        
        #Hace la validacion y regresa la cantidad de errores que encuentre
        self.errors += self.validate(nuse,snapshot_new,id,calc,BLOCKSIZE,FORMAT)
        if self.errors == 0:
            self.logger.info("TEST PASSED, 0 errors")
            return True
        elif self.errors > 0:
            self.logger.info(f"TEST FAILED, {self.errors} error(s)")
            return False
        else:
            self.logger.error("ERROR: Can't validate")
            return False
        
    
    def change_blocksize(self,nsid,format):
        
        # Aplica el formato e indica si se hizo correctamente
        if not self.nvme.format(nsid,format):
            self.logger.error("Blocksize not valid") 
            return False    
        return True
    
    def snapshot(self, nsid=1):
        
        # Hace un llamada al id-ns
        snapshot = self.admin.id_ns(nsid)
        return snapshot
    
    def ex_write(self,id,blocksize,message,start):
        
        # Escribe en un bloque el mensaje
        if self.nvme.write(nsid = id, start_block=start, data_size = blocksize, input_file = message) == None:
            return False
        
        return True
        
    def validate(self,nuse,new,id,calc,blocksize,format):
        
        # Inicia los errores y castea variables dadas en string
        errors = 0
        nsid = int(id) - 1
        nsze = int(calc)
        actual_list = self.nvme.list(json_output = True)
        
        #Con la lista podemos conseguir el tamaño del namespace y vemos si es como formateamos
        if actual_list['Devices'][nsid]['SectorSize'] != blocksize:
            self.logger.error("ERROR: Not in the blocksize from the format")
            errors += 1
        
        # Checa si hubo un cambio en nuse
        if not new["nuse"] != nuse:
            self.logger.error("ERROR: nuse didn't change")
            errors += 1
        
        #  Ve si los parametro nsze y ncap coinciden con los de los calculos de capacidad  
        if new["nsze"] != nsze:  
            self.logger.error("ERROR: nsze are wrong")
            errors += 1
        if new["ncap"] != nsze:
            self.logger.error("ERROR: ncap are wrong")
            errors += 1
            
        # Comprueba si el flbas y el dps coinciden con el formato puesto
        if  new["flbas"] != format:  
            self.logger.error("ERROR: flbas/lbaf incorrect")
            errors += 1
        if new["dps"] != 0:
            self.logger.error("ERROR: dps incorrect")
            errors += 1
            
        return errors
    
test = LogManager("test_id_namespace")
logger = test.get_logger()
admin = AdminCommands(device = DEVICE,logger = logger)
nvme = NvmeCommands(device = DEVICE, logger = logger)

## Crea un objeto con las funciones de esta prueba, y lo corre
id_ns_test = TestIdNs(logger, nvme, admin)

id_ns_test.run()
