import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

LOG_FILE = "llm_logs.txt"

def log(prompt, response):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "="*40 + "\n")
        f.write("Prompt:\n" + prompt.strip() + "\n")
        f.write("Response:\n" + response.strip() + "\n")

def get_agent_action(
    agent_name,
    position,
    inventory,
    cell_content,
    energy,
    consumption_rate,
    retry_message=None,

):
    prompt = f"""
You are agent {agent_name}, currently at position {position}.
Your energy level is {energy}. You lose 1 energy each step.
You gain energy by eating according to this consumption rate: {consumption_rate}, prioritise eating the food that gives you the most energy.
If you do not eat you will die. So collect, eat and stay alive. 
Food will get replenished in the environment. You might have to move up, move down, move left and move right in the grid to find it. 

Your inventory is: {inventory}.
The current cell contains: {cell_content if cell_content else 'nothing'}.
{f"You can collect this {cell_content} food if you choose to." if cell_content in ['red', 'green'] else ""}

You can perform one of the following actions:
- Move: 'move up', 'move down', 'move left', 'move right'
- Collect food at your cell: 'collect'
- Eat food from your inventory: 'eat red' or 'eat green'
- Do nothing: 'do nothing'

Make a smart decision based on your situation. 
Only reply with one valid action as described above.
"""

    if retry_message:
        prompt += f"\n⚠️ Note: Your previous action failed because: {retry_message}. Try something different."

    try:
        # Create OpenAI client with API key
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        action = response.choices[0].message.content.strip().lower()
        log(prompt, action)
        # print(f"DEBUG: {agent_name} received action: '{action}'")  # Debug output

        # Check for valid actions
        valid_actions = ['move up', 'move down', 'move left', 'move right', 
                        'collect', 'eat red', 'eat green', 'do nothing']
        
        for valid in valid_actions:
            if action.startswith(valid):
                return valid
        
        # print(f"DEBUG: No valid action found for '{action}', defaulting to 'do nothing'")
        return "do nothing"
            
    except Exception as e:
        log(prompt, f"[ERROR] {str(e)}")
        print(f"ERROR in {agent_name}: {str(e)}")
        
        # Fallback to simple rule-based decision
        return get_fallback_action(inventory, cell_content, energy, consumption_rate)

def get_fallback_action(inventory, cell_content, energy, consumption_rate):
    """Simple rule-based fallback when LLM fails"""
    # Critical energy - eat immediately
    if energy <= 5:
        if inventory['red'] > 0 and consumption_rate['red'] > 0:
            return "eat red"
        elif inventory['green'] > 0 and consumption_rate['green'] > 0:
            return "eat green"
    
    # If on food, collect it
    if cell_content in ['red', 'green']:
        return "collect"
    
    # Low on preferred food - eat if energy is getting low
    if energy <= 10:
        if consumption_rate['red'] > consumption_rate['green'] and inventory['red'] > 0:
            return "eat red"
        elif consumption_rate['green'] > consumption_rate['red'] and inventory['green'] > 0:
            return "eat green"
    
    # Default to moving randomly to find food
    import random
    return random.choice(['move up', 'move down', 'move left', 'move right'])