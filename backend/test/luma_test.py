import os
from lumaai import LumaAI
import lumaai

client = LumaAI(
    auth_token=os.environ.get("LUMAAI_API_KEY"),  # This is the default and can be omitted
)

# generation = LumaAI.generations()
# generation = client.generations.create(
#     aspect_ratio="16:9",
#     loop=False,
#     prompt="A teddy bear in sunglasses playing electric guitar, dancing and headbanging in the jungle in front of a large beautiful waterfall",
# )
# print(generation.id)

# generation_list = client.generations.get(id="b50b566e-214f-46f6-9553-60a3bb8b076d")  #.generations.list() .generations.list(limit=100, offset=0)

def get_generation_count(client):
  try:
      generations = client.generations.list()
      return generations.count
  except lumaai.APIStatusError as e:
      return 2
try:
    generation_list = client.generations.get("688ad098-2290-487a-8ef9-bd0fea35414e") # list(limit=100, offset=0)
    
    print(generation_list)
    gen_count = get_generation_count(client)
    print(gen_count)
except lumaai.APIConnectionError as e:
    print("The server could not be reached")
    print(e.__cause__)  # an underlying Exception, likely raised within httpx.
except lumaai.RateLimitError as e:
    print("A 429 status code was received; we should back off a bit.")
except lumaai.APIStatusError as e:
    print("Another non-200-range status code was received")
    print(e.status_code)
    print(e.response)
    print(e.with_traceback)    