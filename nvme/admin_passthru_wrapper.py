import re
import sys
import subprocess
import json
from subprocess import Popen, PIPE
from typing import Tuple, Optional
from logger.log_manager import LogManager

# Timeout and conversion constants
CONST_TIMEOUT_LIMIT = 120  # 2 mins
SECONDS_TO_MILISECONS = 1000  # second to miliseconds
CONST_NVME = "nvme"
ADMIN_CMD = 'admin-passthru'

# Data Sizes
SMARTLOGPAGE_SIZE_BYTES = 512

# Broadcast Namespace ID
NSID_BROADCAST = 0xFFFFFFFF

# Opcodes for Admin Commands
ADMIN_CMD_OPCODE_GETLOGPAGE = 0x02

# Get Log Page - Log Page Identifiers
LOG_PAGE_ID_SMART = 0x02

# NVMe Command DWORD constants
DW0 = "DW0"
DW1 = "DW1"
DW2 = "DW2"
DW3 = "DW3"
DW4 = "DW4"
DW5 = "DW5"
DW6 = "DW6"
DW7 = "DW7"
DW8 = "DW8"
DW9 = "DW9"
DW10 = "DW10"
DW11 = "DW11"
DW12 = "DW12"
DW13 = "DW13"
DW14 = "DW14"
DW15 = "DW15"
CID = "CID"
PSDT = "PSDT"
FUSE = "FUSE"
OPC = "OPC"
NSID = "NSID"
PRP1A = "PRP1A"
PRP1B = "PRP1B"
PRP2A = "PRP2A"
PRP2B = "PRP2B"
MPTRA = "MPTRA"
MPTRB = "MPTRB"

# NVMe completion error bit positions and masks
SQHP_BIT = 0
SQHP_MASK = 0xFFFF
SQID_BIT = 16
SQID_MASK = 0xFFFF
DNR_BIT = 31
DNR_MASK = 0x1
M_BIT = 30
M_MASK = 0x01
CRD_BIT = 28
CRD_MASK = 0x3
SCT_BIT = 25
SCT_MASK = 0x7
SC_BIT = 17
SC_MASK = 0xFF
PBIT_BIT = 16
PBIT_MASK = 0x1
COMP_CID_BIT = 0
COMP_CID_MASK = 0xFFFF

# Constants related to hosting path error
SC_HOST_PATH_START = 0X70
SC_HOST_PATH_END = 0X7F
HOST_PATHING_ERROR = 8

# Definition of Status Code Type for NVMe Status
GENERIC_COMMAND_STATUS = 0
COMMAND_SPECIFIC_STATUS = 1
MEDIA_AND_DATA_INTEGRITY_ERROR = 2
PATH_RELATED_STATUS = 3
VENDOR_SPECIFIC_STATUS = 7


class SubmissionQueueEntry(object):
    def __init__(self):
        self.DW0 = None
        self.DW1 = None
        self.DW2 = None
        self.DW3 = None
        self.DW4 = None
        self.DW5 = None
        self.DW6 = None
        self.DW7 = None
        self.DW8 = None
        self.DW9 = None
        self.DW10 = None
        self.DW11 = None
        self.DW12 = None
        self.DW13 = None
        self.DW14 = None
        self.DW15 = None
        self.CID = None
        self.PSDT = None
        self.FUSE = None
        self.OPC = None
        self.NSID = None
        self.PRP1A = None
        self.PRP1B = None
        self.PRP2A = None
        self.PRP2B = None
        self.MPTRA = None
        self.MPTRB = None
        self.data_buffer = bytearray(0)


class CompletionQueueEntry(object):
    def __init__(self):
        self.dw0 = 0
        self.dw1 = 0
        self.dw2 = 0
        self.dw3 = 0
        self.cmdspec = 0
        self.reserved1 = 0
        self.sqid = 0
        self.sqhp = 0
        self.dnr = 0
        self.more = 0
        self.crd = 0
        self.status_code_type = 0
        self.status_code = 0
        self.phase_tag = 0
        self.cid = 0
        self.elapsed_time = 0
        self.latency = 0
        self.data_buffer = bytearray(0)

    def populate_cqe(self, status, data_buffer):
        self.dw0 = status[DW0]
        self.dw1 = status[DW1]
        self.dw2 = status[DW2]
        self.dw3 = status[DW3]
        self.cmdspec = self.dw0
        self.reserved1 = self.dw1
        self.sqhp = (self.dw2 >> SQHP_BIT) & SQHP_MASK
        self.sqid = (self.dw2 >> SQID_BIT) & SQID_MASK
        self.dnr = (self.dw3 >> DNR_BIT) & DNR_MASK
        self.more = (self.dw3 >> M_BIT) & M_MASK
        self.crd = (self.dw3 >> CRD_BIT) & CRD_MASK
        self.status_code_type = (self.dw3 >> SCT_BIT) & SCT_MASK
        self.status_code = (self.dw3 >> SC_BIT) & SC_MASK
        self.phase_tag = (self.dw3 >> PBIT_BIT) & PBIT_MASK
        self.cid = (self.dw3 >> COMP_CID_BIT) & COMP_CID_MASK

        self.latency, self.data_buffer = self.extract_latency_from_buffer(data_buffer)

        # data_buffer is sometimes too long of an int (i.e. 1024 digits) which causes the conversion to bytearray to fail
        # To avoid this, we need to convert it to string
        if isinstance(self.data_buffer, int):
            self.data_buffer = str(self.data_buffer)

        # data_buffer and metadata_buffer must be passed into SsdAbstractionReturn as a bytearray or None
        if self.data_buffer is not None and isinstance(self.data_buffer, str):
            # Check if string consist of hex values
            is_hex = re.fullmatch(r"^([0-9a-fA-F]{2})*$", self.data_buffer) is not None
            if is_hex:
                self.data_buffer = bytearray.fromhex(self.data_buffer)
            else:
                # Need to specify the encoding since data_buffer is a string
                self.data_buffer = bytearray(encoding=sys.stdout.encoding, source=self.data_buffer)
        elif self.data_buffer is not None and not isinstance(self.data_buffer, bytearray):
            self.data_buffer = bytearray(self.data_buffer)

    def extract_latency_from_buffer(self, output):
        latency = None
        data_buffer = output
        # With Python3 the incoming data_buffer in some cases is bytes from stdout
        # Need to convert to string so that the latency info can be removed
        if isinstance(data_buffer, bytes):
            data_buffer = output.decode(encoding=sys.stdout.encoding, errors="replace")
        if not isinstance(data_buffer, str) or output is None:
            return latency, data_buffer
        match = re.match(r".*latency: (\d+) us\n", data_buffer)
        if match is not None:
            latency = int(match.group(1))  # latency in microsecs
            latency = latency / 1000  # latency in millisecs and is a float value
            data_startpos = match.regs[0][1]  # points to the end of match + 1 position
            data_buffer = None
            if len(output) > data_startpos:
                data_buffer = output[data_startpos:]
        return latency, data_buffer


class AdminPassthru:
    def __init__(self, device=None, logger=None):
        """
        Initializes the AdminPassthru interface.

        Args:
            device (str): Path to the NVMe device (e.g., '/dev/nvme0').
            logger (logging.Logger): A logger instance for debug and error output.
        """
        self.device = device
        self.logger = logger

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
        if self.logger:
            self.logger.info(f"Executing: {cmd_str}")

        try:
            # Execute the command capturing stdout and stderr. Enable exception raise if command fails. 
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Return the stdout if the command succeed.
            return result.stdout
        except subprocess.CalledProcessError as error:
            # Log the command that failed.
            if self.logger:
                self.logger.error(f"Command failed: {cmd_str}")
                self.logger.error(f"stderr: {error.stderr}")

            return None

    def obtain_status_code(self, stdout_txt, stderr):
        """Extract status codes from command output"""
        status = {}

        dword0 = 0
        dword1 = 0
        dword2 = 0
        dword3 = 0

        if stdout_txt != "":
            try:
                dword0 = re.findall(r"value:([0x]*[0-9A-Fa-f]+)", stdout_txt)[-1]
                dword0 = int(dword0, 16)
            except:
                pass

        if stderr != "":
            # NVMe-CLI is printing response to stderr
            # see: https://github.com/linux-nvme/nvme-cli/blob/master/nvme.c#L5674
            success_pattern = r"^.*Success and result: 0x(?P<result>[0-9A-Fa-f]+)$"
            re_search = re.match(success_pattern, stderr)
            if re_search is not None:
                result = re_search.group("result")
                dword0 = int(result, 16)

            try:
                dword3 = re.findall(r"\(([0x]*[0-9A-Fa-f]+)\)", stderr)[-1]
                dword3 = int(dword3, 16) << 17
            except:
                pass

        status[DW0] = dword0
        status[DW1] = dword1
        status[DW2] = dword2
        status[DW3] = dword3

        return status

    def run_cmd(self, cmd):
        """Execute command and return output, error, return code and status"""
        try:
            process = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            returncode = process.returncode
            stdout_txt = stdout.decode(encoding=sys.stdout.encoding, errors="replace")
            stderr_txt = stderr.decode(encoding=sys.stdout.encoding, errors="replace")
            status_dwords = self.obtain_status_code(stdout_txt, stderr_txt)
            return stdout_txt, stderr_txt, returncode, status_dwords
        except Exception as e:
            print("Error ejecutando el comando: {}".format(e))
            return None, None, -1, {}

    def admin_passthru(self, opcode, flags=None, reserved=None, namespace_id=None, nsid=None, cdw2=None, 
                       cdw3=None, cdw10=None, cdw11=None, cdw12=None, cdw13=None, cdw14=None, cdw15=None, 
                       data_len=None, metadata_len=None, input_file=None, read=None, show_command=None, 
                       dry_run=None, raw_binary=None, prefill=None, write=None, latency=None, 
                       use_controller_path=False, device_path=None, stdin_data=None, raw=False):
        """
        Send an NVMe admin command via passthrough interface.
        Merged version supporting both implementations.

        Args:
            opcode (int): Admin command opcode.
            flags (int): Command flags.
            reserved (int): Reserved field.
            namespace_id (int): Namespace ID (alternative to nsid).
            nsid (int): Namespace ID.
            cdw2-cdw15 (int|None): Command DWORD values.
            data_len (int): Length of data buffer.
            metadata_len (int): Length of metadata buffer.
            input_file (str): Input file path.
            read (bool): Whether this is a read operation.
            write (bool): Whether this is a write operation.
            show_command (bool): Show command being executed.
            dry_run (bool): Dry run mode.
            raw_binary (bool): Raw binary output.
            prefill (int): Prefill value.
            latency (bool): Show latency information.
            use_controller_path (bool): Use controller path.
            device_path (str): Device path (overrides self.device).
            stdin_data: Input data from stdin.
            raw (bool): Return raw output or parsed.

        Returns:
            tuple: (output, error, returncode, status_dwords) or just output if using simple mode
        """
        # Use provided device_path or fall back to self.device
        device = device_path or self.device
        if not device:
            raise ValueError("Device path must be provided either in constructor or as parameter")

        # Handle namespace_id vs nsid parameter
        if nsid is None and namespace_id is not None:
            nsid = namespace_id
        elif nsid is None:
            nsid = 1

        timeout = CONST_TIMEOUT_LIMIT * SECONDS_TO_MILISECONS  # Converting to miliseconds

        params = {
            '-O': opcode,
            '-f': flags,
            '-R': reserved,
            '-n': nsid,
            '--cdw2': cdw2,
            '--cdw3': cdw3,
            '--cdw10': cdw10,
            '--cdw11': cdw11,
            '--cdw12': cdw12,
            '--cdw13': cdw13,
            '--cdw14': cdw14,
            '--cdw15': cdw15,
            '-r': read,
            '-w': write,
            '-i': input_file,
            '-l': data_len,
            '-m': metadata_len,
            '-s': show_command,
            '-d': dry_run,
            '-b': raw_binary,
            '-p': prefill,
            '-t': timeout,
            '-T': latency
        }

        command = [CONST_NVME, ADMIN_CMD, device]

        for param in params:
            if params[param] is None:
                continue
            command.append(param)
            command.append(str(params[param]))

        output, err, returncode, status_dwords = self.run_cmd(command)

        if returncode:
            match = re.match(r'NVMe command result:(\d+)', err) if err else None
            if not match:
                if self.logger:
                    self.logger.error(f"An error has occurred while running: {command}")
                    self.logger.error(f"Error: {err}")
                    self.logger.error(f"Output: {output}")
                else:
                    print("An error has occurred while running: {}".format(command))
                    print("Error: {}".format(err))
                    print("Output: {}".format(output))

        return output, err, returncode, status_dwords

    def _get_log_page(self, log_page_id, nsid=1, log_len=512):
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

        output, err, returncode, status_dwords = self.admin_passthru(
            opcode=ADMIN_CMD_OPCODE_GETLOGPAGE,
            nsid=nsid,
            data_len=log_len,
            read=True,
            cdw10=dword10
        )

        return output

    def smart_log(self, device_path=None):
        """
        Retrieve and parse the SMART/Health Information Log Page.

        Args:
            device_path (str): Optional device path override.

        Returns:
            str or None: JSON-formatted SMART log data, or None on failure.
        """
        # SMART/Health information is log page 0x02.
        page_id_smart = LOG_PAGE_ID_SMART

        # To request the controller log page, the namespace identifier specified is 0xFFFFFFFF.
        nsid = NSID_BROADCAST

        # SMART/Health log is 512 bytes.
        log_len = SMARTLOGPAGE_SIZE_BYTES
        
        # Temporarily override device if provided
        original_device = self.device
        if device_path:
            self.device = device_path
        
        try:
            # Send Get Log Page command to retrieve SMART/Health log page.
            log_page_output = self._get_log_page(log_page_id=page_id_smart, nsid=nsid, log_len=log_len)
            return self._parse_smart_log(log_page_output)
        finally:
            # Restore original device
            self.device = original_device

    def _parse_smart_log(self, raw_bytes):
        """
        Parse raw bytes output of SMART log page into a structured JSON.

        Args:
            raw_bytes (str): Raw hex string output from the admin-passthru command.

        Returns:
            str: JSON string of parsed SMART log.
        """
        if not raw_bytes:
            return None

        try:
            hex_lines = re.findall(r'\b(?:[0-9a-f]{2} ){15}[0-9a-f]{2}', raw_bytes, re.IGNORECASE)
            hex_str = ''.join(''.join(line.split()) for line in hex_lines)
            info = bytes.fromhex(hex_str)
            smart_log_dict = {
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
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error parsing SMART log: {e}")
            return None


# Legacy class for backward compatibility with the first implementation
class AdminCommands(AdminPassthru):
    """Legacy wrapper for backward compatibility"""
    def __init__(self, device, logger):
        super().__init__(device=device, logger=logger)
    
    def admin_passthru(self, opcode, nsid=1, data_len=None, read=True, cdw10=None, cdw11=None, cdw12=None, 
                       cdw13=None, cdw14=None, cdw15=None, raw=False):
        """
        Legacy method signature for backward compatibility with admin_mis_compa.py
        """
        return super().admin_passthru(
            opcode=opcode,
            nsid=nsid,
            data_len=data_len,
            read=read,
            cdw10=cdw10,
            cdw11=cdw11,
            cdw12=cdw12,
            cdw13=cdw13,
            cdw14=cdw14,
            cdw15=cdw15,
            raw=raw
        )[0]  # Return only output for backward compatibility

if __name__ == "__main__":
    # Test code - can be removed in production
    
    
    logger = LogManager("admin-passthru-test").get_logger()
    admin = AdminPassthru("/dev/nvme0", logger)
    
    # Test SMART log
    out = admin.smart_log()
    if out:
        print(out)
    else:
        print("No SMART log data received")