import subprocess
import json
import re

from logger.log_manager import LogManager

"""
Data Sizes
"""
SMARTLOGPAGE_SIZE_BYTES = 512

"""
Broadcast Namespace ID
"""
NSID_BROADCAST = 0xFFFFFFFF

"""
Opcodes for Admin Commands
"""
ADMIN_CMD_OPCODE_GETLOGPAGE = 0x02

"""
Get Log Page - Log Page Identifiers
"""
LOG_PAGE_ID_SMART = 0x02

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
    
    def admin_passthru(self, opcode, nsid=1, data_len=None, read=True, cdw10=None, cdw11=None, cdw12=None, 
                       cdw13=None, cdw14=None, cdw15=None, raw=False):
        """
        Send an NVMe admin command via passthrough interface.

        Args:
            opcode (int): Admin command opcode.
            nsid (int): Namespace ID.
            data_len (int): Length of data buffer.
            read (bool): Whether this is a read operation.
            cdw10..cdw15 (int|None): Optional command DWORD values.
            raw (bool): Whether to return raw output or parsed.
            extra_args (list[str]): Additional arguments (e.g., vendor-specific options).

        Returns:
            str or None: Output from the command or None on failure.
        """

        # Mandatory command structure: nvme admin-passthru {device_path}.
        cmd = ["nvme", "admin-passthru", self.device]

        # Add the Opcode to the command.
        cmd.append(f"--opcode={opcode}")

        # Add the Namespace ID to the command.
        cmd.append(f"--namespace-id={nsid}")

        # Add CDW fields to the command if given.
        for i, cdw in enumerate([cdw10, cdw11, cdw12, cdw13, cdw14, cdw15], start=10):
            if cdw is not None:
                cmd += [f"--cdw{i}={cdw}"]
                   
        # Add the Data I/O Length (bytes) to the command.
        if data_len:
            cmd.append(f"--data-len={data_len}")

        # Add the Dataflow Direction to Receive option to the command.
        if read:
            cmd.append("--read")

        # Execute the command
        cmd_output = self._execute_cmd(cmd)

        return cmd_output
    
    def get_log_page(self, log_page_id, nsid=1, log_len=512):
        """
        Get an NVMe log page via the admin passthru interface.

        Args:
            log_page_id (int): Log Page Identifier.
            nsid (int): Namespace ID.
            log_len (int): Number of bytes to read.

        Returns:
            str: Log page output.
        """

        # Number of Dwords Lower (NUMDL) field is in unit of DWords (4 bytes) zeroes-based.
        numdl = (log_len // 4) - 1

        # Set the Log Page Identifier (LID) and Number of Dwords Lower (NUMDL) fields in the Dword 10.
        dword10 = (numdl << 16) | log_page_id

        return self.admin_passthru(
            opcode=ADMIN_CMD_OPCODE_GETLOGPAGE,
            nsid=nsid,
            data_len=log_len,
            read=True,
            cdw10=dword10
        )
    
    def smart_log(self):
        """
        Retrieve and parse the SMART/Health Information Log Page.

        Returns:
            str or None: JSON-formatted SMART log data, or None on failure.
        """

        # SMART/Health information is log page 0x02.
        page_id_smart = LOG_PAGE_ID_SMART

        # To request the controller log page, the namespace identifier specified is 0xFFFFFFFF.
        nsid = NSID_BROADCAST

        # SMART/Health log is 512 bytes.
        log_len = SMARTLOGPAGE_SIZE_BYTES
        
        # Send Get Log Page command to retrieve SMART/Health log page.
        log_page_output = self.get_log_page(log_page_id=page_id_smart, nsid=nsid, log_len=log_len)

        return self._parse_smart_log(log_page_output)
    
    def _parse_smart_log(self, raw_bytes):
        """
        Parse raw bytes output of SMART log page into a structured dictionary.

        Args:
            raw_bytes (str): Raw hex string output from the admin-passthru command.

        Returns:
            str: JSON string of parsed SMART log.
        """

        hex_lines = re.findall(r'\b(?:[0-9a-f]{2} ){15}[0-9a-f]{2}', raw_bytes, re.IGNORECASE)
        hex_str = ''.join(''.join(line.split()) for line in hex_lines)
        info = bytes.fromhex(hex_str)
        smart_log_dict =  {
            "critical_warning": info[0],
            "temperature": int.from_bytes(info[1:3], 'little'),
            "available_spare": info[3],
            "available_spare_threshold": info[4],
            "percentage_used": info[5],
            "data_units_read": int.from_bytes(info[32:48], 'little'),
            "data_units_written": int.from_bytes(info[48:64], 'little'),
            "host_read_commands": int.from_bytes(info[64:80], 'little'),
            "host_write_commands": int.from_bytes(info[80:96], 'little'),
            "controller_busy_time": int.from_bytes(info[96:112], 'little'),
            "power_cycles": int.from_bytes(info[112:128], 'little'),
            "power_on_hours": int.from_bytes(info[128:144], 'little'),
            "unsafe_shutdowns": int.from_bytes(info[144:160], 'little'),
            "media_errors": int.from_bytes(info[160:176], 'little'),
            "num_err_log_entries": int.from_bytes(info[176:192], 'little'),
        }

        return json.dumps(smart_log_dict, indent=2)


logger = LogManager("admin-passthru-test").get_logger()
nvme = NvmeCommands("/dev/nvme0", logger)

out = nvme.smart_log()
print(out)