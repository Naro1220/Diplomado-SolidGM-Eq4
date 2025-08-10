from logger.log_manager import LogManager
from nvme.nvme_wrapper import NvmeCommands

if __name__ == "__main__":
    nvme_device = "/dev/nvme0"
    namespace_id = 1
    
    log_manager = LogManager(testname="id_ns_test", console=True)
    logger = log_manager.get_logger()
    nvme_wrapper = NvmeCommands("/dev/nvme0", logger)
  
    #ID-NS command via admin-passthru
    logger.info("Datos crudos:")
    output, err, returncode, status = nvme_wrapper.nvme_id_ns(namespace_id=namespace_id)
    
    # Mostrar los datos crudos
    if output:
        logger.info(f"\nDatos crudos recibidos:\n{output}")
    
    logger.info("\nDatos parseados:")
    parsed_output, raw_output, err, returncode, status = nvme_wrapper.nvme_id_ns_parsed(namespace_id=namespace_id)
    
    # Mostrar los datos parseados
    if parsed_output:
        logger.info(f"\nDatos parseados:\n{parsed_output}")
    else:
        logger.error("No se recibieron datos parseados")
  
    #Crear namespace
    nsid = nvme_wrapper.create_ns(size=1000000000)
   
   
    #Attach namespace
    #Delete namespace