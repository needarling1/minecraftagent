#!/usr/bin/env python3
"""
Quick test script for A2A server endpoints
Run this after starting the server to verify it's working
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✓ Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_list_tasks():
    """Test task listing endpoint"""
    print("\nTesting task list...")
    try:
        response = requests.get(f"{BASE_URL}/a2a/tasks")
        data = response.json()
        print(f"✓ Found {len(data.get('tasks', []))} tasks")
        if data.get('tasks'):
            print(f"  Example: {data['tasks'][0]}")
        return True
    except Exception as e:
        print(f"✗ Task list failed: {e}")
        return False

def test_list_agents():
    """Test active agents endpoint"""
    print("\nTesting active agents list...")
    try:
        response = requests.get(f"{BASE_URL}/a2a/agents")
        data = response.json()
        print(f"✓ Active agents: {len(data.get('active_agents', []))}")
        return True
    except Exception as e:
        print(f"✗ Active agents failed: {e}")
        return False

def test_task_init():
    """Test task initialization (requires MineStudio)"""
    print("\nTesting task initialization...")
    try:
        payload = {
            "task_name": "mine_diamond_ore",
            "difficulty": "simple",
            "agent_id": "test_agent"
        }
        response = requests.post(
            f"{BASE_URL}/a2a/task/init",
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Task initialized: {data.get('task_name')}")
            print(f"  Agent ID: {data.get('agent_id')}")
            return data.get('agent_id')
        else:
            print(f"✗ Task init failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Task init failed: {e}")
        return None

def main():
    print("=" * 50)
    print("A2A Server Test Suite")
    print("=" * 50)
    
    # Basic tests
    if not test_health():
        print("\n✗ Server is not running. Please start it first:")
        print("  python a2a_server.py")
        sys.exit(1)
    
    test_list_tasks()
    test_list_agents()
    
    # Advanced test (requires MineStudio)
    print("\n" + "=" * 50)
    print("Testing MineStudio integration...")
    agent_id = test_task_init()
    
    if agent_id:
        print(f"\n✓ All tests passed! Agent {agent_id} is ready.")
        print("\nNote: To test action execution, use:")
        print(f"  curl -X POST {BASE_URL}/a2a/action \\")
        print(f"    -H 'Content-Type: application/json' \\")
        print(f"    -d '{{\"agent_id\": \"{agent_id}\", \"action\": {{}}}}'")
    else:
        print("\n⚠ MineStudio test failed. This is expected if:")
        print("  - MineStudio is not installed")
        print("  - Java 8 is not available")
        print("  - MineStudio API differs from expected")
        print("\nThe server is still functional for evaluation endpoints.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()

