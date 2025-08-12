import re
import subprocess
import json

from logger.log_manager import LogManager

"""
Data Sizes
"""
SMARTLOGPAGE_SIZE_BYTES = 512
IDENTIFY_DATA_SIZE_BYTES = 4096

"""
Broadcast Namespace ID
"""
NSID_BROADCAST = 0xFFFFFFFF

"""
Opcodes for Admin Commands
"""
ADMIN_CMD_OPCODE_GETLOGPAGE = 0x02
ADMIN_CMD_OPCODE_IDENTIFY = 0x06
ADMIN_CMD_OPCODE_SETFEATURES = 0x09
ADMIN_CMD_OPCODE_GETFEATURES = 0x0A

"""
Get Log Page - Log Page Identifiers
"""
LOG_PAGE_ID_SMART = 0x02

"""
Identify - Controller or Namespace Structures
"""
IDENTIFY_STRUCTURE_NAMESPACE = 0x00
IDENTIFY_STRUCTURE_CONTROLLER = 0x01

class AdminCommands:

    def __init__(self, device, logger):
        """
        Initializes the AdminCommands interface.

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
            tuple(str|None, str|None): stdout and stderr if successful; None, None if error.
        """

        # Convert the command list into string for logging.
        cmd_str = ' '.join(cmd)

        # Log the command to be executed.
        self.logger.info(f"Executing: {cmd_str}")

        try:
            # Execute the command capturing stdout and stderr. Enable exception raise if command fails. 
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Return both stdout and stderr if the command succeed.
            return result.stdout, result.stderr
        
        except subprocess.CalledProcessError as error:
            # Log the command that failed.
            self.logger.error(f"Command failed: {cmd_str}")

            # Log the stderr output.
            self.logger.error(f"stderr: {error.stderr}")

            return None, None
        
        except Exception as ex:
            # Log in case of any other errors.
            self.logger.error(f"Unexpected error executing command: {ex}")

            return None, None
        
    def _parse_cqe_result(self, stderr: str):
        """
        Parse the completion queue entry DWORD0 result from stderr text.

        Args:
            stderr (str): Standard error output from nvme admin-passthru command.

        Returns:
            int | None: The DWORD0 integer value if found, else None.
        """

        if not stderr:
            self.logger.warning("No stderr to parse CQE result from.")
            return None

        pattern = r"result:\s*0x([0-9a-fA-F]+)"
        match = re.search(pattern, stderr)
        if match:
            try:
                hex_str = match.group(1)
                return int(hex_str, 16)
            except Exception as ex:
                self.logger.error(f"Error parsing CQE result hex: {ex}")
        else:
            self.logger.warning("CQE result pattern not found in stderr.")
        return None

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

        Returns:
            tuple(str|None, str|None): stdout and stderr or None,None on failure.
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
        cmd_stdout, cmd_stderr = self._execute_cmd(cmd)

        return cmd_stdout, cmd_stderr
    
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

        try:
            # Number of Dwords Lower (NUMDL) field is in unit of DWords (4 bytes) zeroes-based.
            numdl = (log_len // 4) - 1

            # Set the Log Page Identifier (LID) and Number of Dwords Lower (NUMDL) fields in the Dword 10.
            dword10 = (numdl << 16) | log_page_id

            stdout, _ =  self.admin_passthru(
                opcode=ADMIN_CMD_OPCODE_GETLOGPAGE,
                nsid=nsid,
                data_len=log_len,
                read=True,
                cdw10=dword10
            )

            if stdout is None:
                self.logger.error("Failed to get log page output.")

            return stdout
        
        except Exception as ex:
            self.logger.error(f"Exception in _get_log_page: {ex}")
            return None
    
    def smart_log(self):
        """
        Retrieve and parse the SMART/Health Information Log Page.

        Returns:
            str or None: JSON-formatted SMART log data, or None on failure.
        """

        try:
            # SMART/Health information is log page 0x02.
            page_id_smart = LOG_PAGE_ID_SMART

            # To request the controller log page, the namespace identifier specified is 0xFFFFFFFF.
            nsid = NSID_BROADCAST

            # SMART/Health log is 512 bytes.
            log_len = SMARTLOGPAGE_SIZE_BYTES
            
            # Send Get Log Page command to retrieve SMART/Health log page.
            log_page_output = self._get_log_page(log_page_id=page_id_smart, nsid=nsid, log_len=log_len)
            if not log_page_output:
                self.logger.error("No SMART log page output received.")
                return None

            return self._parse_smart_log(log_page_output)
        
        except Exception as ex:
            self.logger.error(f"Exception in smart_log: {ex}")
            return None
    
    def _parse_smart_log(self, raw_bytes):
        """
        Parse raw bytes output of SMART log page into a structured JSON.

        Args:
            raw_bytes (str): Raw hex string output from the admin-passthru command.

        Returns:
            str: JSON string of parsed SMART log.
        """

        if not raw_bytes:
            self.logger.error("No raw bytes to parse for SMART log.")

        try:
            # Extract the hex dump from nvme CLI output.
            hex_lines = re.findall(r'\b(?:[0-9a-f]{2} ){15}[0-9a-f]{2}', raw_bytes, re.IGNORECASE)

            if not hex_lines:
                self.logger.warning("No hex lines found in SMART log output.")
                return None
            
            hex_str = ''.join(''.join(line.split()) for line in hex_lines)
            info = bytes.fromhex(hex_str)

            smart_log_dict =  {
                "cw": info[0],                                    # Critical Warning
                "ctemp": int.from_bytes(info[1:3], 'little'),     # Composite Temperature
                "avsp": info[3],                                  # Available Spare
                "avspt": info[4],                                 # Available Spare Threshold
                "pused": info[5],                                 # Percentage Used
                "dur": int.from_bytes(info[32:48], 'little'),     # Data Units Read
                "duw": int.from_bytes(info[48:64], 'little'),     # Data Units Written
                "hrc": int.from_bytes(info[64:80], 'little'),     # Host Read Commands
                "hwc": int.from_bytes(info[80:96], 'little'),     # Host Write Commands
                "cbt": int.from_bytes(info[96:112], 'little'),    # Controller Busy Time
                "pwrc": int.from_bytes(info[112:128], 'little'),  # Power Cycles
                "poh": int.from_bytes(info[128:144], 'little'),   # Power On Hours
                "upl": int.from_bytes(info[144:160], 'little'),   # Unexpected Power Losses
                "mdie": int.from_bytes(info[160:176], 'little'),  # Media and Data Integrity Errors
                "neile": int.from_bytes(info[176:192], 'little'), # Number of Error Information Log Entries
            }

            return json.dumps(smart_log_dict, indent=2)
        
        except Exception as ex:
            self.logger.error(f"Failed to parse SMART log: {ex}")
            return None

    def _identify(self, nsid, cns):
        """
        Send Identify command via admin passthru.

        Args:
            nsid (int): Namespace ID to identify.
            cns (int): Controller or Namespace Structure type.

        Returns:
            str or None: Raw output from identify command, or None on failure.
        """

        try:
            # cdw10 holds CNS value in bits[7:0], rest reserved.
            cdw10 = cns & 0xFF

            stdout, _ =  self.admin_passthru(
                opcode=ADMIN_CMD_OPCODE_IDENTIFY,
                nsid=nsid,
                data_len=IDENTIFY_DATA_SIZE_BYTES,
                read=True,
                cdw10=cdw10
            )

            if stdout is None:
                self.logger.error("Identify command returned no output.")

            return stdout
        
        except Exception as ex:
            self.logger.error(f"Exception in _identify: {ex}")
            return None
    
    def id_ns(self, nsid=1):
        """
        Identify Namespace data structure for given Namespace ID.

        Args:
            nsid (int): Namespace ID to query.

        Returns:
            str or None: JSON-formatted namespace identification data, or None on failure.
        """

        try:
            raw_output = self._identify(nsid=nsid, cns=IDENTIFY_STRUCTURE_NAMESPACE)
            if not raw_output:
                self.logger.error("No output from id_ns identify command.")
                return None

            return self._parse_id_ns(raw_output)
        
        except Exception as ex:
            self.logger.error(f"Exception in id_ns: {ex}")
            return None
    
    def _parse_id_ns(self, raw_bytes):
        """
        Parse raw Identify Namespace bytes into JSON structure.

        Args:
            raw_bytes (str): Raw hex string from admin-passthru.

        Returns:
            str: JSON string containing parsed namespace info.
        """

        if not raw_bytes:
            self.logger.error("No raw bytes to parse for Identify Namespace.")
            return None

        try:
            # Extract the hex dump from nvme CLI output.
            hex_lines = re.findall(r'\b(?:[0-9a-f]{2} ){15}[0-9a-f]{2}', raw_bytes, re.IGNORECASE)

            if not hex_lines:
                self.logger.warning("No hex lines found in Identify Namespace output.")
                return None
            
            hex_str = ''.join(''.join(line.split()) for line in hex_lines)
            data = bytes.fromhex(hex_str)

            ns_info = {
                "nsze": int.from_bytes(data[0:8], 'little'),        # Namespace Size (in LBAs)
                "ncap": int.from_bytes(data[8:16], 'little'),       # Namespace Capacity (in LBAs)
                "nuse": int.from_bytes(data[16:24], 'little'),      # Namespace Utilization (in LBAs)
                "nsfeat": data[24],                                 # Namespace Features
                "nlbaf": data[25],                                  # Number of LBA Formats
                "flbas": data[26],                                  # Formatted LBA Size
                "mc": data[27],                                     # Metadata Capabilities
                "dpc": data[28],                                    # End-to-end Data Protection Capabilities
                "dps": data[29],                                    # End-to-end Data Protection Type Settings
                "nmic": data[30],                                   # Namespace Multi-path I/O and Namespace Sharing Capabilities
                "rescap": data[31],                                 # Reservation Capabilities
                "fpi": data[32],                                    # Format Progress Indicator
                "dlfeat": data[33],                                 # Deallocated Logical Block Features
                "nawun": int.from_bytes(data[34:36], 'little'),     # Namespace Atomic Write Unit Normal
                "nawupf": int.from_bytes(data[36:38], 'little'),    # Namespace Atomic Write Unit Power Fail
                "nacwu": int.from_bytes(data[38:40], 'little'),     # Namespace Atomic Compare & Write Unit
                "nabsn": int.from_bytes(data[40:42], 'little'),     # Namespace Atomic Boundary Size Normal
                "nabo": int.from_bytes(data[42:44], 'little'),      # Namespace Atomic Boundary Offset
                "nabspf": int.from_bytes(data[44:46], 'little'),    # Namespace Atomic Boundary Size Power Fail
                "noiob": int.from_bytes(data[46:48], 'little'),     # Namespace Optimal I/O Boundary
                "nvmcap": int.from_bytes(data[48:64], 'little'),    # NVM Capacity
                "mssrl": int.from_bytes(data[74:76], 'little'),     # Maximum Single Source Range Length
                "mcl": int.from_bytes(data[76:80], 'little'),       # Maximum Copy Length
                "msrc": data[80],                                   # Maximum Source Range Count
                "anagrpid": int.from_bytes(data[92:96], 'little'),  # ANA Group Identifier
                "nsattr": data[99],                                 # Namespace Attributes
                "nvmsetid": int.from_bytes(data[100:102], 'little'),# NVM Set Identifier
                "endgid": int.from_bytes(data[102:104], 'little'),  # Endurance Group Identifier
                "nguid": int.from_bytes(data[104:120], 'little'),   # Namespace Globally Unique Identifier
                "eui64": int.from_bytes(data[120:127], 'little')    # IEEE Extended Unique Identifier
            }

            # Parse LBA formats (4 bytes each, starting at byte 128)
            nlbaf_count = ns_info["nlbaf"] + 1
            lbafs = []
            for i in range(nlbaf_count):
                entry_offset = 128 + (i * 4)
                entry = int.from_bytes(data[entry_offset:entry_offset + 4], 'little')
                ms = entry & 0xFFFF
                lbads = (entry >> 16) & 0xFF
                rp = (entry >> 24) & 0x3
                lbafs.append({
                    "ms": ms,                                       # Metadata Size (MS)
                    "ds": lbads,                                    # LBA Data Size (LBADS)
                    "rp": rp                                        # Relative Performance (RP)
                })

            ns_info["lbafs"] = lbafs

            return json.dumps(ns_info, indent=2)
        except Exception as ex:
            self.logger.error(f"Failed to parse Identify Namespace data: {ex}")
    
    def id_ctrl(self):
        """
        Retrieve and parse the Identify Controller data structure.

        Returns:
            str or None: JSON-formatted controller identify data, or None on failure.
        """

        try:
            # Controller structure ignores NSID, use 0
            nsid = 0

            raw_output = self._identify(nsid=nsid, cns=IDENTIFY_STRUCTURE_CONTROLLER)
            if not raw_output:
                self.logger.error("No output from id_ctrl identify command.")
                return None
            return self._parse_id_ctrl(raw_output)
        except Exception as ex:
            self.logger.error(f"Exception in id_ctrl: {ex}")
            return None
    
    def _parse_id_ctrl(self, raw_bytes):
        """
        Parse raw bytes of Identify Controller into JSON.

        Args:
            raw_bytes (str): Raw hex string from admin-passthru.

        Returns:
            str: JSON-formatted Identify Controller data.
        """

        if not raw_bytes:
            self.logger.error("No raw bytes to parse for Identify Controller.")
            return None

        try:
            # Extract the hex dump from nvme CLI output.
            hex_lines = re.findall(r'\b(?:[0-9a-f]{2} ){15}[0-9a-f]{2}', raw_bytes, re.IGNORECASE)

            if not hex_lines:
                self.logger.warning("No hex lines found in Identify Controller output.")
                return None
            
            hex_str = ''.join(''.join(line.split()) for line in hex_lines)
            info = bytes.fromhex(hex_str)

            id_ctrl_dict = {
                "vid": int.from_bytes(info[0:2], 'little'),                # PCI Vendor ID
                "ssvid": int.from_bytes(info[2:4], 'little'),              # PCI Subsystem Vendor ID
                "sn": info[4:24].decode('ascii', errors='ignore').strip(), # Serial Number
                "mn": info[24:64].decode('ascii', errors='ignore').strip(),# Model Number
                "fr": info[64:72].decode('ascii', errors='ignore').strip(),# Firmware Revision
                "rab": info[72],                                           # Recommended Arbitration Burst
            }

            return json.dumps(id_ctrl_dict, indent=2)
        
        except Exception as ex:
            self.logger.error(f"Failed to parse Identify Controller data: {ex}")
            return None
    
    def set_feature(self, fid, value, nsid=0, save=False):
        """
        Set an NVMe feature via the admin passthru interface.

        Args:
            fid (int): Feature Identifier (FID).
            value (int): Feature value to set (placed in CDW11).
            nsid (int): Namespace ID. Set to 0 for controller-wide features.
            save (bool): Whether to set the "Save" bit (bit 31) in CDW10.

        Returns:
            str or None: Command output or None on failure.
        """

        try:
            # CDW10: Bits 0–7 = FID, Bit 31 = Save
            cdw10 = fid & 0xFF
            if save:
                cdw10 |= (1 << 31)

            _, result = self.admin_passthru(
                opcode=ADMIN_CMD_OPCODE_SETFEATURES,
                nsid=nsid,
                cdw10=cdw10,
                cdw11=value
            )

            return result
        except Exception as ex:
            self.logger.error(f"Exception in set_feature: {ex}")
            return None

    def get_feature(self, fid, nsid=0, sel=0):
        """
        Get an NVMe feature value via the admin passthru interface.

        Args:
            fid (int): Feature Identifier (FID).
            nsid (int): Namespace ID. Set to 0 for controller-wide features.
            sel (int): Select which value to retrieve (CDW10 bits 8-9):
                       0 = Current, 1 = Default, 2 = Saved, 3 = Supported capabilities.

        Returns:
            str or None: Command output or None on failure.
        """

        try:
            # CDW10: Bits 0–7 = FID, Bits 8–9 = SEL
            cdw10 = (fid & 0xFF) | ((sel & 0x3) << 8)

            _, cqe_output = self.admin_passthru(
                opcode=ADMIN_CMD_OPCODE_GETFEATURES,
                nsid=nsid,
                cdw10=cdw10,
                read=True
            )

            if cqe_output is None:
                self.logger.error("No output from get_feature admin_passthru command.")
                return None
        
            return self._parse_feature(fid, cqe_output)
        
        except Exception as ex:
            self.logger.error(f"Exception in get_feature: {ex}")
            return None
    

    def _parse_feature(self, fid, cmd_result):
        """
        Decode known NVMe features into a human-readable dict.

        Args:
            fid (int): Feature Identifier.
            cmd_result (str | bytes): Raw output from the device.

        Returns:
            dict: Parsed feature fields.
        """

        # For Get Feature, parse DWORD0 from stderr CQE result
        dword0 = self._parse_cqe_result(cmd_result)
        if dword0 is None:
            self.logger.error("Failed to parse CQE DWORD0 result from stderr.")
            return None

        parsers = {
            0x04: self._parse_temperature_threshold_feature,
        }

        if fid in parsers:
            try:
                return parsers[fid](dword0)
            except Exception as ex:
                self.logger.error(f"Exception parsing feature {fid}: {ex}")
                return None
        else:
            # For unknown features, just return the raw DWORD0 hex
            return {"raw_dword0": hex(dword0)}
        
    def _parse_temperature_threshold_feature(self, dword0):
        """
        Parse Temperature Threshold (FID = 0x04).
        Returns the threshold in both Kelvin and Celsius.
        """

        try:
            temp_threshold = dword0 & 0xFFFF               # Temperature Threshold (TMPTH)-> bits 15:0
            threshold_temp_sel = (dword0 >> 16) & 0xF      # Threshold Temperature Select (TMPSEL)-> bits 19:16
            threshold_type_sel = (dword0 >> 20) & 0x3      # Threshold Type Select (THSEL) -> bits 21:20
            temp_threshold_hyst = (dword0 >> 22) & 0x7     # Temperature Threshold Hysteresis (TMPTHH) -> bits 24:22

            temperature_threshold_dict = {
                "tmpth": temp_threshold,
                "tmpsel": threshold_temp_sel,
                "thsel": threshold_type_sel,
                "tmpthh": temp_threshold_hyst
            }
        
            return json.dumps(temperature_threshold_dict, indent=2)
        except Exception as ex:
            self.logger.error(f"Exception parsing temperature threshold feature: {ex}")
            return None

"""
DEMO: How to use the admin-passthru wrapper

logger = LogManager("admin-passthru-test").get_logger()
admin = AdminCommands(device="/dev/nvme0", logger=logger)

out = admin.get_feature(fid=4)
print(out)
out = admin.id_ctrl()
print(out)
out = admin.id_ns()
print(out)
out = admin.smart_log()
print(out)
"""