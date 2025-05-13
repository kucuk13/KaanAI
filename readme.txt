pip install openai
pip install Flask
pip install PyGame
pip install matplotlib
pip install elevenlabs
pip install python-dotenv
pip install moviepy
pip install pydub


http://localhost:5000/

response = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."}, #specific instructions
    {"role": "user", "content": "Who won the world series in 2020?"}, #previous question
    {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},  #previous answer
    {"role": "user", "content": "Where was it played?"} #current question
  ]
)

git rm --cached api_key.txt
git add .gitignore
git commit -m "Ignore api_key.txt file"


CMD Commands
(for /l %i in (1,1,200) do @echo file '%i.mp4') > file_list.txt
ffmpeg -f concat -safe 0 -i file_list.txt -c:v libx264 -c:a aac -strict experimental -b:a 192k -preset fast output.mp4
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=1.1111*PTS[v];[0:a]atempo=0.9[a]" -map "[v]" -map "[a]" -preset fast output_slow.mp4
