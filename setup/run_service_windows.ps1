Param(
  [string]$WorkingDir
)

$ErrorActionPreference = 'Stop'

if (-not $WorkingDir) {
  $WorkingDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
Set-Location $WorkingDir

# Prefer compiled binary if present, else venv python, else system python
$binPath = Join-Path $WorkingDir '..\build\dist\monitor-agent.exe'
$pyExe = Join-Path $WorkingDir '..\venv\Scripts\python.exe'
$useBinary = Test-Path $binPath

if ($useBinary) {
  $cmd = @($binPath)
} elseif (Test-Path $pyExe) {
  $cmd = @($pyExe, (Join-Path $WorkingDir '..\monitor_agent.py'))
} else {
  $cmd = @('python', (Join-Path $WorkingDir '..\monitor_agent.py'))
}

# Required args
$esHost   = $env:ES_HOST   ; if (-not $esHost)   { $esHost = 'http://localhost:9200' }
$esIndex  = $env:ES_INDEX  ; if (-not $esIndex)  { $esIndex = 'lab_monitoring' }
$interval = $env:INTERVAL  ; if (-not $interval) { $interval = '30' }
$ignore   = $env:IGNORE_USERS; if (-not $ignore) { $ignore = 'system root Administrator SYSTEM' }

# Security args
$monitorApiKey = $env:MONITOR_API_KEY
$monitorAllowedCommands = $env:MONITOR_ALLOWED_COMMANDS
$monitorBindHost = $env:MONITOR_BIND_HOST; if (-not $monitorBindHost) { $monitorBindHost = '127.0.0.1' }
$enableRemoteExec = $env:ENABLE_REMOTE_EXEC; if (-not $enableRemoteExec) { $enableRemoteExec = 'false' }
$monitorRateLimit = $env:MONITOR_RATE_LIMIT; if (-not $monitorRateLimit) { $monitorRateLimit = '10' }

$argsList = @('--es_host', $esHost, '--es_index', $esIndex, '--interval', $interval, '--ignore_users')
$argsList += $ignore.Split(' ')

# Auth
if ($env:ES_USER) { $argsList += @('--es_user', $env:ES_USER) }
if ($env:ES_PASS) { $argsList += @('--es_pass', $env:ES_PASS) }
if ($env:ES_API_KEY) { $argsList += @('--es_api_key', $env:ES_API_KEY) }

# TLS
if ($env:ES_CA_CERTS) { $argsList += @('--es_ca_certs', $env:ES_CA_CERTS) }
if ($env:ES_INSECURE -and @('1','true','TRUE','yes','YES') -contains $env:ES_INSECURE) { $argsList += '--es_insecure' }
if ($env:ES_SSL_ASSERT_HOSTNAME) { $argsList += @('--es_ssl_assert_hostname', $env:ES_SSL_ASSERT_HOSTNAME) }
if ($env:ES_SSL_ASSERT_FINGERPRINT) { $argsList += @('--es_ssl_assert_fingerprint', $env:ES_SSL_ASSERT_FINGERPRINT) }

# Timeout / refresh / port
if ($env:ES_TIMEOUT) { $argsList += @('--es_timeout', $env:ES_TIMEOUT) }
if ($env:ES_REFRESH) { $argsList += @('--es_refresh', $env:ES_REFRESH) }
if ($env:AGENT_PORT) { $argsList += @('--listen_port', $env:AGENT_PORT) }

# Cross-index scoring
if ($env:CMD_SCORE_INDEX_PATTERN) { $argsList += @('--cmd_score_index_pattern', $env:CMD_SCORE_INDEX_PATTERN) }

# Security parameters
if ($monitorApiKey) { $argsList += @('--api-key', $monitorApiKey) }
if ($monitorAllowedCommands) { $argsList += @('--allowed-commands') + $monitorAllowedCommands.Split(' ') }
if ($monitorBindHost) { $argsList += @('--bind-host', $monitorBindHost) }
if ($enableRemoteExec -and @('1','true','TRUE','yes','YES') -contains $enableRemoteExec) { $argsList += '--enable-remote-exec' }
if ($monitorRateLimit) { $argsList += @('--rate-limit', $monitorRateLimit) }

# Launch in the foreground (SCM will supervise via NSSM)
& $cmd @argsList
exit $LASTEXITCODE


