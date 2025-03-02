def get(key):
  with open('api_key.txt', 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if '=' in line:
                k, v = line.split('=', 1)
                if k.strip() == key:
                    return v.strip()
  return None
