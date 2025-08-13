import torch
import torch.nn as nn
import torch.nn.functional as F
import re
import os

main_config = {
    "device": 'cuda' if torch.cuda.is_available() else 'cpu',
    "batch_size": 16,
    "block_size": 64,
    "max_iters": 100,
    "eval_interval": 10,
    "learning": 1e-3,
    "n_embd": 128,
    "n_head": 4,
    "n_layer": 1,
    "dropout": 0.1
}

def load_corpus(url = "https://www.gutenberg.org/cache/epub/1504/pg1504.txt"):
    print("(1) Reading text source ...")
    print("")
    command = "wget {source} -O corpus.txt".format(source = url)
    os.system(command)

    with open('corpus.txt', 'r', encoding='utf-8') as f:
        text = f.read()

    # Tokenize into words and punctuation
    words = re.findall(r"\b\w+\b|[^\w\s]", text)
    vocab = sorted(set(words))
    vocab_size = len(vocab)
    stoi = {w:i for i,w in enumerate(vocab)}
    itos = {i:w for w,i in stoi.items()}
    encode = lambda s: [stoi[w] for w in re.findall(r"\b\w+\b|[^\w\s]", s) if w in stoi]
    decode = lambda idxs: ' '.join([itos[i] for i in idxs])

    print(f"type(words) = {type(words)}")
    print(f"Vocab size (word-level): {vocab_size}")

    # Convert full corpus to token IDs
    data = torch.tensor(encode(text), dtype=torch.long)
    # x, y = data[:-1], data[1:]

    print(f"type(encode(text)) = {type(encode(text))}")
    print(f"type(data) = {type(data)}")
    print(f"data.shape = {data.shape}")

    return data, vocab_size, stoi, itos

# --- Batching ---
def get_batch(x, y):
    block_size = main_config["block_size"]
    batch_size = main_config["batch_size"]
    device = main_config["device"]

    ix = torch.randint(len(x) - block_size, (batch_size,))
    xb = torch.stack([x[i:i+block_size] for i in ix]).to(device)
    yb = torch.stack([y[i:i+block_size] for i in ix]).to(device)
    return xb, yb

def create_model(vocab_size):
    print("(2) Creating training model ...")
    print("")

    n_embd = main_config["n_embd"]
    n_head = main_config["n_head"]
    n_layer = main_config["n_layer"]
    dropout = main_config["dropout"]
    block_size = main_config["block_size"]
    device = main_config["device"]

    # --- Model Components ---
    class Head(nn.Module):
        def __init__(self, head_size):
            super().__init__()
            self.key = nn.Linear(n_embd, head_size, bias=False)
            self.query = nn.Linear(n_embd, head_size, bias=False)
            self.value = nn.Linear(n_embd, head_size, bias=False)
            self.register_buffer('tril', torch.tril(torch.ones(block_size, block_size)))
            self.dropout = nn.Dropout(dropout)

        def forward(self, x):
            B, T, C = x.shape
            k = self.key(x)
            q = self.query(x)
            wei = q @ k.transpose(-2, -1) * C**-0.5
            wei = wei.masked_fill(self.tril[:T, :T] == 0, float('-inf'))
            wei = F.softmax(wei, dim=-1)
            wei = self.dropout(wei)
            v = self.value(x)
            return wei @ v

    class MultiHead(nn.Module):
        def __init__(self):
            super().__init__()
            head_size = n_embd // n_head
            self.heads = nn.ModuleList([Head(head_size) for _ in range(n_head)])
            self.proj = nn.Linear(n_embd, n_embd)
            self.dropout = nn.Dropout(dropout)

        def forward(self, x):
            return self.dropout(self.proj(torch.cat([h(x) for h in self.heads], dim=-1)))

    class FeedForward(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(n_embd, 4 * n_embd),
                nn.ReLU(),
                nn.Linear(4 * n_embd, n_embd),
                nn.Dropout(dropout)
                        )

        def forward(self, x):
            return self.net(x)

    class Block(nn.Module):
        def __init__(self):
            super().__init__()
            self.ln1 = nn.LayerNorm(n_embd)
            self.ln2 = nn.LayerNorm(n_embd)
            self.sa = MultiHead()
            self.ff = FeedForward()

        def forward(self, x):
            x = x + self.sa(self.ln1(x))
            x = x + self.ff(self.ln2(x))
            return x

    class MiniLLM(nn.Module):
        def __init__(self):
            super().__init__()
            self.tok_emb = nn.Embedding(vocab_size, n_embd)
            self.pos_emb = nn.Embedding(block_size, n_embd)
            self.blocks = nn.Sequential(*[Block() for _ in range(n_layer)])
            self.ln_f = nn.LayerNorm(n_embd)
            self.head = nn.Linear(n_embd, vocab_size)

        def forward(self, idx, targets, debug_print):
            B, T = idx.size()
            tok = self.tok_emb(idx)
            pos = self.pos_emb(torch.arange(T, device=device))
            x = tok + pos
            x = self.blocks(x)
            x = self.ln_f(x)
            logits = self.head(x)
            loss = F.cross_entropy(logits.view(-1, vocab_size), targets.view(-1)) if targets is not None else None

            if debug_print == 1:
                print("logits.shape = ", logits.shape)
                print("targets.shape = ", targets.shape)
                print("logits.view(-1, vocab_size).shape = ", logits.view(-1, vocab_size).shape)
                print("targets.view(-1).shape = ", targets.view(-1).shape)

            return logits, loss

        def generate(self, idx, max_new):
            for _ in range(max_new):
                idx_cond = idx[:, -block_size:]
                logits, _ = self(idx_cond, None, 0)
                probs = F.softmax(logits[:, -1], dim=-1)
                idx_next = torch.multinomial(probs, num_samples=1)
                idx = torch.cat([idx, idx_next], dim=1)
            return idx

    return MiniLLM().to(device)

def train_model(model, data):
    print("(3) Training model ...")
    print("")

    max_iters = main_config["max_iters"]
    eval_interval = main_config["eval_interval"]
    learning = main_config["learning"]

    opt = torch.optim.AdamW(model.parameters(), lr=learning)
    x, y = data[:-1], data[1:]

    # --- Training ---
    first = 1
    for it in range(max_iters):
        xb, yb = get_batch(x, y)
        if first == 1:
            first = 0
            _, loss = model(xb, yb, 1)
        else:
            _, loss = model(xb, yb, 0)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if it % eval_interval == 0:
            print(f"Iter {it} | Loss: {loss.item():.4f}")

    return model

def generative_prompt(model, stoi, itos, max_new = 50):
    print("(4) Generating text from prompt ...")
    print("")

    # --- Interactive Prompt ---
    device = main_config["device"]
    encode = lambda s: [stoi[w] for w in re.findall(r"\b\w+\b|[^\w\s]", s) if w in stoi]
    decode = lambda idxs: ' '.join([itos[i] for i in idxs])
	
    print("\nToy GPT Interactive Mode (word-level) — type 'exit' to quit.")
    while True:
        prompt = input("\nPrompt > ").strip()
        if prompt.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        if not prompt:
            continue
        try:
            print("type(encode(prompt)) = ", type(encode(prompt)))
            print("encode(prompt) = ", encode(prompt))
            context = torch.tensor([encode(prompt)], dtype=torch.long).to(device)
            print("context.shape = ", context.shape)
        except Exception as e:
            print(f"Error: {e}")
            continue
        out = model.generate(context, max_new)[0]
        result = decode(out.tolist())
        print("\nGPT Replying >", result[len(prompt.split()):])