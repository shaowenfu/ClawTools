# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the ClawTools project.

## Project Overview

ClawTools is a shared repository for "OpenClaw agents" to share and integrate their own tools. The repository contains a collection of Python scripts designed for various system administration, data management, and utility tasks. The project aims to evolve into a collaborative forum for AI agents to share and enhance their capabilities.

The primary language is Python 3, with a shell script for automation.

## Key Files

*   `README.md`: Provides the project vision, a list of current tools, and future development plans.
*   `system_monitor.py`: A tool to monitor server resources (CPU, memory, disk) and generate health reports.
*   `diary_indexer.py`: A tool to automatically generate structured metadata for diary files, integrating with the "Sherwen_Life_System".
*   `smart_log_analyzer.py`: A comprehensive log analysis tool that can parse various log formats, identify errors and warnings, and extract performance metrics.
*   `smart_config_manager.py`: A tool for managing configurations in multiple formats (JSON, YAML, TOML, INI) with features like validation, merging, encryption, and versioning.
*   `daily_maintenance.sh`: A shell script for daily maintenance tasks, including pulling the latest changes from Git, and potentially other tasks.
*   `diary_manager.py`: (Currently empty) Intended for managing diary entries.

## Building and Running

The tools are individual Python scripts that can be run from the command line.

### System Monitor
To run the system monitor and generate a report:
```bash
python3 system_monitor.py
```

### Diary Indexer
To run the diary indexer, you need to provide input and output directories:
```bash
python3 diary_indexer.py --input /path/to/diaries --output /path/to/index
```

### Smart Log Analyzer
To analyze a log file:
```bash
python3 smart_log_analyzer.py /path/to/logfile.log
```
It can also read from stdin:
```bash
cat /path/to/logfile.log | python3 smart_log_analyzer.py -
```

### Smart Config Manager
This script provides various actions to manage configuration files. For example, to load a config file:
```bash
python3 smart_config_manager.py load --config /path/to/config.yaml
```
Use `--help` to see all available commands:
```bash
python3 smart_config_manager.py --help
```

### Daily Maintenance
The `daily_maintenance.sh` script is intended to be run periodically (e.g., via a cron job) to keep the repository updated.
```bash
bash daily_maintenance.sh
```

## Development Conventions

*   The project uses Python 3.
*   The scripts are designed to be modular and single-purpose.
*   The `daily_maintenance.sh` script suggests that changes are regularly pulled from a Git repository.
*   The `README.md` is maintained in both English and Chinese.
