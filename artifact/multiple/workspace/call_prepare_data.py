import sys
from simple_train_lib import *

if len(sys.argv) < 2:
    lookback = 4
else:
    lookback = sys.argv[1]

store = dict()
namelist = ["train", "test", "forecast"]
for name in namelist:
	path = "/pytorch/" + name + ".pt"
	print(f"loading {name} data from {path} ...")
	store[name] = torch.load(path, weights_only=False)

X_train, y_train, X_test, y_test, X_forecast = prepare_data(store["train"], store["test"], store["forecast"], lookback)

store = {"X_train": X_train, "y_train": y_train, "X_test": X_test, "y_test": y_test, "X_forecast": X_forecast}
namelist = ["X_train", "y_train", "X_test", "y_test", "X_forecast"]
for name in namelist:
	path = "/pytorch/" + name + ".pt"
	print(f"Saving {name} data to {path} ...")
	torch.save(store[name], path)