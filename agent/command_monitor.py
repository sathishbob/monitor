"""
Command Monitor Module - Command Execution Monitoring and Security Analysis

This module provides comprehensive monitoring of command execution activities in lab
server environments. It tracks command patterns, identifies potentially dangerous
commands, and provides security analysis to protect against malicious activities.

Key Features:
- Real-time command execution monitoring
- Dangerous command detection and alerting
- Command pattern analysis and scoring
- Security risk assessment
- Command history tracking and analysis
- Integration with engagement scoring system
- Compliance and audit trail generation

The module works in conjunction with the engagement scoring system to provide
comprehensive command behavior analysis and security monitoring.
"""

import logging
import re
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

# Set up module-level logging
logger = logging.getLogger(__name__)

class CommandMonitor:
    """
    Command execution monitoring and security analysis system.
    
    This class provides comprehensive monitoring of command execution activities
    including pattern analysis, security risk assessment, and dangerous command
    detection. It integrates with the engagement scoring system to provide
    behavioral analysis and security insights.
    
    The monitor supports:
    - Real-time command execution tracking
    - Dangerous command identification and alerting
    - Command pattern analysis and scoring
    - Security risk assessment and reporting
    - Command history management and analysis
    - Integration with external security systems
    - Compliance and audit trail generation
    
    All command data is analyzed for security risks and can be used for
    threat detection, compliance monitoring, and user behavior analysis.
    """
    
    def __init__(self, max_history_size: int = 1000):
        """
        Initialize the command monitor.
        
        Args:
            max_history_size (int): Maximum number of commands to retain in history
        """
        # Configuration for command monitoring and analysis
        self.max_history_size = max_history_size
        
        # Command history and tracking
        # Complete command execution history with metadata
        self.command_history: List[Dict[str, Any]] = []
        # Command history per user for individual analysis
        self.user_command_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        
        # Security analysis and risk assessment
        # Known dangerous commands and their risk levels
        self.dangerous_commands = {
            'rm -rf': {'risk_level': 'critical', 'description': 'Recursive file deletion'},
            'dd if=/dev/zero': {'risk_level': 'critical', 'description': 'Disk overwrite'},
            'mkfs': {'risk_level': 'high', 'description': 'Filesystem formatting'},
            'fdisk': {'risk_level': 'high', 'description': 'Disk partitioning'},
            'chmod 777': {'risk_level': 'high', 'description': 'Excessive permissions'},
            'chown root': {'risk_level': 'high', 'description': 'Ownership change to root'},
            'sudo su': {'risk_level': 'medium', 'description': 'Privilege escalation'},
            'wget': {'risk_level': 'medium', 'description': 'File download'},
            'curl': {'risk_level': 'medium', 'description': 'File download'},
            'nc -l': {'risk_level': 'medium', 'description': 'Network listener'},
            'python -c': {'risk_level': 'medium', 'description': 'Code execution'},
            'eval': {'risk_level': 'high', 'description': 'Command evaluation'},
            'exec': {'risk_level': 'high', 'description': 'Command execution'}
        }
        
        # Command pattern analysis
        # Regular expressions for identifying command patterns
        self.command_patterns = {
            'file_operations': r'\b(rm|cp|mv|ln|chmod|chown|touch|mkdir|rmdir)\b',
            'system_operations': r'\b(systemctl|service|init|telinit|shutdown|reboot|halt)\b',
            'network_operations': r'\b(ssh|scp|rsync|wget|curl|nc|netcat|telnet|ftp)\b',
            'process_operations': r'\b(kill|pkill|killall|nice|renice|nohup|screen|tmux)\b',
            'privilege_operations': r'\b(sudo|su|doas|pkexec|runuser)\b',
            'development_tools': r'\b(gcc|make|cmake|git|svn|docker|kubectl)\b',
            'monitoring_tools': r'\b(top|htop|iotop|nethogs|iftop|tcpdump|wireshark)\b'
        }
        
        # Risk scoring and assessment
        # Risk scoring weights for different command categories
        self.risk_weights = {
            'dangerous_commands': 10.0,
            'privilege_escalation': 8.0,
            'file_operations': 3.0,
            'system_operations': 5.0,
            'network_operations': 4.0,
            'process_operations': 2.0,
            'development_tools': 1.0,
            'monitoring_tools': 2.0
        }
        
        # Alert and notification system
        # Active security alerts and notifications
        self.active_alerts: List[Dict[str, Any]] = []
        # Security event statistics and metrics
        self.security_metrics: Dict[str, int] = defaultdict(int)
        
        logger.info("Command monitor initialized with max history size: %d", max_history_size)
    
    def monitor_command(self, username: str, command: str, working_directory: str = None, 
                       exit_code: int = None, execution_time: float = None) -> Dict[str, Any]:
        """
        Monitor and analyze a command execution.
        
        Args:
            username (str): Username who executed the command
            command (str): The command that was executed
            working_directory (str, optional): Working directory where command was executed
            exit_code (int, optional): Exit code of the command
            execution_time (float, optional): Time taken to execute the command
            
        Returns:
            Dict[str, Any]: Command analysis results with security assessment
        """
        try:
            # Get current timestamp for command execution
            timestamp = datetime.now(timezone.utc)
            
            # Analyze command for security risks
            security_analysis = self._analyze_command_security(command)
            
            # Calculate command risk score
            risk_score = self._calculate_risk_score(security_analysis)
            
            # Generate command hash for deduplication
            command_hash = self._generate_command_hash(command, username, working_directory)
            
            # Create command record with comprehensive metadata
            command_record = {
                'timestamp': timestamp.isoformat(),
                'username': username,
                'command': command,
                'working_directory': working_directory,
                'exit_code': exit_code,
                'execution_time': execution_time,
                'command_hash': command_hash,
                'security_analysis': security_analysis,
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score)
            }
            
            # Store command in history
            self._store_command(command_record)
            
            # Update user command history
            self.user_command_history[username].append(command_record)
            
            # Check for security alerts
            if risk_score > 5.0:  # Medium risk threshold
                self._create_security_alert(command_record)
            
            # Update security metrics
            self._update_security_metrics(security_analysis)
            
            logger.debug("Command monitored for user %s: %s (risk score: %.2f)", 
                        username, command[:50], risk_score)
            
            return command_record
            
        except Exception as e:
            logger.error("Error monitoring command for user %s: %s", username, e)
            return {}
    
    def _analyze_command_security(self, command: str) -> Dict[str, Any]:
        """
        Analyze command for security risks and patterns.
        
        Args:
            command (str): Command to analyze
            
        Returns:
            Dict[str, Any]: Security analysis results
        """
        try:
            analysis = {
                'is_dangerous': False,
                'dangerous_command_type': None,
                'risk_factors': [],
                'command_patterns': [],
                'privilege_escalation': False,
                'file_operations': False,
                'network_operations': False,
                'system_operations': False
            }
            
            # Check for dangerous commands
            for dangerous_cmd, details in self.dangerous_commands.items():
                if dangerous_cmd in command:
                    analysis['is_dangerous'] = True
                    analysis['dangerous_command_type'] = dangerous_cmd
                    analysis['risk_factors'].append(f"Dangerous command: {details['description']}")
                    break
            
            # Analyze command patterns
            for pattern_name, pattern_regex in self.command_patterns.items():
                if re.search(pattern_regex, command, re.IGNORECASE):
                    analysis['command_patterns'].append(pattern_name)
                    
                    # Set specific flags based on pattern matches
                    if pattern_name == 'privilege_operations':
                        analysis['privilege_escalation'] = True
                    elif pattern_name == 'file_operations':
                        analysis['file_operations'] = True
                    elif pattern_name == 'network_operations':
                        analysis['network_operations'] = True
                    elif pattern_name == 'system_operations':
                        analysis['system_operations'] = True
            
            # Check for additional security risks
            if 'sudo' in command and 'rm' in command:
                analysis['risk_factors'].append("Sudo with destructive command")
            
            if 'eval' in command or 'exec' in command:
                analysis['risk_factors'].append("Dynamic command evaluation")
            
            if '>' in command and '/dev/' in command:
                analysis['risk_factors'].append("Device file redirection")
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing command security: %s", e)
            return {}
    
    def _calculate_risk_score(self, security_analysis: Dict[str, Any]) -> float:
        """
        Calculate risk score based on security analysis.
        
        Args:
            security_analysis (Dict[str, Any]): Security analysis results
            
        Returns:
            float: Calculated risk score (0.0 to 10.0)
        """
        try:
            risk_score = 0.0
            
            # Base risk from dangerous commands
            if security_analysis.get('is_dangerous', False):
                risk_score += self.risk_weights['dangerous_commands']
            
            # Risk from command patterns
            for pattern in security_analysis.get('command_patterns', []):
                if pattern in self.risk_weights:
                    risk_score += self.risk_weights[pattern]
            
            # Additional risk factors
            if security_analysis.get('privilege_escalation', False):
                risk_score += self.risk_weights['privilege_escalation']
            
            # Cap risk score at maximum
            risk_score = min(risk_score, 10.0)
            
            return risk_score
            
        except Exception as e:
            logger.error("Error calculating risk score: %s", e)
            return 0.0
    
    def _get_risk_level(self, risk_score: float) -> str:
        """
        Get risk level based on risk score.
        
        Args:
            risk_score (float): Calculated risk score
            
        Returns:
            str: Risk level (low, medium, high, critical)
        """
        if risk_score >= 8.0:
            return 'critical'
        elif risk_score >= 5.0:
            return 'high'
        elif risk_score >= 2.0:
            return 'medium'
        else:
            return 'low'
    
    def _generate_command_hash(self, command: str, username: str, working_directory: str = None) -> str:
        """
        Generate unique hash for command identification.
        
        Args:
            command (str): Command string
            username (str): Username who executed the command
            working_directory (str, optional): Working directory
            
        Returns:
            str: SHA-256 hash of command data
        """
        try:
            # Create unique identifier from command components
            command_data = f"{command}|{username}|{working_directory or ''}"
            return hashlib.sha256(command_data.encode()).hexdigest()
            
        except Exception as e:
            logger.error("Error generating command hash: %s", e)
            return ""
    
    def _store_command(self, command_record: Dict[str, Any]) -> None:
        """
        Store command record in history.
        
        Args:
            command_record (Dict[str, Any]): Command record to store
        """
        try:
            # Add to main command history
            self.command_history.append(command_record)
            
            # Maintain history size limit
            if len(self.command_history) > self.max_history_size:
                self.command_history.pop(0)
                
        except Exception as e:
            logger.error("Error storing command record: %s", e)
    
    def _create_security_alert(self, command_record: Dict[str, Any]) -> None:
        """
        Create security alert for high-risk command.
        
        Args:
            command_record (Dict[str, Any]): Command record that triggered alert
        """
        try:
            alert = {
                'timestamp': command_record['timestamp'],
                'username': command_record['username'],
                'command': command_record['command'],
                'risk_score': command_record['risk_score'],
                'risk_level': command_record['risk_level'],
                'working_directory': command_record['working_directory'],
                'security_analysis': command_record['security_analysis']
            }
            
            self.active_alerts.append(alert)
            
            logger.warning("Security alert created for user %s: %s (risk: %s)", 
                          command_record['username'], command_record['command'][:50], 
                          command_record['risk_level'])
                          
        except Exception as e:
            logger.error("Error creating security alert: %s", e)
    
    def _update_security_metrics(self, security_analysis: Dict[str, Any]) -> None:
        """
        Update security metrics based on analysis results.
        
        Args:
            security_analysis (Dict[str, Any]): Security analysis results
        """
        try:
            # Update pattern-based metrics
            for pattern in security_analysis.get('command_patterns', []):
                self.security_metrics[f"pattern_{pattern}"] += 1
            
            # Update risk-based metrics
            if security_analysis.get('is_dangerous', False):
                self.security_metrics['dangerous_commands'] += 1
            
            if security_analysis.get('privilege_escalation', False):
                self.security_metrics['privilege_escalation'] += 1
            
            # Update total commands metric
            self.security_metrics['total_commands'] += 1
            
        except Exception as e:
            logger.error("Error updating security metrics: %s", e)
    
    def get_command_summary(self, username: str = None) -> Dict[str, Any]:
        """
        Get summary of command monitoring data.
        
        Args:
            username (str, optional): Specific username to get summary for
            
        Returns:
            Dict[str, Any]: Command monitoring summary
        """
        try:
            if username:
                # User-specific summary
                user_commands = self.user_command_history.get(username, [])
                return {
                    'username': username,
                    'total_commands': len(user_commands),
                    'recent_commands': list(user_commands)[-10:],  # Last 10 commands
                    'risk_distribution': self._get_risk_distribution(user_commands),
                    'command_patterns': self._get_pattern_distribution(user_commands)
                }
            else:
                # Overall summary
                return {
                    'total_commands': len(self.command_history),
                    'active_alerts': len(self.active_alerts),
                    'security_metrics': dict(self.security_metrics),
                    'risk_distribution': self._get_risk_distribution(self.command_history),
                    'command_patterns': self._get_pattern_distribution(self.command_history),
                    'recent_alerts': self.active_alerts[-10:] if self.active_alerts else []
                }
                
        except Exception as e:
            logger.error("Error generating command summary: %s", e)
            return {}
    
    def _get_risk_distribution(self, commands: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get distribution of risk levels in command list.
        
        Args:
            commands (List[Dict[str, Any]]): List of command records
            
        Returns:
            Dict[str, int]: Count of commands by risk level
        """
        try:
            distribution = defaultdict(int)
            for command in commands:
                risk_level = command.get('risk_level', 'unknown')
                distribution[risk_level] += 1
            return dict(distribution)
            
        except Exception as e:
            logger.error("Error calculating risk distribution: %s", e)
            return {}
    
    def _get_pattern_distribution(self, commands: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get distribution of command patterns in command list.
        
        Args:
            commands (List[Dict[str, Any]]): List of command records
            
        Returns:
            Dict[str, int]: Count of commands by pattern type
        """
        try:
            distribution = defaultdict(int)
            for command in commands:
                patterns = command.get('security_analysis', {}).get('command_patterns', [])
                for pattern in patterns:
                    distribution[pattern] += 1
            return dict(distribution)
            
        except Exception as e:
            logger.error("Error calculating pattern distribution: %s", e)
            return {}
    
    def get_linux_commands(self) -> List[Dict[str, Any]]:
        """Get completed commands with durations from Linux auditd."""
        completed_commands: List[Dict[str, Any]] = []
        try:
            import subprocess
            import os
            import platform
            import psutil
            
            # Check if auditd is running
            result = subprocess.run(['systemctl', 'is-active', 'auditd'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.debug("Auditd is not running, cannot collect commands")
                return completed_commands
            
            # Read audit log
            audit_log_path = '/var/log/audit/audit.log'
            if not os.path.exists(audit_log_path):
                logger.debug("Audit log not found at %s", audit_log_path)
                return completed_commands
            
            # Read only new lines since last read
            try:
                with open(audit_log_path, 'rb') as f:
                    st = os.fstat(f.fileno())
                    inode = st.st_ino
                    if not hasattr(self, '_audit_last_inode') or self._audit_last_inode != inode or getattr(self, '_audit_last_pos', 0) > st.st_size:
                        self._audit_last_inode = inode
                        self._audit_last_pos = 0
                    f.seek(self._audit_last_pos)
                    data = f.read()
                    self._audit_last_pos = f.tell()
                
                text = data.decode(errors='ignore')
                
                # Parse audit log entries
                event_cmd: Dict[str, str] = {}
                event_meta: Dict[str, Dict[str, Any]] = {}
                id_regex = re.compile(r'audit\([^)]*:(\d+)\)')
                
                for line in text.splitlines():
                    if not line.strip():
                        continue
                    
                    # Extract audit ID
                    id_match = id_regex.search(line)
                    if not id_match:
                        continue
                    
                    audit_id = id_match.group(1)
                    
                    # Parse EXECVE events
                    if 'type=EXECVE' in line:
                        # Extract command and arguments
                        cmd_match = re.search(r'argc=(\d+)', line)
                        if cmd_match:
                            argc = int(cmd_match.group(1))
                            args = []
                            for i in range(argc):
                                arg_match = re.search(rf'a{i}="([^"]*)"', line)
                                if arg_match:
                                    args.append(arg_match.group(1))
                            
                            if args:
                                command = ' '.join(args)
                                event_cmd[audit_id] = command
                    
                    # Parse SYSCALL events for metadata
                    elif 'type=SYSCALL' in line:
                        # Extract user info
                        uid_match = re.search(r'uid=(\d+)', line)
                        pid_match = re.search(r'pid=(\d+)', line)
                        ppid_match = re.search(r'ppid=(\d+)', line)
                        
                        if uid_match and pid_match:
                            event_meta[audit_id] = {
                                'uid': int(uid_match.group(1)),
                                'pid': int(pid_match.group(1)),
                                'ppid': int(ppid_match.group(1)) if ppid_match else None
                            }
                
                # Correlate commands with metadata and get execution time
                for audit_id, command in event_cmd.items():
                    if audit_id in event_meta:
                        meta = event_meta[audit_id]
                        
                        # Get username from UID
                        try:
                            import pwd
                            username = pwd.getpwuid(meta['uid']).pw_name
                        except (KeyError, OSError):
                            username = f"uid_{meta['uid']}"
                        
                        # Try to get execution time from process info
                        execution_time = None
                        try:
                            # Check if process is still running
                            if psutil.pid_exists(meta['pid']):
                                try:
                                    proc = psutil.Process(meta['pid'])
                                    # Get process creation time and current time
                                    create_time = proc.create_time()
                                    current_time = time.time()
                                    execution_time = current_time - create_time
                                    # Cap execution time at reasonable maximum
                                    execution_time = min(execution_time, 300)  # 5 minutes max
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    # Process might have finished, estimate execution time
                                    execution_time = 0.1  # Default short execution time
                            else:
                                # Process has finished, estimate execution time based on command type
                                if any(cmd in command.lower() for cmd in ['sleep', 'wait', 'ping', 'curl', 'wget']):
                                    execution_time = 1.0  # Longer commands
                                elif any(cmd in command.lower() for cmd in ['ls', 'pwd', 'echo', 'cat', 'head', 'tail']):
                                    execution_time = 0.1  # Quick commands
                                else:
                                    execution_time = 0.5  # Medium commands
                        except Exception:
                            execution_time = 0.1  # Default fallback
                        
                        # Check if command is dangerous
                        dangerous = self._analyze_command_security(command).get('is_dangerous', False)
                        
                        completed_commands.append({
                            'command': command,
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'user': username,
                            'uid': meta['uid'],
                            'pid': meta['pid'],
                            'ppid': meta['ppid'],
                            'dangerous': dangerous,
                            'audit_id': audit_id,
                            'execution_time': execution_time,
                            'duration_seconds': execution_time
                        })
                
                logger.debug("Collected %d commands from audit log", len(completed_commands))
                
            except Exception as e:
                logger.error("Error reading audit log: %s", e)
                
        except Exception as e:
            logger.error("Error collecting Linux commands: %s", e)
            
        return completed_commands
    
    def get_windows_commands(self) -> List[Dict[str, Any]]:
        """Get commands from Windows Event Logs with enhanced details."""
        commands = []
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                # PowerShell script to get detailed process creation events
                ps_script = '''
                $events = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4688} -MaxEvents 50 -ErrorAction SilentlyContinue
                $results = @()
                
                foreach ($event in $events) {
                    try {
                        $xml = [xml]$event.ToXml()
                        $eventData = $xml.Event.EventData.Data
                        
                        $commandLine = ($eventData | Where-Object {$_.Name -eq 'CommandLine'}).'#text'
                        $newProcessName = ($eventData | Where-Object {$_.Name -eq 'NewProcessName'}).'#text'
                        $userName = ($eventData | Where-Object {$_.Name -eq 'SubjectUserName'}).'#text'
                        $domain = ($eventData | Where-Object {$_.Name -eq 'SubjectDomainName'}).'#text'
                        $processId = ($eventData | Where-Object {$_.Name -eq 'NewProcessId'}).'#text'
                        
                        # Only add if we have meaningful data
                        if ($newProcessName -and $userName) {
                            $results += [PSCustomObject]@{
                                CommandLine = $commandLine
                                ProcessName = $newProcessName
                                UserName = "$domain\\$userName"
                                ProcessId = $processId
                                TimeCreated = $event.TimeCreated.ToString('o')
                            }
                        }
                    } catch {
                        # Skip malformed events
                        continue
                    }
                }
                
                $results | ConvertTo-Json -Compress
                '''
                
                result = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', ps_script],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    import json
                    data = json.loads(result.stdout)
                    
                    # Handle both single object and array
                    if not isinstance(data, list):
                        data = [data]
                    
                    for item in data:
                        command_line = item.get('CommandLine', '') or item.get('ProcessName', '')
                        process_name = item.get('ProcessName', '')
                        username = item.get('UserName', 'unknown')
                        process_id = item.get('ProcessId', '0')
                        timestamp_str = item.get('TimeCreated', datetime.now(timezone.utc).isoformat())
                        
                        # Try to parse timestamp
                        try:
                            if 'T' in timestamp_str and '+' in timestamp_str:
                                timestamp = datetime.fromisoformat(timestamp_str)
                            else:
                                timestamp = datetime.now(timezone.utc)
                        except:
                            timestamp = datetime.now(timezone.utc)
                        
                        # Analyze if command is dangerous
                        dangerous = self._analyze_command_security(command_line).get('is_dangerous', False)
                        
                        # Estimate execution time (0.1 default for Windows)
                        execution_time = 0.1
                        if any(slow_cmd in command_line.lower() for slow_cmd in ['build', 'compile', 'test', 'deploy', 'backup']):
                            execution_time = 5.0
                        
                        commands.append({
                            'command': command_line,
                            'timestamp': timestamp.isoformat(),
                            'user': username,
                            'pid': int(process_id) if process_id.isdigit() else 0,
                            'process_name': process_name,
                            'dangerous': dangerous,
                            'execution_time': execution_time,
                            'duration_seconds': execution_time
                        })
                    
                    logger.info(f"Retrieved {len(commands)} commands from Windows Event Logs")
                
        except subprocess.TimeoutExpired:
            logger.error("PowerShell query timed out")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse PowerShell output: {e}")
        except Exception as e:
            logger.error(f"Error reading Windows Event Logs: {e}")
            
    def get_recent_commands(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """Get commands from the last N minutes."""
        try:
            import platform
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            recent_commands = []
            
            # Get commands from appropriate log based on platform
            if platform.system() == "Linux":
                commands = self.get_linux_commands()
            elif platform.system() == "Windows":
                commands = self.get_windows_commands()
            else:
                commands = []
                logger.warning(f"Platform {platform.system()} not fully supported")
            
            for command in commands:
                try:
                    # Parse timestamp (handle both formats)
                    timestamp_str = command.get('timestamp', '')
                    if 'Z' in timestamp_str:
                        command_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    elif '+' in timestamp_str:
                        command_time = datetime.fromisoformat(timestamp_str)
                    else:
                        # If no timezone info, assume UTC
                        timestamp_str_clean = timestamp_str.rstrip('Z') + '+00:00'
                        command_time = datetime.fromisoformat(timestamp_str_clean)
                    
                    if command_time >= cutoff_time:
                        recent_commands.append(command)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error parsing timestamp {command.get('timestamp')}: {e}")
                    continue
            
            logger.debug("Found %d recent commands in last %d minutes", len(recent_commands), minutes)
            return recent_commands
            
        except Exception as e:
            logger.error("Error getting recent commands: %s", e)
            return []

    def clear_history(self) -> None:
        """Clear all command history and security data."""
        self.command_history.clear()
        self.user_command_history.clear()
        self.active_alerts.clear()
        self.security_metrics.clear()
        logger.info("Command monitor history cleared")


__all__ = ["CommandMonitor"]
