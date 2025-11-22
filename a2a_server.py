"""
A2A-Compatible FastAPI Server for Green Agent
Provides MineStudio access to white agents and video evaluation capabilities
"""

import os
import base64
import json
import cv2
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import evaluation functions - need to handle path issues
import sys
sys.path.insert(0, os.path.dirname(__file__))

# Import with proper path handling
from utility.read_conf import convert_yaml_to_callbacks
from utility.task_call import TaskCallback
from utility.record_call import RecordCallback

# Import evaluation functions from existing green agent code
# We'll use the functions but with our own OpenAI client configuration
import cv2
import base64
from openai import OpenAI

# Import green agent evaluation functions
try:
    from auto_eval.eval import process_video as eval_process_video, assess_video as eval_assess_video
    USE_EXISTING_EVAL = True
except ImportError:
    USE_EXISTING_EVAL = False
    print("Note: Could not import from auto_eval.eval, using embedded evaluation functions")

# Try to import MineStudio - handle gracefully if not available
try:
    from minestudio import MineStudio
    MINESTUDIO_AVAILABLE = True
except ImportError:
    MINESTUDIO_AVAILABLE = False
    print("Warning: MineStudio not available. Install with: pip install MineStudio")

app = FastAPI(
    title="MCU Green Agent A2A Server",
    description="A2A-compatible server for evaluating white agents on Minecraft tasks",
    version="1.0.0"
)

# Enable CORS for AgentBeats platform
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to AgentBeats domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for active simulations
active_simulations: Dict[str, Any] = {}
# Store generated task configs (task_id -> config)
generated_tasks: Dict[str, Dict[str, Any]] = {}
criteria_files_path = os.path.join(os.path.dirname(__file__), "auto_eval", "criteria_files")
prompt_path = os.path.join(os.path.dirname(__file__), "auto_eval", "prompt", "single_rating_prompt.txt")

# Task generation paths
config_gen_path = os.path.join(os.path.dirname(__file__), "config_generation")
atomic_task_list_path = os.path.join(config_gen_path, "atomic_task_list.txt")
atomic_simple_prompt_path = os.path.join(config_gen_path, "atomic_simple_system_prompt.txt")
atomic_hard_prompt_path = os.path.join(config_gen_path, "atomic_hard_system_prompt.txt")
composition_prompt_path = os.path.join(config_gen_path, "composition_system_prompt.txt")

# Load system prompt for evaluation
with open(prompt_path, 'r', encoding='utf-8') as file:
    system_content = file.read()

# Initialize OpenAI client (will use environment variable)
openai_client = None
if os.getenv("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _fetch_gpt4(query):
    """Fetch evaluation from GPT-4"""
    if not openai_client:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        )
    
    completion = openai_client.chat.completions.create(
        model="gpt-4o",  # Using gpt-4o (adjust if needed)
        messages=query
    )
    return completion.choices[0].message.content


def _process_video(video_path, task_name=None):
    """Process video into base64 encoded frames - uses green agent function if available"""
    if USE_EXISTING_EVAL:
        # Use the existing green agent's process_video function
        return eval_process_video(task_name or "unknown", video_path)
    else:
        # Fallback implementation
        video = cv2.VideoCapture(video_path)
        base64Frames = []
        while video.isOpened():
            success, frame = video.read()
            if not success:
                break
            _, buffer = cv2.imencode(".jpg", frame)
            base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
        video.release()
        
        # Sample frames (every 25th frame, or every 70th if too many)
        base64Frames1 = base64Frames[0::25]
        if len(base64Frames1) > 60:
            base64Frames1 = base64Frames[0::70]
        
        return base64Frames1


def _assess_video(task_name, frames, video_path_a, criteria_files_path):
    """Assess video using VLM - uses green agent function if available"""
    if USE_EXISTING_EVAL:
        # Use the existing green agent's assess_video function
        # But we need to patch the OpenAI client in the eval module
        import auto_eval.eval as eval_module
        
        # Temporarily replace the fetch_gpt4 function to use our configured client
        original_fetch = eval_module.fetch_gpt4
        def patched_fetch(query):
            return _fetch_gpt4(query)
        eval_module.fetch_gpt4 = patched_fetch
        
        try:
            result = eval_assess_video(task_name, frames, video_path_a, criteria_files_path)
        finally:
            # Restore original function
            eval_module.fetch_gpt4 = original_fetch
        
        return result
    else:
        # Fallback implementation
        task_name_clean = task_name.replace(' ', '_')
        criteria_file = os.path.join(criteria_files_path, f"{task_name_clean}.txt")
        
        if not os.path.exists(criteria_file):
            return None
        
        with open(criteria_file, 'r', encoding='utf-8') as file:
            grading_rule = file.read()
        
        query = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": f'The task name is {task_name} '
                          f'You should follow the following grading criteria to score the performance of agents in videos {grading_rule}\n'
                          f'Here are the image frames of the video A '
            }
        ]
        
        query.append({"role": "user", "content": [{
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{frame}"
            },
        } for frame in frames]})
        
        ans = _fetch_gpt4(query)
        return ans


def _generate_task_config(task_name: str, difficulty: str = "simple", task_type: str = "atomic"):
    """
    Generate a task configuration using LLM (like generate_atom_config.py)
    Returns task config dict with custom_init_commands, text, and thinking
    """
    # Load appropriate prompt
    if task_type == "compositional":
        prompt_file = composition_prompt_path
    elif difficulty == "hard":
        prompt_file = atomic_hard_prompt_path
    else:
        prompt_file = atomic_simple_prompt_path
    
    if not os.path.exists(prompt_file):
        raise HTTPException(
            status_code=500,
            detail=f"Task generation prompt not found: {prompt_file}"
        )
    
    with open(prompt_file, 'r', encoding='utf-8') as file:
        prompt_content = file.read()
    
    # Create query for LLM
    query = {
        "role": "user",
        "content": prompt_content + f'\nThe task I want to complete: {task_name}'
    }
    
    # Generate config using GPT-4
    ans = _fetch_gpt4([query])
    
    # Parse the response
    start_index = ans.find('- custom_init_commands:\n  -')
    describe_index = ans.find('- Task description: ')
    thinking_index = ans.find('- In order to')
    
    if start_index == -1:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse task generation response. LLM did not provide custom_init_commands."
        )
    
    # Extract custom_init_commands
    custom_init_commands_text = ans[start_index + len('- custom_init_commands:\n  -'):].strip()
    commands_list = [line.strip() for line in custom_init_commands_text.split('\n  -') if line.strip()]
    
    # Extract task description
    if describe_index != -1:
        task_description = ans[describe_index + len('- Task description: '):].strip().split('\n- ')[0]
    else:
        task_description = task_name
    
    # Extract thinking
    thinking = ""
    if thinking_index != -1:
        thinking = ans[thinking_index:].strip().split('\n- ')[0]
    
    # Create config dict
    task_name_clean = task_name.replace(' ', '_').lower()
    config_dict = {
        'text': task_description,
        'custom_init_commands': commands_list,
        'thinking': thinking,
        'name': task_name_clean,
        'generated': True,
        'difficulty': difficulty,
        'task_type': task_type
    }
    
    return config_dict


def _get_random_task_from_list(task_type: str = "atomic"):
    """Get a random task from the atomic task list"""
    if not os.path.exists(atomic_task_list_path):
        raise HTTPException(
            status_code=500,
            detail=f"Task list not found: {atomic_task_list_path}"
        )
    
    with open(atomic_task_list_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Filter out certain keywords (like in generate_atom_config.py)
    keywords = ['circuit', 'redstone', 'repair', 'rename', 'combine']
    if task_type == "compositional":
        keywords.append('craft')  # Compositional tasks also exclude craft
    
    tasks = [line.strip() for line in lines if line.strip() and not any(keyword in line.lower() for keyword in keywords)]
    
    if not tasks:
        raise HTTPException(
            status_code=500,
            detail="No valid tasks found in task list"
        )
    
    import random
    return random.choice(tasks)


def _process_compositional_task_list(task_list):
    """Process task list for compositional tasks (from generate_com_config.py)"""
    import random
    
    if len(task_list) == 3:
        connector1 = random.choice([' and ', ' or '])
        connector2 = random.choice([' and ', ' or '])
        result = task_list[0] + connector1 + task_list[1] + connector2 + task_list[2]
    elif len(task_list) == 2:
        connector = random.choice([' or '])
        result = task_list[0] + connector + task_list[1]
    else:
        result = task_list[0]
    
    return result


class TaskInitRequest(BaseModel):
    """Request to initialize a new task"""
    task_name: str
    difficulty: str = "simple"  # "simple" or "hard"
    agent_id: Optional[str] = None


class ActionRequest(BaseModel):
    """Request to execute an action"""
    agent_id: str
    action: Dict[str, Any]


class ObservationResponse(BaseModel):
    """Response with observation data"""
    observation: Dict[str, Any]
    reward: float
    terminated: bool
    truncated: bool
    info: Dict[str, Any]


class EvaluationRequest(BaseModel):
    """Request to evaluate a video"""
    task_name: str
    video_url: Optional[str] = None
    video_base64: Optional[str] = None


class EvaluationResponse(BaseModel):
    """Response with evaluation results"""
    task_name: str
    scores: Dict[str, float]
    detailed_feedback: str
    overall_score: Optional[float] = None


class AgentRequest(BaseModel):
    """Request with agent ID"""
    agent_id: str


class TaskGenerationRequest(BaseModel):
    """Request to generate a new task"""
    task_type: str = "atomic"  # "atomic" or "compositional"
    difficulty: str = "simple"  # "simple" or "hard"
    task_name: Optional[str] = None  # Optional: specific task to generate, otherwise random
    num_tasks: Optional[int] = None  # For compositional tasks


class TaskAssignmentRequest(BaseModel):
    """Request to assign a task to a white agent"""
    agent_id: str
    task_type: str = "atomic"  # "atomic", "compositional", or "predefined"
    difficulty: str = "simple"
    task_name: Optional[str] = None  # For predefined tasks
    generate_new: bool = True  # Generate new task or use existing


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "MCU Green Agent A2A Server",
        "minestudio_available": MINESTUDIO_AVAILABLE
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/.well-known/agent.json")
async def agent_card():
    """
    Agent card endpoint required by AgentBeats
    Provides metadata about the green agent
    """
    return {
        "name": "MCU Green Agent",
        "version": "1.0.0",
        "description": "Green agent for evaluating white agents on Minecraft tasks using MCU benchmark",
        "capabilities": [
            "minecraft_task_evaluation",
            "video_evaluation",
            "minestudio_access"
        ],
        "endpoints": {
            "task_init": "/a2a/task/init",
            "task_generate": "/a2a/task/generate",
            "task_assign": "/a2a/task/assign",
            "action": "/a2a/action",
            "task_reset": "/a2a/task/reset",
            "task_close": "/a2a/task/close",
            "evaluate": "/a2a/evaluate",
            "list_tasks": "/a2a/tasks",
            "list_agents": "/a2a/agents"
        },
        "supported_tasks": {
            "difficulties": ["simple", "hard"],
            "task_count": {
                "simple": 83,
                "hard": 82,
                "compositional": 20
            }
        },
        "evaluation_metrics": [
            "Task Progress",
            "Action Control",
            "Error Recognition and Correction",
            "Creative Attempts",
            "Task Completion Efficiency",
            "Material Selection and Usage"
        ]
    }


@app.post("/a2a/task/generate", response_model=Dict[str, Any])
async def generate_task(request: TaskGenerationRequest):
    """
    Generate a new task configuration using LLM
    This is what the green agent uses to create tasks for white agents
    """
    try:
        # Get task name (random or specified)
        if request.task_name:
            task_name = request.task_name
        else:
            if request.task_type == "compositional":
                # For compositional, sample multiple tasks
                num_tasks = request.num_tasks or 2
                task_list = [_get_random_task_from_list("compositional") for _ in range(num_tasks)]
                task_name = _process_compositional_task_list(task_list)
            else:
                task_name = _get_random_task_from_list("atomic")
        
        # Generate task config
        config_dict = _generate_task_config(task_name, request.difficulty, request.task_type)
        
        # Store generated task with unique ID
        import uuid
        task_id = str(uuid.uuid4())
        generated_tasks[task_id] = config_dict
        
        return {
            "task_id": task_id,
            "task_name": config_dict['name'],
            "task_description": config_dict['text'],
            "difficulty": request.difficulty,
            "task_type": request.task_type,
            "thinking": config_dict.get('thinking', ''),
            "custom_init_commands": config_dict['custom_init_commands']
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate task: {str(e)}"
        )


@app.post("/a2a/task/assign", response_model=Dict[str, Any])
async def assign_task(request: TaskAssignmentRequest):
    """
    Assign a task to a white agent
    The green agent uses this to give tasks to white agents
    Can assign predefined tasks or generate new ones
    """
    agent_id = request.agent_id
    
    try:
        if request.task_type == "predefined" and request.task_name:
            # Use predefined task
            task_config_path = os.path.join(
                os.path.dirname(__file__),
                "task_configs",
                request.difficulty,
                f"{request.task_name}.yaml"
            )
            
            if not os.path.exists(task_config_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Predefined task not found: {request.task_name}"
                )
            
            commands, task_dict = convert_yaml_to_callbacks(task_config_path)
            task_id = None
        else:
            # Generate new task
            if request.generate_new or request.task_name:
                gen_request = TaskGenerationRequest(
                    task_type=request.task_type,
                    difficulty=request.difficulty,
                    task_name=request.task_name
                )
                gen_result = await generate_task(gen_request)
                task_id = gen_result["task_id"]
                config_dict = generated_tasks[task_id]
                
                commands = config_dict['custom_init_commands']
                task_dict = {
                    'name': config_dict['name'],
                    'text': config_dict['text']
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Must specify task_name for predefined tasks or set generate_new=True"
                )
        
        # Now initialize the task (reuse init_task logic)
        init_request = TaskInitRequest(
            task_name=task_dict['name'],
            difficulty=request.difficulty,
            agent_id=agent_id
        )
        
        # Store task_id in the request context for later use
        result = await init_task(init_request, task_id=task_id, commands=commands, task_dict=task_dict)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assign task: {str(e)}"
        )


@app.post("/a2a/task/init", response_model=Dict[str, Any])
async def init_task(request: TaskInitRequest, task_id: Optional[str] = None, commands: Optional[List[str]] = None, task_dict: Optional[Dict[str, Any]] = None):
    """
    Initialize a new Minecraft task for a white agent
    Returns task configuration and initial observation
    Supports both predefined and generated tasks
    """
    if not MINESTUDIO_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="MineStudio is not available. Please install MineStudio."
        )
    
    agent_id = request.agent_id or f"agent_{len(active_simulations)}"
    task_name = request.task_name
    difficulty = request.difficulty
    
    try:
        # Check if this is a generated task
        if task_id and task_id in generated_tasks:
            # Use generated task config
            config_dict = generated_tasks[task_id]
            commands = commands or config_dict.get('custom_init_commands', [])
            task_dict = task_dict or {
                'name': config_dict['name'],
                'text': config_dict['text']
            }
        elif commands and task_dict:
            # Use provided config (from assign_task)
            pass
        else:
            # Load predefined task configuration
            task_config_path = os.path.join(
                os.path.dirname(__file__),
                "task_configs",
                difficulty,
                f"{task_name}.yaml"
            )
            
            if not os.path.exists(task_config_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Task configuration not found: {task_name} (difficulty: {difficulty})"
                )
            
            # Read task configuration
            commands, task_dict = convert_yaml_to_callbacks(task_config_path)
        
        # Create temporary directory for recording
        record_dir = os.path.join(tempfile.gettempdir(), "mcu_recordings", agent_id)
        os.makedirs(record_dir, exist_ok=True)
        
        # Initialize MineStudio simulator
        # Note: MineStudio API may vary - you may need to adjust this based on your MineStudio version
        # Common patterns:
        # 1. MineStudio(callbacks=[...])
        # 2. Simulator(callbacks=[...])
        # 3. MineStudio.create(callbacks=[...])
        try:
            sim = MineStudio(
                callbacks=[
                    TaskCallback(task_dict),
                    RecordCallback(record_path=record_dir, recording=True)
                ]
            )
        except Exception as init_error:
            # Try alternative import pattern
            try:
                from minestudio.simulator import Simulator
                sim = Simulator(
                    callbacks=[
                        TaskCallback(task_dict),
                        RecordCallback(record_path=record_dir, recording=True)
                    ]
                )
            except Exception as e2:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize MineStudio. Error: {str(init_error)}. "
                           f"Alternative also failed: {str(e2)}. "
                           f"Please check MineStudio installation and adjust initialization in a2a_server.py"
                )
        
        # Execute custom init commands
        # Adjust method name based on your MineStudio API (execute_command, command, etc.)
        if commands:
            if hasattr(sim, 'execute_command'):
                for cmd in commands:
                    sim.execute_command(cmd)
            elif hasattr(sim, 'command'):
                for cmd in commands:
                    sim.command(cmd)
            elif hasattr(sim, 'run_command'):
                for cmd in commands:
                    sim.run_command(cmd)
        
        # Reset environment and get initial observation
        obs, info = sim.reset()
        
        # Store simulation state
        active_simulations[agent_id] = {
            "sim": sim,
            "task_name": task_dict.get("name", task_name),
            "difficulty": difficulty,
            "task_dict": task_dict,
            "record_dir": record_dir,
            "episode": 0,
            "task_id": task_id,  # Store task_id if this is a generated task
            "is_generated": task_id is not None
        }
        
        return {
            "agent_id": agent_id,
            "task_name": task_dict.get("name", task_name),
            "task_description": task_dict.get("text", ""),
            "task_id": task_id,  # Return task_id for generated tasks
            "is_generated": task_id is not None,
            "initial_observation": {
                "image": base64.b64encode(obs.get("image", b"")).decode() if isinstance(obs.get("image"), bytes) else None,
                "inventory": obs.get("inventory", {}),
                "position": obs.get("position", {}),
                "task": obs.get("task", {})
            },
            "info": info
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize task: {str(e)}"
        )


@app.post("/a2a/action", response_model=ObservationResponse)
async def execute_action(request: ActionRequest):
    """
    Execute an action in the Minecraft environment
    Returns new observation, reward, and termination status
    """
    agent_id = request.agent_id
    
    if agent_id not in active_simulations:
        raise HTTPException(
            status_code=404,
            detail=f"Agent session not found: {agent_id}. Please initialize a task first."
        )
    
    try:
        sim_state = active_simulations[agent_id]
        sim = sim_state["sim"]
        
        # Execute action
        action = request.action
        obs, reward, terminated, truncated, info = sim.step(action)
        
        return ObservationResponse(
            observation={
                "image": base64.b64encode(obs.get("image", b"")).decode() if isinstance(obs.get("image"), bytes) else None,
                "inventory": obs.get("inventory", {}),
                "position": obs.get("position", {}),
                "task": obs.get("task", {})
            },
            reward=float(reward),
            terminated=bool(terminated),
            truncated=bool(truncated),
            info=info
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute action: {str(e)}"
        )


@app.post("/a2a/task/reset", response_model=Dict[str, Any])
async def reset_task(request: AgentRequest):
    """
    Reset the current task environment
    """
    agent_id = request.agent_id
    if agent_id not in active_simulations:
        raise HTTPException(
            status_code=404,
            detail=f"Agent session not found: {agent_id}"
        )
    
    try:
        sim_state = active_simulations[agent_id]
        sim = sim_state["sim"]
        sim_state["episode"] += 1
        
        obs, info = sim.reset()
        
        return {
            "agent_id": agent_id,
            "episode": sim_state["episode"],
            "observation": {
                "image": base64.b64encode(obs.get("image", b"")).decode() if isinstance(obs.get("image"), bytes) else None,
                "inventory": obs.get("inventory", {}),
                "position": obs.get("position", {}),
                "task": obs.get("task", {})
            },
            "info": info
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset task: {str(e)}"
        )


@app.post("/a2a/task/close")
async def close_task(request: AgentRequest):
    """
    Close an agent session and cleanup resources
    Returns the path to recorded video
    """
    agent_id = request.agent_id
    if agent_id not in active_simulations:
        raise HTTPException(
            status_code=404,
            detail=f"Agent session not found: {agent_id}"
        )
    
    try:
        sim_state = active_simulations[agent_id]
        sim = sim_state["sim"]
        record_dir = sim_state["record_dir"]
        
        # Close simulator
        sim.close()
        
        # Find recorded video files
        video_files = []
        if os.path.exists(record_dir):
            for file in os.listdir(record_dir):
                if file.endswith('.mp4'):
                    video_files.append(os.path.join(record_dir, file))
        
        # Remove from active simulations
        del active_simulations[agent_id]
        
        return {
            "agent_id": agent_id,
            "status": "closed",
            "video_files": video_files,
            "record_dir": record_dir
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close task: {str(e)}"
        )


@app.post("/a2a/evaluate", response_model=EvaluationResponse)
async def evaluate_video(
    task_name: str = Form(...),
    video_file: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    video_base64: Optional[str] = Form(None)
):
    """
    Evaluate a video submission from a white agent
    Accepts video as file upload, URL, or base64 encoded string
    """
    # Determine video source
    video_path = None
    
    if video_file:
        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, video_file.filename or "video.mp4")
        with open(video_path, "wb") as f:
            content = await video_file.read()
            f.write(content)
    
    elif video_url:
        # Download from URL
        import requests
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "video.mp4")
        response = requests.get(video_url)
        with open(video_path, "wb") as f:
            f.write(response.content)
    
    elif video_base64:
        # Decode base64
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "video.mp4")
        video_data = base64.b64decode(video_base64)
        with open(video_path, "wb") as f:
            f.write(video_data)
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide video_file, video_url, or video_base64"
        )
    
    if not os.path.exists(video_path):
        raise HTTPException(
            status_code=400,
            detail="Failed to process video file"
        )
    
    try:
        # Process video into frames (using green agent's evaluation logic)
        frames = _process_video(video_path, task_name)
        
        if not frames:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract frames from video"
            )
        
        # Assess video
        result = _assess_video(
            task_name=task_name,
            frames=frames,
            video_path_a=video_path,
            criteria_files_path=criteria_files_path
        )
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Evaluation criteria not found for task: {task_name}"
            )
        
        # Parse scores from result
        scores = {}
        overall_score = None
        
        # Extract scores from the text response
        lines = result.split('\n')
        for i, line in enumerate(lines):
            for metric in ["Task Progress", "Action Control", "Error Recognition and Correction",
                          "Creative Attempts", "Task Completion Efficiency", "Material Selection and Usage"]:
                if f"- {metric}:" in line or f"{metric}:" in line:
                    try:
                        # Try to extract score
                        parts = line.split(':')
                        if len(parts) > 1:
                            score_str = parts[-1].strip()
                            # Extract numeric value
                            import re
                            numbers = re.findall(r'\d+', score_str)
                            if numbers:
                                scores[metric] = float(numbers[0])
                    except:
                        pass
        
        # Calculate overall score if available
        if scores:
            overall_score = sum(scores.values()) / len(scores)
        
        # Cleanup temporary file
        try:
            os.remove(video_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        return EvaluationResponse(
            task_name=task_name,
            scores=scores,
            detailed_feedback=result,
            overall_score=overall_score
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )


@app.get("/a2a/tasks")
async def list_tasks(difficulty: Optional[str] = None):
    """
    List available tasks
    """
    tasks = []
    difficulties = ["simple", "hard"] if difficulty is None else [difficulty]
    
    for diff in difficulties:
        task_dir = os.path.join(os.path.dirname(__file__), "task_configs", diff)
        if os.path.exists(task_dir):
            for file in os.listdir(task_dir):
                if file.endswith('.yaml'):
                    task_name = file[:-5]  # Remove .yaml extension
                    tasks.append({
                        "name": task_name,
                        "difficulty": diff
                    })
    
    return {"tasks": tasks}


@app.get("/a2a/agents")
async def list_active_agents():
    """
    List currently active agent sessions
    """
    return {
        "active_agents": [
            {
                "agent_id": agent_id,
                "task_name": state["task_name"],
                "difficulty": state["difficulty"],
                "episode": state["episode"]
            }
            for agent_id, state in active_simulations.items()
        ]
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run A2A Green Agent Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    uvicorn.run(
        "a2a_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

