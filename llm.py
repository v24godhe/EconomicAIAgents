import os
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
from config import (
    USE_LOCAL_LLM, USE_MULTIMODAL, LOCAL_LLM_MODEL, MULTIMODAL_LLM_MODEL,
    LOCAL_LLM_URL, LOCAL_LLM_TIMEOUT, AGENT_MEMORY_SIZE
)

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

LOG_FILE = "llm_logs.txt"

def log(prompt, response):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "="*40 + "\n")
        f.write("Prompt:\n" + prompt.strip() + "\n")
        f.write("Response:\n" + response.strip() + "\n")

def call_local_llm(prompt):
    """Call local LLM via Ollama API"""
    try:
        payload = {
            "model": LOCAL_LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 50,
                "stop": ["\n", ".", "Action:"]
            }
        }
        response = requests.post(
            f"{LOCAL_LLM_URL}/api/generate",
            json=payload,
            timeout=LOCAL_LLM_TIMEOUT
        )
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            print(f"Local LLM error: HTTP {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print("Cannot connect to local LLM. Make sure Ollama is running.")
        return None
    except requests.exceptions.Timeout:
        print("Local LLM request timed out.")
        return None
    except Exception as e:
        print(f"Local LLM error: {str(e)}")
        return None

def call_multimodal_llm(prompt, image_base64):
    """Call multimodal LLM (LLaVA) via Ollama API with image input"""
    try:
        payload = {
            "model": MULTIMODAL_LLM_MODEL,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 50,
                "stop": ["\n", ".", "Action:"]
            }
        }
        response = requests.post(
            f"{LOCAL_LLM_URL}/api/generate",
            json=payload,
            timeout=LOCAL_LLM_TIMEOUT
        )
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            print(f"Multimodal LLM error: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Multimodal LLM error: {str(e)}")
        return None

def call_openai_llm(prompt):
    """Call OpenAI API"""
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.7
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None

def get_agent_action(
    agent_name,
    position,
    inventory,
    cell_content,
    energy,
    consumption_rate,
    memory=None,
    grid_image_base64=None,
    retry_message=None,
):
    # Convert Project 1's memory system to Project 2's movement history format
    history_section = ""
    if memory and len(memory) > 0:
        # Extract movement info from Project 1's memory entries to create Project 2 style history
        formatted_entries = []
        for mem in memory[-3:]:  # Last 3 memories
            # Parse memory format: "Step X: Action: Y | Observation: Z | Outcome: W | Energy: E | Inventory: I"
            if "Step " in mem and "Action:" in mem:
                try:
                    step_part = mem.split("Step ")[1].split(":")[0]
                    action_part = mem.split("Action: ")[1].split(" | ")[0]
                    if "Observation:" in mem:
                        obs_part = mem.split("Observation: ")[1].split(" | ")[0]
                        # Extract position and cell content from observation
                        if "at (" in obs_part:
                            pos_part = obs_part.split("at ")[1].split(",")[0] + "," + obs_part.split(", ")[1].split(")")[0] + ")"
                            cell_part = obs_part.split("cell has ")[1].split(",")[0] if "cell has " in obs_part else "unknown"
                            formatted_entries.append(f"- Step {step_part}: At {pos_part} | Found: {cell_part} | Action: {action_part}")
                except:
                    # If parsing fails, use a simplified format
                    formatted_entries.append(f"- {mem[:50]}...")
        
        if formatted_entries:
            history_section = f"\n📜 Your recent actions:\n" + "\n".join(formatted_entries) + "\n"

    # Project 2's enhanced prompt structure
    base_prompt = f"""🧠 Agent Status Report: {agent_name}
📍 Position: {position} on a 9x9 grid
⚡ Energy Level: {energy} (you lose 1 energy every step)
🎒 Inventory: {inventory}
🍽️ Consumption Rate: {consumption_rate}. — Give priority to eat the food that gives you the most energy according to consumption rate.
📦 Current Cell Contents: {cell_content if cell_content else 'nothing'}
{f"✅ You can collect the {cell_content} food here." if cell_content in ['red', 'green'] else ""}

{history_section}

🧭 Strategy Tips:
- Collect food if it's available.
- Eat if you have food available or your energy is low.
- Move in all directions (up, down, left, right) to find food — the grid is 9x9.
- Avoid wasting turns — survive as long as possible!

🧭 Movement Tips:
- Based on your recent actions above, try to make a smart decision.
- Avoid repeating moves that led to empty cells or no gain.
- Change your direction if move is blocked.
- Explore unvisited or promising directions based on your recent outcomes.
- Learn from past actions: if moving in one direction wasn't useful, try a different one.

🚨 PRIORITY: 🔺 Don't forget to eat food to maintain energy levels.

🎮 Valid Actions (choose one only):
- Move → 'move up', 'move down', 'move left', 'move right'
- Collect food → 'collect'
- Eat → 'eat red', 'eat green'
- Take a break → 'do nothing' (not recommended if you can act)

🎯 Decision Rule:
Reply with only **one valid action** exactly as described above. No explanation or reasoning."""

    # Add visual context if multimodal
    if USE_MULTIMODAL and grid_image_base64:
        visual_prompt = f"""
Look at the image showing the grid around you. In the image:
- 🍎 Red circles = red food
- 🥦 Green circles = green food  
- ⚪ Gray circles = other agents
- 🟡 Yellow circle with black border = you
- ⬜ White squares = empty cells

Use this visual information along with the text description to make your decision.

{base_prompt}"""
        prompt = visual_prompt
    else:
        prompt = base_prompt

    if retry_message:
        prompt += f"\n⚠️ Note: Your previous action failed because: {retry_message}. Try something different."

    # Try multimodal LLM first if enabled and image available
    action = None
    if USE_MULTIMODAL and grid_image_base64 and USE_LOCAL_LLM:
        action = call_multimodal_llm(prompt, grid_image_base64)
        if action:
            action = action.lower()
            log(prompt, f"[MULTIMODAL LLM] {action}")

    # Try local text LLM if multimodal failed or not enabled
    if not action and USE_LOCAL_LLM:
        action = call_local_llm(base_prompt)
        if action:
            action = action.lower()
            log(base_prompt, f"[LOCAL LLM] {action}")

    # Fallback to OpenAI if local LLM failed or is disabled
    if not action and api_key:
        action = call_openai_llm(base_prompt)
        if action:
            log(base_prompt, f"[OPENAI] {action}")

    # If all LLMs failed, do nothing
    if not action:
        log(base_prompt, "[NO ACTION] All LLMs failed, agent does nothing.")
        return "do nothing"

    # Check for valid actions
    valid_actions = ['move up', 'move down', 'move left', 'move right',
                     'collect', 'eat red', 'eat green', 'do nothing']

    for valid in valid_actions:
        if action.startswith(valid):
            return valid

    # Default fallback
    return "do nothing"