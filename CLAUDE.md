# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Auto Obsidian is an AI-powered learning note generator that automatically creates Markdown notes and saves them to an Obsidian vault with Git integration. The application is built with Python and PyQt5/PyQt6.

## Common Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Run with batch files (Windows)
run.bat          # Run the application
start.bat        # Run with virtual environment
```

### Building Executable
```bash
# Build to EXE using PyInstaller
build_exe.bat    # Windows build script
pyinstaller build_spec.py    # Direct build command
```

### Virtual Environment
```bash
setup_env.bat      # Create virtual environment
update_deps.bat    # Update dependencies
clean_env.bat      # Remove virtual environment
```

## Architecture

### Configuration Management

Configuration files are stored in the user's home directory at `~/.auto_obsidian/`:
- `config.yaml` - Main configuration (AI provider, API key, save paths)
- `topics.yaml` - Preset learning topics for batch generation
- `dir_history.json` - Directory selection history

The `ConfigPathManager` class (src/config_manager.py) handles configuration path management and automatic migration from the old `config/` directory. First-run initialization creates default topics.yaml.

**Note**: API keys are encrypted at rest using `crypto_utils.py`. Always use the crypto manager to encrypt/decrypt API keys.

### Core Components

**Note Generation Flow:**
1. `NoteGenerator` (src/note_generator.py) - Orchestrates AI providers to generate content
2. AI Providers (src/ai_providers/) - Abstract base class with implementations for ChatGLM and OpenAI
3. `FileManager` (src/file_manager.py) - Saves notes as Markdown with Obsidian frontmatter
4. `GitManager` (src/git_manager.py) - Automates git add/commit/push using subprocess
5. `NoteScheduler` (src/scheduler.py) - APScheduler-based automated batch generation
6. `NotificationManager` (src/notification_manager.py) - System tray notifications

**AI Provider Pattern:**
All AI providers inherit from `BaseAIProvider` (src/ai_providers/base.py) which defines:
- `generate(prompt, **kwargs)` - Raw text generation
- `generate_note(topic, language, style, **kwargs)` - Structured note generation with built-in prompt template

To add a new AI provider:
1. Create a new file in `src/ai_providers/` (e.g., `claude.py`)
2. Inherit from `BaseAIProvider` and implement the abstract methods
3. Add the provider to `NoteGenerator.PROVIDERS` dict in src/note_generator.py:19-22

### GUI Architecture

The application uses a tabbed interface with PyQt5/6 (PyQt5 is preferred for stability):

**Panels** (gui/):
- `main_window.py` - Main window initialization and manager orchestration
- `config_panel.py` - Configuration management
- `note_panel.py` - Manual note generation
- `scheduler_panel.py` - Scheduled task configuration
- `stats_panel.py` - Statistics dashboard

Key pattern: The main window initializes all managers (generator, file, git, scheduler) and passes them to panels via `initialize_managers()` in gui/main_window.py:147.

### Scheduler Architecture

`NoteScheduler` uses APScheduler's QtScheduler for thread-safe integration with PyQt:
- Jobs are triggered via `IntervalTrigger` for recurring execution
- The scheduler maintains execution history and statistics
- On completion, it calls the `on_job_complete` callback (connected to NotificationManager)
- Real-time logs are stored in `self.log_messages` (max 100 entries)

### Git Integration

The GitManager uses subprocess to call system git commands (more reliable than GitPython):
- `commit_and_push()` performs the full workflow: add → commit → push
- Git repository is auto-detected by searching upward for `.git` directory
- Commit messages support template variables: `{date}`, `{time}`, `{topic}`, `{count}`, etc.

## Important Implementation Details

### PyQt Version Compatibility
The codebase supports both PyQt5 and PyQt6. Import pattern:
```python
try:
    from PyQt5.QtWidgets import ...
    PYQT_VERSION = 5
except ImportError:
    from PyQt6.QtWidgets import ...
    PYQT_VERSION = 6
```

### File Naming Convention
Filenames are generated using the format specified in config (default: `{date}_{topic}`).
Invalid characters are sanitized in `FileManager._sanitize_filename()`.
Duplicate filenames get a numeric suffix (`_1`, `_2`, etc.).

### First-Run Detection
Check `ConfigPathManager.is_first_run()` which returns `True` if `~/.auto_obsidian/config.yaml` doesn't exist.
On first run, `ConfigPathManager.initialize_on_first_run()`:
1. Creates `~/.auto_obsidian/` directory
2. Migrates old config from `config/` if present
3. Creates default `topics.yaml` if not present
4. Does NOT create `config.yaml` (user must configure via GUI)

### Logging
Logs are written to `logs/auto_obsidian.log` and stdout. Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Testing AI Provider Changes

After modifying AI provider code:
1. Test connection via `NoteGenerator.test_connection()`
2. Generate a single note manually via the GUI
3. Check logs at `logs/auto_obsidian.log` for errors

## Modifying Scheduled Tasks

The scheduler supports three modes configured via GUI:
1. **Daily** - Executes at specified time, then every 24 hours
2. **Hourly** - Executes every N hours
3. **Interval** - Custom interval in hours

Tasks are stored in APScheduler and persist only while the application is running.
