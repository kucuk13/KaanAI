def get():
  file = open('api_key.txt', 'r')
  api_key = file.read()
  file.close()
  return api_key
