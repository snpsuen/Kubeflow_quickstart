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
X_train, y_train, X_test, y_test, X_forecast = prepare_data(train, test, forecast, lookback)

input_size = 1
hidden_size = 50
num_layers = 1
in_features = 50
out_features = 1
model = create_model(input_size, hidden_size, num_layers, in_features, out_features)

batch_size = 8
n_epochs = 100
trained = train_model(model, X_train, y_train, X_test, y_test, batch_size, n_epochs)

y_forecast = model_forecast(trained, X_forecast)