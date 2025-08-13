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
        
    def id_ctrl(self, json_output=False, vendor=False):
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
        if vendor:
            cmd = ["nvme", "solidigm", "id-ctrl", self.device]
        else:
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
        
    def create_ns(self, size, blocksize):
        
        cmd = [ "nvme", "create-ns", self.device]
        
        calc =str(size // blocksize)
        
        nsze = "--nsze=" + calc 
        ncap = "--ncap=" + calc
        
        cmd.append(nsze)
        cmd.append(ncap)
        cmd.append("--flbas=0")
        
        # Execute the command
        cmd_output = self._execute_cmd(cmd)
        nsid = ""
        for char in cmd_output:
            if char.isdigit():
                nsid += char

        return nsid, calc
    
    def attach_ns(self, nsID, controller="0"):
        """
        Attach a namespace to a controller.        
        """
        if nsID == None:
            self.logger.error("nsID not provided")             
            return False
        
    # Mandatory command structure: nvme id-ctrl {device_path}
        cmd = ["nvme", "attach-ns", self.device]
        cmd.append(f"-n {nsID}")
        cmd.append(f"-c {controller}")

        # Execute the command
        cmd_output = self._execute_cmd(cmd)

        # Parse and convert the JSON formatted string to a dictionary
        if cmd_output == None:
            self.logger.error("Didn't execute Attach")  
            return False
        return True

    def detach_ns(self, nsID, controller="0"):
        """
        Detach a namespace from a controller.
        """
        if nsID is None:
            self.logger.error("nsID not provided")
            return False
    
        cmd = ["nvme", "detach-ns", self.device]
        cmd.append(f"-n {nsID}")
        cmd.append(f"-c {controller}")
    
        # Ejecutar el comando
        cmd_output = self._execute_cmd(cmd)
    
        if cmd_output is None:
            self.logger.error(f"Didn't detach namespace {nsID}")
            return False
    
        self.logger.info(f"Namespace {nsID} detached from controller {controller}")
        return True

    def delete_ns(self, nsID):
        """
        Delete a namespace from the NVMe device.
        """
        if nsID is None:
            self.logger.error("No se dio nsID")
            return False
    
        cmd = ["nvme", "delete-ns", self.device]
        cmd.append(f"-n {nsID}")
    
        # Ejecutar el comando
        cmd_output = self._execute_cmd(cmd)
    
        if cmd_output is None:
            self.logger.error(f"Didn't delete namespace {nsID}")
            return False
    
        return True
        
    def format(self, nsID, format):
        
        """
        Change format from namespace from the NVMe device.
        """
        if nsID is None:
            self.logger.error("No defined nsID")
            return False
    
        cmd = ["nvme", "format"]
        ns = self.device + f"n{nsID}"
        lbaf = f"--lbaf={format}"
        cmd.append(ns)
        cmd.append(lbaf)
        
    
        # Ejecutar el comando
        cmd_output = self._execute_cmd(cmd)
    
        if cmd_output is None:
            self.logger.error(f"Didn't format namespace {nsID}")
            return False
        return True

    def get_feature(self, fid):
        
        cmd = ["nvme","get-feature", self.device,"-f"]
        
        cmd.append(f"{fid}")
        cmd.append("-H")
        
        cmd_output = self._execute_cmd(cmd)
        
        return cmd_output
