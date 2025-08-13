import sys
from toy_gpt_lib import *

if len(sys.argv) < 2:
    url = "https://www.gutenberg.org/cache/epub/1504/pg1504.txt"
else:
    url = sys.argv[1]

data, vocab_size, stoi, itos = load_corpus(url)
model = create_model(vocab_size)
trained = train_model(model, data)
generative_prompt(model, stoi, itos)
