# flake8: noqa
PERPLEXITY_CHAT_COMPLETIONS_DOCS = """BASE URL: https://api.perplexity.ai/chat/completions

API Documentation:
The `/chat/completions` endpoint generates chat completions using Perplexity AI. Authorization via Bearer token is required.

Parameter	Format	Required	Default	Description
Authorization	Header	Yes		Your API key: 'Bearer YOUR_API_KEY'
model	String	Yes		Specifies the model name. Refer to Supported Models for available options.
messages	Object[]	Yes		Contains conversation history (role and content).
max_tokens	Integer	No		Maximum number of tokens to generate. Combined with prompt tokens, must not exceed the context window limit.
temperature	Float	No	0.2	Controls response randomness. Values between 0 and 2.
top_p	Float	No	0.9	Nucleus sampling threshold. Alter either top_p or top_k.
return_citations	Bool	No	false	Whether to return citations in the response (beta).
search_domain_filter	Array	No		Whitelist or blacklist specific domains for online models.
return_images	Bool	No	false	Whether to return images (beta).
return_related_questions	Bool	No	false	Returns related questions in the response (beta).
search_recency_filter	String	No		Limit search results to a specific time range (e.g., day, week).
top_k	Integer	No	0	Top-k filtering. Use either top_p or top_k.
stream	Bool	No	false	Stream responses incrementally (text/event-stream).
presence_penalty	Float	No	0	Penalizes new tokens based on their presence in previous text. Range: -2 to 2.
frequency_penalty	Float	No	1	Penalizes tokens based on their frequency. Range: 0 to infinity.

Example Request:
POST https://api.perplexity.ai/chat/completions
Headers:
{
  "Authorization": "Bearer YOUR_API_KEY",
  "Content-Type": "application/json"
}
Body:
{
  "model": "llama-3.1-sonar-large-128k-online",
  "messages": [
    {
      "role": "system",
      "content": "You are an artificial intelligence assistant and you need to engage in a helpful, detailed, polite conversation with a user."
    },
    {
      "role": "user",
      "content": "How many stars are there in our galaxy?"
    }
  ]
}

Example Response:
{
  "id": "3c90c3cc-0d44-4b50-8888-8dd25736052a",
  "model": "llama-3.1-sonar-large-128k-online,
  "object": "chat.completion",
  "created": 1724369245,
  "choices": [
    {
      "index": 0,
      "finish_reason": "stop",
      "message": {
        "role": "assistant",
        "content": "The number of stars in the Milky Way galaxy is estimated to be between 100 billion and 400 billion stars. The most recent estimates from the Gaia mission suggest that there are approximately 100 to 400 billion stars in the Milky Way, with significant uncertainties remaining due to the difficulty in detecting faint red dwarfs and brown dwarfs."
      },
      "delta": {
        "role": "assistant",
        "content": ""
      }
    }
  ],
  "usage": {
    "prompt_tokens": 14,
    "completion_tokens": 70,
    "total_tokens": 84
  }
}
"""
