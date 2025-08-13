from toy_gpt_lib import *

print("loading vocab_size from /gpt/vocab_size.pt ...")
vocab_size = torch.load("/gpt/vocab_size.pt", weights_only=False)
model = create_model(vocab_size)

print("Loading trained model weight data from /gpt/trained_weights.pt ...")
trained_weights = torch.load("/torch/trained_weights.pt")
model.load_state_dict(trained_weights)

print("Loading stoi from /gpt/stoi.pt ...")
stoi = torch.load("/gpt/stoi.pt", weights_only=False)

print("Loading itos from /gpt/itos.pt ...")
itos = torch.load("/gpt/itos.pt", weights_only=False)

generative_prompt(model, stoi, itos)
