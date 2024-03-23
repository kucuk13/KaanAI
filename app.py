from openai import OpenAI
import api_key

client = OpenAI(api_key = api_key.get())
conversation = []

while True:
  message = input('For finish write 0 and enter. Enter your message:  ')
  if message == "0":
    break
  else:
    conversation.append({"role": "user", "content": message})
    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=conversation
    )
    conversation.append({"role": "assistant", "content": response.choices[0].message.content})

    speech_response = client.audio.speech.create(
      model="tts-1",
      voice="nova",
      input=response.choices[0].message.content
    )
    speech_response.stream_to_file("output.mp3")
    
    print(response.choices[0].message.content)
