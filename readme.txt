pip install openai
pip install Flask
pip install PyGame
pip install matplotlib


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