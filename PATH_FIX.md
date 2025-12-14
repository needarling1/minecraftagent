# Path Fix for Absolute Paths

## Problem
The agents were using relative paths (`./task_configs`, `./auto_eval/criteria_files`), which break when running from different directories or in multiprocessing contexts.

## Solution
Changed all paths to be absolute, calculated relative to the script location using `Path(__file__).parent.parent.absolute()`.

## Files Changed

### 1. green_agent/agent.py
- Line 173-184: `MinecraftGreenAgentExecutor.__init__` - Use absolute paths
- Line 314-319: `start_green_agent` - Default parameters to None
- Line 246-249: Save video with absolute path

### 2. white_agent/agent.py
- Line 41-50: `MinecraftWhiteAgentExecutor.__init__` - Use absolute paths
- Line 352-356: `start_white_agent` - Default parameter to None

### 3. utils/task_utils.py
- Line 39: `find_task_config` - Default parameter to None
- Line 51-54: Calculate absolute path if None
- Line 62: `list_available_tasks` - Default parameter to None
- Line 73-76: Calculate absolute path if None

## Quick Fix Commands for Ubuntu Machine

```bash
cd ~/dev/minecraftagent

# Backup files
cp green_agent/agent.py green_agent/agent.py.backup
cp white_agent/agent.py white_agent/agent.py.backup
cp utils/task_utils.py utils/task_utils.py.backup

# Download or copy the fixed files from Mac
# Then test:
python main.py launch --task-name collect_wood --difficulty simple
```

## What Changed

**Before:**
```python
def __init__(self, task_configs_dir: str = "./task_configs"):
    self.task_configs_dir = Path(task_configs_dir)
```

**After:**
```python
def __init__(self, task_configs_dir: str = None):
    if task_configs_dir is None:
        script_dir = Path(__file__).parent.parent.absolute()
        task_configs_dir = script_dir / "task_configs"
    self.task_configs_dir = Path(task_configs_dir)
```

This ensures paths always work regardless of:
- Current working directory
- How the script is invoked
- Multiprocessing contexts
- Different machines

## Testing

After applying the fix:
```bash
# Should now work from any directory
cd /tmp
python ~/dev/minecraftagent/main.py launch --task-name collect_wood

# Should find all files correctly
python ~/dev/minecraftagent/main.py list-tasks --difficulty simple
```
