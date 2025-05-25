SYSTEM_PROMPT = """
You are Nova-Bot’s brain.  
• If the user gives a **robot command**, answer *only* with a JSON object in this schema and nothing else:

{
  "type": "command",
  "commands": [
    {
      "device": "<motor|camera|gripper|...>",
      "action": "<speed|rotate|state|...>",
      "value": <number|string>
    }
  ]
}


The outer object must appear exactly once, with keys in the same order.
Reply only with raw JSON, no markdown, no backticks, no explanation.

• If the user asks a knowledge question, reply with a plain-text sentence ≤ 30 words, no bullet points, no parentheses, no symbols except basic punctuation
"""

def get_output(user_input: str, client) -> str:
	messages = [
		{"role": "system", "content": SYSTEM_PROMPT},
		# Optional “self-reminder” makes some models more obedient
		{"role": "assistant", "content": "I will obey the above format strictly."},
		{"role": "user", "content": user_input}
	]
	resp = client.chat.completions.create(
		model="deepseek-chat",
		messages=messages,
		temperature=0.3,
		top_p=1.0
		)
	return resp.choices[0].message.content
