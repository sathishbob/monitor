# Build Directory

This directory contains all build-related files and scripts for the Lab Server Monitoring Agent.

## Directory Structure

```
build/
├── dist/                    # Built binaries (monitor-agent, monitor-agent.exe)
├── monitor-agent/          # PyInstaller build artifacts
├── scripts/                # Build scripts
│   ├── build.sh           # Linux build script
│   └── build_windows.ps1  # Windows build script
├── monitor-agent.spec     # PyInstaller specification file
└── README.md              # This file
```

## Building the Agent

### Linux
```bash
# From build directory
./build.sh

# Or directly from build/scripts
cd scripts && ./build.sh
```

### Windows
```powershell
# From build directory
powershell -ExecutionPolicy Bypass -File build_windows.ps1

# Or directly from build/scripts
cd scripts && .\build_windows.ps1
```

## Output

Built binaries will be placed in `build/dist/`:
- `monitor-agent` (Linux executable)
- `monitor-agent.exe` (Windows executable)

## Notes

- All build scripts are now located in the build directory
- PyInstaller build artifacts are stored in `monitor-agent/`
- The spec file is located at `monitor-agent.spec`
- Service scripts (`run_service.sh`, `run_service_windows.ps1`) automatically detect and use built binaries from `dist/`
