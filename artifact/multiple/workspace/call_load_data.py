import sys
from simple_train_lib import *

if len(sys.argv) < 2:
    url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv"
else:
    url = sys.argv[1]

if len(sys.argv) < 3:
    proportion = 0.7
else:
    proportion = sys.argv[2]

if len(sys.argv) < 4:
    lookback = 4
else:
    lookback = sys.argv[3]

train, test, forecast = load_data(url, proportion, lookback)

store = {"train": train, "test": test, "forecast": forecast}
namelist = ["train", "test", "forecast"]
for name in namelist:
	path = "/pytorch/" + name + ".pt"
	print(f"Saving {name} data to {path} ...")
	torch.save(store[name], path)