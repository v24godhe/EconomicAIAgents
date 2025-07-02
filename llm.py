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
    # Build memory context
    memory_context = ""
    if memory and len(memory) > 0:
        memory_context = ""
        for i, mem in enumerate(memory[-AGENT_MEMORY_SIZE:], 1):
            memory_context += f"{i}. {mem}\n"
    else:
        memory_context = "None"

    # Build emoji-rich prompt
    base_prompt = f"""You are 🤖 Agent {agent_name} at position {position} on a 9x9 grid.
Your current energy is {energy} ⚡. You lose 1 ⚡ each step.
Your inventory: {inventory}
The cell you are on contains: {cell_content if cell_content else 'nothing'}.

🍎 Red food gives you {consumption_rate.get('red', 0)} ⚡.
🥦 Green food gives you {consumption_rate.get('green', 0)} ⚡.

Your recent memories:
{memory_context}

You can do ONE of the following actions (reply with just the action):
- 🚶 Move: 'move up', 'move down', 'move left', 'move right'
- 🍽️ Collect food at your cell: 'collect'
- 🍴 Eat food from your inventory: 'eat red' or 'eat green'
- 😴 Do nothing: 'do nothing'

🎯 Goal: Stay alive as long as possible by collecting and eating food to keep your energy above 0. Prioritize actions that maximize your survival.

Reply with only one valid action from the list above."""

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
    return