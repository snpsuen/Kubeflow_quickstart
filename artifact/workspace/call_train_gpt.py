from toy_gpt_lib import *

print("loading vocab_size from /gpt/vocab_size.pt ...")
vocab_size = torch.load("/gpt/vocab_size.pt", weights_only=False)
model = create_model(vocab_size)

print("loading data from /gpt/data.pt ...")
data = torch.load("/gpt/data.pt", weights_only=False)
trained = train_model(model, data)

print("Saving trained model weight data to /gpt/trained_weights.pt ...")
torch.save(trained.state_dict(), "/gpt/trained_weights.pt")
