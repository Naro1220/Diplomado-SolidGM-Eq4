import subprocess
import json

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
        self.logger.debug(f"Executing: {cmd_str}")

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
                self.logger.debug(f"Raw output: {cmd_output}")
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
                self.logger.debug(f"Raw output: {cmd_output}")
                return None
            
        return cmd_output
    
    def read(self, nsid=1, block_count=0, start_block=0):
        """
        Reads blocks from the NVMe device.

        Args:
            namespace_id (int): Namespace ID to read from.
            block_count (int): Number of logical blocks to read.
            start_block (int): Starting logical block address.
            output_file (str): Path to the output file.

        Returns:
            str | None: Command output if successful, else None.
        """ 

        # Mandatory command structure: nvme read {device_path}
        cmd = ["nvme", "read", self.device]
