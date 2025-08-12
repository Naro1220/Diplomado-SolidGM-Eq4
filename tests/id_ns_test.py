from admin import AdminPassthru
from log_manager import LogManager
from nvme_wrapper import NvmeCommands
import subprocess

## Datos de nuestro NVME controller
DEVICE = "/dev/nvme0"
NVME = "nvme"
SIZE = 1000000000
BLOCKSIZE = 512

class TestIdNs():
    def _init_(self, nvme, admin, logger):
        self.nvme = nvme
        self.admin = admin
        self.logger = logger
        self.errors = 0
        
    def run(self):
        snapshot_old = self.snapshot()
        
        if not (self.nvme.delete_ns("0XFFFFFFFF")):
            self.logger.error("Delete all namespaces unsuccessful")
            self.errors += 1
        id, calc = self.nvme.create_ns(SIZE, BLOCKSIZE)  
        if id == None:
            self.logger.error("Command create-ns unsuccessful")
            self.errors += 1
        if not (self.nvme.attach_ns(id)):
            self.logger.error("Command attach-ns unsuccessful")
            self.errors += 1
        if not (self.change_blocksize()):
            self.logger.error("Blocksize change unsuccessful")
            self.errors += 1
            
        snapshot_new = self.snapshot(snapshot_old,snapshot_new,id,calc)
        
        self.errors += self.validate()
        if self.errors == 0:
            self.logger.info("TEST PASSED, 0 errors")
            return True
        elif self.errors > 0:
            self.logger.info(f"TEST FAILED, {self.errors} error(s)")
            return False
        else:
            self.logger.error("ERROR: Can't validate")
            return False
        
    
    def change_blocksize(self,nsid):
        if BLOCKSIZE == 512:
            self.nvme.format(nsid)
        elif BLOCKSIZE == 4096:
            self.nvme.format(nsid)
        else:
            self.logger.error("Blocksize not valid") 
            return False    
        return True
    
    def snapshot(self):
        ns_list = self.nvme.list(json_output = True)
        ns_ids = [] 
        ns_id_count = len(ns_list['Devices'])
        snapshot = []
        for i in range(ns_id_count):
            ns_ids.append(ns_list['Devices'][i]['NameSpace'])
        for id in ns_ids:
            snapshot.append(self.admin.id_ns(id))
        return snapshot
    
    def validate(self,old,new,id,calc):
        errors = 0
        actual_ns = self.nvme.list(json_output = True)
        if actual_ns['Devices'][1]['SectorSize'] != BLOCKSIZE:
            self.logger.error("ERROR: Not in the blocksize from the format")
            errors += 1
        if new[id]['nuse'] == old[id]['nuse']:
            self.logger.error("ERROR: nuse didn't change")
            errors += 1
        if new[id]["nsze"] != calc or new[id]["ncap"] != calc:
            self.logger.error("ERROR: nsze/ncap are wrong")
            errors += 1
        if BLOCKSIZE == 512:
            format = 0
        elif BLOCKSIZE == 4096:
            format = 2
        if  new[id]["flbas"] != 0 or  new[id]["dsp"] != 0 or  new[id]["lbaf"] != format:
            self.logger.error("ERROR: flbas/dps/lbaf incorrect")
            errors += 1
        return errors
