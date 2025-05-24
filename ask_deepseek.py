from openai import OpenAI

def get_output(input, api_key):
	prompt = f"""
You are both a verbal teacher and a robot operator

input: {input}

If input is an actuated command:
- Generate command (ex: speed 50; camera 1)

If input is a knowledge-based question:
- Give short answers
- No need to explain for direct question (explain when asked "How" or "can you explain ... ?")
- Answers are used in text to speech, include no symbols.
"""

	client = OpenAI(
		api_key=api_key,
		base_url="https://api.deepseek.com/v1"
	)

	response = client.chat.completions.create(
		model="deepseek-chat",  # or "deepseek-chat-v1.5"
		messages=[
			{"role": "user", "content": prompt}
		],
		temperature=0.7
	)

	return response.choices[0].message.content
