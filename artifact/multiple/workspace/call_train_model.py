import sys
from simple_train_lib import *

input_size = 1
hidden_size = 50
num_layers = 1
in_features = 50
out_features = 1
model = create_model(input_size, hidden_size, num_layers, in_features, out_features)

store = dict()
namelist = ["X_train", "y_train", "X_test", "y_test"]
for name in namelist:
	path = "/pytorch/" + name + ".pt"
	print(f"loading {name} data from {path} ...")
	store[name] = torch.load(path, weights_only=False)

batch_size = 8
n_epochs = 100
trained = train_model(model, store["X_train"], store["y_train"], store["X_test"], store["y_test"], batch_size, n_epochs)
print("Saving trained model weight data to /pytorch/trained_weights.pt ...")
torch.save(trained.state_dict(), "/pytorch/trained_weights.pt")