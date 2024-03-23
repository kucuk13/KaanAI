from openai import OpenAI

API_KEY = "YOUR API KEY"

client = OpenAI(api_key = API_KEY)
conversation = []

while True:
  message = input('For finish write 0 and enter. Enter your message:  ')
  if message == "0":
    break
  else:
    conversation.append({"role": "user", "content": message})
    response = client.chat.completions.create(
      model = "gpt-3.5-turbo",
      messages = conversation
    )
    conversation.append({"role": "assistant", "content": response.choices[0].message.content})
    print(response.choices[0].message.content)
