import sys
from toy_gpt_lib import *

if len(sys.argv) < 2:
    url = "https://www.gutenberg.org/cache/epub/1504/pg1504.txt"
else:
    url = sys.argv[1]

data, vocab_size, stoi, itos = load_corpus(url)

store = {"data": data, "vocab_size": vocab_size, "stoi": stoi, "itos": itos}
namelist = ["data", "vocab_size", "stoi", "itos"]
for name in namelist:
    path = "/gpt/" + name + ".pt"
    print(f"Saving {name} data to {path} ...")
    torch.save(store[name], path)
