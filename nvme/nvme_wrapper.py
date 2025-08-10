import subprocess
import json


from logger.log_manager import LogManager

class NvmeCommands():
    """
    A wrapper class around the `nvme-cli` command-line tool for interacting with NVMe devices.

    Attributes:
        device (str): The target NVMe device path (e.g., '/dev/nvme0').
        logger (logging.Logger): A logger instance used for logging command executions and errors.
    """

    def __init__(self, device, logger):
        """
        Initializes the NvmeCommands interface.

        Args:
            device (str): Path to the NVMe device (e.g., '/dev/nvme0').
            logger (logging.Logger): A logger instance for debug and error output.
        """

        self.logger = logger
        self.device = device

    def _execute_cmd(self, cmd: list):
        """
        Executes an NVMe CLI command and handles logging and errors.

        Args:
            cmd (list): The full command to execute as a list of strings.

        Returns:
            str | None: The command's stdout if successful; None if an error occurred.
        """

        # Convert the command list into string for logging.
        cmd_str = ' '.join(cmd)

        # Log the command to be executed.
        self.logger.info(f"Executing: {cmd_str}")

        try:
            # Execute the command capturing stdout and stderr. Enable exception raise if command fails. 
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Return the stdout if the command succeed.
            return result.stdout
        except subprocess.CalledProcessError as error:
            # Log the command that failed.
            self.logger.error(f"Command failed: {cmd_str}")

            # Log the stderr output.
            self.logger.error(f"stderr: {error.stderr}")

            return None
        
    def id_ctrl(self, json_output=False):
        """
        Retrieves the controller identification data of the NVMe device.

        This corresponds to the `nvme id-ctrl` command, which provides detailed info about
        the controller capabilities and configuration.

        Args:
            json_output (bool): If True, returns the output parsed as a dictionary using JSON;
                                if False, returns the raw string output.

        Returns:
            dict | str | None:
                - A dictionary if `json_output=True` and the command succeeds.
                - A raw string if `json_output=False` and the command succeeds.
                - None if the command fails or output is empty.
        """

        # Mandatory command structure: nvme id-ctrl {device_path}
        cmd = ["nvme", "id-ctrl", self.device]

        # Set output format to JSON if requested. 
        if json_output:
            cmd.append("-o=json")

        # Execute the command
        cmd_output = self._execute_cmd(cmd)

        # Parse and convert the JSON formatted string to a dictionary
        if json_output and cmd_output:
            try:
                cmd_output = json.loads(cmd_output)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse JSON output from 'id-ctrl' command.")
                self.logger.info(f"Raw output: {cmd_output}")
                return None

        return cmd_output
    
    def list(self, json_output=False, verbose=False):
        """
        Lists all NVMe devices on the system.

        Args:
            json_output (bool): Return parsed JSON output if True.

        Returns:
            dict | str | None: Parsed JSON dict, raw string output, or None if failed.
        """

        # Mandatory command structure: nvme list
        cmd = ["nvme", "list"]

        # Increase output verbosity if requsted.
        if verbose:
            cmd.append("-v")

        # Set output format to JSON if requested. 
        if json_output:
            cmd.append("-o=json")

        # Execute the command
        cmd_output = self._execute_cmd(cmd)

        # Parse and convert the JSON formatted string to a dictionary
        if json_output and cmd_output:
            try:
                cmd_output = json.loads(cmd_output)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse JSON output from 'list' command.")
                self.logger.info(f"Raw output: {cmd_output}")
                return None
            
        return cmd_output
    
    def read(self, nsid=1, start_block=0, block_count=0, data_size=512):
        """
        Reads blocks from the NVMe device.

        Args:
            nsid (int): Identifier of the desired namespace.
            block_count (int): Number of blocks on device to access.
            start_block (int): 64-bit address of first block to access.
            data_size (int): Size of data in bytes.

        Returns:
            str | None: Command output if successful, else None.
        """ 

        # Get the path to the selected namespace.
        device_path = f"{self.device}n{nsid}"

        # Mandatory command structure: nvme read {device_path}.
        cmd = ["nvme", "read", device_path]

        # Add the Start Block to the command.
        cmd.append(f"--start-block={start_block}")

        # Add the Block Count to the command.
        cmd.append(f"--block-count={block_count}")

        # Add the Data Size to the command.
        cmd.append(f"--data-size={data_size}")

        # Execute the command
        cmd_output = self._execute_cmd(cmd)

        return cmd_output
    
    def write(self, nsid=1, start_block=0, block_count=0, data_size=512, input_file=None):
        """
        Writes blocks to the NVMe device from a file.

        Args:
            nsid (int): Identifier of the desired namespace.
            block_count (int): Number of logical blocks to write.
            start_block (int): Starting logical block address.
            data_size (int): Size of data in bytes.
            input_file (str): Path to the input file to be written.

        Returns:
            str | None: Command output if successful, else None.
        """

        # Get the path to the selected namespace.
        device_path = f"{self.device}n{nsid}"

        # Mandatory command structure: nvme write {device_path}.
        cmd = ["nvme", "write", device_path]

        # Add the Start Block to the command.
        cmd.append(f"--start-block={start_block}")

        # Add the Block Count to the command.
        cmd.append(f"--block-count={block_count}")

        # Add the Data Size to the command.
        cmd.append(f"--data-size={data_size}")

        # Add the Data File to the command.
        cmd.append(f"--data={input_file}")

        # Execute the command
        cmd_output = self._execute_cmd(cmd)

        return cmd_output
    
    def parse_identify_namespace(self, raw_data):
        """
        Parsea los datos raw de identify namespace y los convierte a formato legible
        
        Args:
            raw_data: Datos binarios raw del comando identify namespace
            
        Returns:
            str: Datos formateados de manera legible
        """
        if not raw_data or len(raw_data) < 4096:
            return "Error: Datos insuficientes"
        
        # Convertir a bytes si es necesario
        if isinstance(raw_data, str):
            if all(c in '0123456789abcdefABCDEF \n' for c in raw_data):
                raw_data = bytes.fromhex(raw_data.replace(' ', '').replace('\n', ''))
            else:
                raw_data = raw_data.encode()

        try:
            # Parsear los campos principales del Identify Namespace según NVMe spec
            nsze = struct.unpack('<Q', raw_data[0:8])[0]
            ncap = struct.unpack('<Q', raw_data[8:16])[0]
            nuse = struct.unpack('<Q', raw_data[16:24])[0]
            nsfeat = raw_data[24]
            nlbaf = raw_data[25]
            flbas = raw_data[26]
            mc = raw_data[27]
            dpc = raw_data[28]
            dps = raw_data[29]
            nmic = raw_data[30]
            rescap = raw_data[31]
            fpi = raw_data[32]
            dlfeat = raw_data[33]
            nawun = struct.unpack('<H', raw_data[34:36])[0]
            nawupf = struct.unpack('<H', raw_data[36:38])[0]
            nacwu = struct.unpack('<H', raw_data[38:40])[0]
            nabsn = struct.unpack('<H', raw_data[40:42])[0]
            nabo = struct.unpack('<H', raw_data[42:44])[0]
            nabspf = struct.unpack('<H', raw_data[44:46])[0]
            noiob = struct.unpack('<H', raw_data[46:48])[0]
            
            nvmcap = struct.unpack('<QQ', raw_data[48:64])
            nvmcap_val = nvmcap[0] + (nvmcap[1] << 64)
            
            result = f"""nsze    : 0x{nsze:x}
ncap    : 0x{ncap:x}
nuse    : 0x{nuse:x}
nsfeat  : 0x{nsfeat:x}
nlbaf   : {nlbaf}
flbas   : 0x{flbas:x}
mc      : 0x{mc:x}
dpc     : 0x{dpc:x}
dps     : {dps}
nmic    : {nmic}
rescap  : 0x{rescap:x}
fpi     : 0x{fpi:x}
dlfeat  : {dlfeat}
nawun   : {nawun}
nawupf  : {nawupf}
nacwu   : {nacwu}
nabsn   : {nabsn}
nabo    : {nabo}
nabspf  : {nabspf}
noiob   : {noiob}
nvmcap  : {nvmcap_val}"""
            
            return result
            
        except Exception as e:
            return f"Error parseando datos: {e}\nDatos raw recibidos: {len(raw_data)} bytes"

    def nvme_id_ns(self, namespace_id=1):
        """
        Versión simplificada para solo obtener datos crudos
        """
        admin = AdminPassthru()
        nvme_device = "/dev/nvme0"
        self.logger.info(f"Ejecutando 'nvme id-ns' en {nvme_device} para namespace {namespace_id}")

        output, err, returncode, status_dwords = admin.admin_passthru(
            opcode = 0x06,
            namespace_id = namespace_id,
            data_len = 4096,
            read = True,
            device_path = nvme_device
        )

        if returncode == 0:
            self.logger.info("Comando ejecutado exitosamente")
        else:
            self.logger.error(f"Error ejecutando comando. Return code: {returncode}")
            if err:
                self.logger.error(f"Error: {err}")
            
        return output, err, returncode, status_dwords

    def nvme_id_ns_parsed(self, namespace_id=1):
        """
        Ejecuta admin-passthru para id-ns y parsea los datos
        """
        admin = AdminPassthru()
        nvme_device = "/dev/nvme0"
        self.logger.info(f"Ejecutando 'nvme id-ns' via admin-passthru en {nvme_device} para namespace {namespace_id}")

        raw_output, err, returncode, status_dwords = admin.admin_passthru(
            opcode = 0x06,
            namespace_id = namespace_id,
            data_len = 4096,
            read = True,
            device_path = nvme_device
        )

        if returncode == 0 and raw_output:
            parsed_output = self.parse_identify_namespace(raw_output)
            self.logger.info("Comando ejecutado exitosamente")
            return parsed_output, raw_output, err, returncode, status_dwords
        else:
            self.logger.error(f"Error ejecutando comando. Return code: {returncode}")
            if err:
                self.logger.error(f"Error: {err}")
            return None, raw_output, err, returncode, status_dwords
  
logger = LogManager("admin-passthru-test").get_logger()
nvme = NvmeCommands("/dev/nvme0", logger)

out = nvme.id_ctrl()
print(out)