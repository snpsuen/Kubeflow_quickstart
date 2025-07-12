import sys
from simple_train_lib import *

input_size = 1
hidden_size = 50
num_layers = 1
in_features = 50
out_features = 1
model = create_model(input_size, hidden_size, num_layers, in_features, out_features)

print("Loading trained model weight data from /pytorch/trained_weights.pt ...")
trained_weights = torch.load("/pytorch/trained_weights.pt")
model.load_state_dict(trained_weights)

print("Loading X_forecast data from /pytorch/X_forecast.pt ...")
X_forecast = torch.load("/pytorch/X_forecast.pt", weights_only=False)

y_forecast = model_forecast(model, X_forecast)
print("Saving y_forecast data to /pytorch/y_forecast.pt ...")
torch.save(y_forecast, "/pytorch/y_forecasts.pt")