# Code Architecture - Active vs. Legacy Components

This document clarifies which parts of the cs194 folder are actively used in the A2A implementation vs. legacy code from your previous work.

---

## ✅ ACTIVELY USED - New A2A Implementation

### Core Agents (NEW - December 2025)

```
green_agent/
├── agent.py                        ✅ ACTIVE - A2A server for evaluation
├── minecraft_green_agent.toml      ✅ ACTIVE - Agent card for discovery
└── __init__.py                     ✅ ACTIVE - Package exports
```
**Purpose**: Green agent (evaluator) with A2A protocol integration
**Used by**: AgentBeats platform, launcher.py, main.py

```
white_agent/
├── agent.py                        ✅ ACTIVE - MineStudio task executor
├── minecraft_white_agent.toml      ✅ ACTIVE - Agent card for discovery
└── __init__.py                     ✅ ACTIVE - Package exports
```
**Purpose**: White agent (task executor) with MineStudio integration
**Used by**: Green agent via A2A, launcher.py, main.py

### Utilities (NEW - December 2025)

```
utils/
├── a2a_utils.py                    ✅ ACTIVE - A2A protocol helpers
├── task_utils.py                   ✅ ACTIVE - Task config loading
└── __init__.py                     ✅ ACTIVE - Package exports
```
**Purpose**: A2A communication and YAML task config utilities
**Used by**: Both green and white agents

### Orchestration (NEW - December 2025)

```
launcher.py                         ✅ ACTIVE - Multi-agent orchestration
main.py                             ✅ ACTIVE - CLI entry point
```
**Purpose**: Start agents, coordinate evaluation, CLI interface
**Used by**: Direct user interaction

### Documentation (NEW - December 2025)

```
README.md                           ✅ ACTIVE - Project overview
SETUP.md                            ✅ ACTIVE - Setup guide
QUICKSTART.md                       ✅ ACTIVE - Quick start
IMPLEMENTATION_SUMMARY.md           ✅ ACTIVE - Technical summary
.env.example                        ✅ ACTIVE - Environment template
.gitignore                          ✅ ACTIVE - Git config
requirements.txt                    ✅ ACTIVE - Dependencies
```
**Purpose**: User documentation and configuration

---

## ✅ ACTIVELY USED - Shared from Previous Work

### Evaluation Module (EXISTING - from your original work)

```
auto_eval/
├── eval.py                         ✅ ACTIVE - Core VLM evaluation logic
├── criteria_files/                 ✅ ACTIVE - 82 task criteria
│   ├── collect_wood.txt           (Original)
│   ├── build_a_house.txt          (Copied from MCU)
│   └── ... (81 more from MCU)
├── prompt/                         ✅ ACTIVE - VLM prompts
│   ├── single_rating_prompt.txt   ✅ ACTIVE - Main evaluation prompt
│   ├── rule_system_prompt.txt
│   └── compare_rating_prompts.txt
└── vlm_rating_res/                 ✅ ACTIVE - Evaluation outputs
```
**Purpose**: VLM-based video evaluation
**Used by**: Green agent calls `eval.py` functions
**Note**: Your original `eval.py` is directly integrated into the green agent

### Task Configurations (EXISTING + NEW)

```
task_configs/
├── simple/                         ✅ ACTIVE - 82 simple tasks (from MCU)
├── hard/                           ✅ ACTIVE - 82 hard tasks (from MCU)
└── compositional/                  ✅ ACTIVE - 18 composite tasks (from MCU)
```
**Purpose**: YAML task definitions
**Used by**: White agent for task execution
**Note**: These were copied from MCU benchmark

### Output Directory (EXISTING)

```
output/                             ✅ ACTIVE - Video recordings
├── collect_wood/                   (Example existing)
├── find_forest/                    (Example existing)
└── ... (new tasks will create dirs here)
```
**Purpose**: Storage for generated videos
**Used by**: White agent saves videos here, green agent reads from here

---

## ⚠️ LEGACY CODE - Not Used in A2A Implementation

### Config Generation (LEGACY - October 2025)

```
config_generation/                  ⚠️ LEGACY - Not used
├── generate_atom_config.py         ⚠️ Not called
├── generate_com_config.py          ⚠️ Not called
├── atomic_task_list.txt            ⚠️ Not used
├── atomic_simple_system_prompt.txt ⚠️ Not used
├── atomic_hard_system_prompt.txt   ⚠️ Not used
└── composition_system_prompt.txt   ⚠️ Not used
```
**Original Purpose**: Generate task configs using GPT-4
**Why Not Used**: We copied pre-made task configs from MCU instead
**Can Delete?**: Yes, safe to remove if you don't need task generation

### Utility Scripts (LEGACY - October 2025)

```
utility/                            ⚠️ LEGACY - Not used
├── task_call.py                    ⚠️ Not called
├── record_call.py                  ⚠️ Not called
└── read_conf.py                    ⚠️ Not called
```
**Original Purpose**: Utilities for your old standalone evaluation
**Why Not Used**: Replaced by new `utils/` module
**Can Delete?**: Yes, functionality replaced by `utils/a2a_utils.py` and `utils/task_utils.py`

### Standalone Evaluation Scripts (PARTIALLY LEGACY)

```
auto_eval/
├── eval_individual.py              ⚠️ LEGACY - Not used in A2A flow
├── video_comparison.py             ⚠️ LEGACY - Not used in A2A flow
├── video_rating_example.py         ⚠️ LEGACY - Not used in A2A flow
└── README.md                       ⚠️ LEGACY - Old instructions
```
**Original Purpose**: Standalone CLI tools for manual evaluation
**Why Not Used**: Green agent handles evaluation automatically
**Can Delete?**: Optional - useful for debugging, but not part of A2A flow
**Note**: These still work independently if you want to test evaluation without agents

---

## 📊 Architecture Comparison

### OLD ARCHITECTURE (Your Original Setup)
```
Manual Workflow:
1. Manually run tasks → generate videos
2. Save videos to output/
3. Run eval.py manually on videos
4. Review JSON results
```

### NEW ARCHITECTURE (A2A Implementation)
```
Automated Workflow:
AgentBeats → Green Agent → White Agent → MineStudio
                 ↓              ↓
            eval.py        RecordCallback
                 ↓              ↓
            JSON scores ← video artifact
```

---

## 🔄 Code Reuse Map

| Original Component | New Usage | Notes |
|-------------------|-----------|-------|
| `auto_eval/eval.py` | ✅ Used by green agent | Core evaluation logic preserved |
| `auto_eval/prompt/` | ✅ Used by green agent | VLM prompts unchanged |
| `auto_eval/criteria_files/` | ✅ Extended (1→82 files) | Added MCU criteria |
| `task_configs/` | ✅ Extended (0→182 files) | Copied from MCU |
| `output/` | ✅ Used by both agents | Video storage location |
| `config_generation/` | ❌ Not used | Task generation scripts |
| `utility/` | ❌ Replaced | Old utils replaced by `utils/` |
| `auto_eval/eval_individual.py` | ❌ Standalone only | Not in A2A flow |

---

## 🗂️ Recommended Cleanup

### Safe to Delete (if you don't need them)

```bash
# Remove legacy config generation
rm -rf config_generation/

# Remove legacy utility scripts
rm -rf utility/

# Remove standalone evaluation scripts (optional)
rm auto_eval/eval_individual.py
rm auto_eval/video_comparison.py
rm auto_eval/video_rating_example.py
rm auto_eval/README.md  # Old instructions
```

### Keep These (actively used)

```bash
# Core agents
green_agent/
white_agent/

# Utilities
utils/

# Orchestration
launcher.py
main.py

# Evaluation
auto_eval/eval.py
auto_eval/criteria_files/
auto_eval/prompt/

# Data
task_configs/
output/

# Documentation
README.md
SETUP.md
QUICKSTART.md
IMPLEMENTATION_SUMMARY.md
.env.example
requirements.txt
```

---

## 🔍 How to Verify What's Used

### Check Import Dependencies

```bash
# Find all imports of legacy modules
cd /path/to/cs194
grep -r "from utility" . --include="*.py"
grep -r "from config_generation" . --include="*.py"
grep -r "import utility" . --include="*.py"
grep -r "import config_generation" . --include="*.py"
```

If these return nothing (except in the legacy files themselves), they're not used.

### Active Code Paths

**When you run `python main.py launch`:**

1. `main.py` → CLI entry
2. `launcher.py` → Orchestration
3. `green_agent/agent.py` → Green agent starts
4. `white_agent/agent.py` → White agent starts
5. `utils/a2a_utils.py` → A2A communication
6. `utils/task_utils.py` → Load task config
7. `white_agent/agent.py` → Execute task in MineStudio
8. `auto_eval/eval.py` → Green agent evaluates video
9. Results returned via A2A

**Never called:**
- `config_generation/*`
- `utility/*`
- `auto_eval/eval_individual.py`
- `auto_eval/video_comparison.py`

---

## 📝 Summary

### ✅ ACTIVE CODE (Use these)
- **green_agent/** - Green agent with A2A
- **white_agent/** - White agent with MineStudio
- **utils/** - A2A and task utilities
- **launcher.py** - Orchestration
- **main.py** - CLI interface
- **auto_eval/eval.py** - VLM evaluation (your original!)
- **auto_eval/criteria_files/** - Task criteria (extended)
- **task_configs/** - Task definitions (new)

### ⚠️ LEGACY CODE (Can remove)
- **config_generation/** - Old task generation scripts
- **utility/** - Replaced by `utils/`
- **auto_eval/eval_individual.py** - Standalone tool
- **auto_eval/video_comparison.py** - Standalone tool
- **auto_eval/video_rating_example.py** - Standalone tool

### 🔄 HYBRID (Existing + Enhanced)
- **auto_eval/** - Your evaluation logic is core, but standalone scripts are legacy
- **output/** - Used for video storage (both old and new)
- **task_configs/** - New addition (from MCU)

---

## 💡 Recommendation

**Minimal cleanup:**
```bash
# Keep working code, remove unused scripts
mv config_generation/ ../backup/
mv utility/ ../backup/
```

**Full cleanup:**
```bash
# Remove all legacy code
rm -rf config_generation/
rm -rf utility/
rm auto_eval/eval_individual.py
rm auto_eval/video_comparison.py
rm auto_eval/video_rating_example.py
rm auto_eval/README.md
```

The A2A implementation is **completely independent** of the legacy scripts. Your original `eval.py` is the only old code actively used, and it's perfectly integrated into the green agent.
