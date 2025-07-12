import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.utils.data as data

def load_data(url, proportion, lookback):
	print("(1) Reading CSV source ...")
	print("")
	# df = pd.read_csv('https://raw.githubusercontent.com/jbrownlee/Datasets/master/airline-passengers.csv')
	df = pd.read_csv(url)
	print("Type of df = ", type(df))
	print("df.shape = ", df.shape)
	timeseries = df[["Passengers"]].values.astype('float32')
	print("Type of timeseries = ", type(timeseries))
	print("timeseries.shape = ", timeseries.shape)

	# proportion = 0.70
	# lookback = 4
	train_size = int(len(timeseries) * proportion)
	test_size = len(timeseries) - train_size
	train, test, forecast = timeseries[:train_size], timeseries[train_size:], timeseries[-lookback:]

	print("Type of train = ", type(train))
	print("train.shape = ", train.shape)
	print("Type of test = ", type(test))
	print("test.shape = ", test.shape)
	print("Type of forecast = ", type(forecast))
	print("forecast.shape = ", forecast.shape)
	return train, test, forecast
	
def prepare_data(train, test, forecast, lookback):
	print("(2) Preparing training data ...")
	print("")
	
	def create_dataset(numarray, past):
		X, y = [], []

		for i in range(len(numarray)-past):
			feature = numarray[i:i+past]
			target = numarray[i+past]
			X.append(feature)
			y.append(target)
		
		return torch.tensor(np.array(X)), torch.tensor(np.array(y))
	
	X_train, y_train = create_dataset(train, lookback)
	X_test, y_test = create_dataset(test, lookback)
	X_forecast = torch.tensor(forecast.reshape(1, -1, 1))

	print("Type of X_train, type of y_train = ", type(X_train), type(y_train))
	print("X_train.shape(samples, timesteps, features), y_train.shape(samples, features) = ", X_train.shape, y_train.shape)
	print("Type of X_test, type of y_test = ", type(X_train), type(y_train))
	print("X_test.shape(samples, timesteps, features), y_test.shape(samples, features) = ", X_test.shape, y_test.shape)
	print("Type of X_forecast = ", type(X_forecast))
	print("X_forecast.shape(samples, timesteps, features) = ", X_forecast.shape)
	
	return X_train, y_train, X_test, y_test, X_forecast

def create_model(input_size, hidden_size, num_layers, in_features, out_features):
	print("(3) Creating training model ...")
	print("")

	class AirModel(nn.Module):
		def __init__(self):
			super().__init__()
			self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)
			self.linear = nn.Linear(in_features=in_features, out_features=out_features)
			
		def forward(self, x):
			x, _ = self.lstm(x)
			x = self.linear(x[:, -1, :])
			return x

	return AirModel()

def train_model(model, X_train, y_train, X_test, y_test, batch_size, n_epochs):
	print("(4) Training and evaluating the model ...")
	print("")

	optimizer = optim.Adam(model.parameters())
	mseloss = nn.MSELoss()
	trainloader = data.DataLoader(data.TensorDataset(X_train, y_train), shuffle=True, batch_size=batch_size)

	for epoch in range(n_epochs):
		model.train()
		for X_batch, y_batch in trainloader:
			y_pred = model(X_batch)
			loss = mseloss(y_pred, y_batch)
			optimizer.zero_grad()
			loss.backward()
			optimizer.step()

		if epoch % 10 != 0:
			continue

		# Validation
		model.eval()
		with torch.no_grad():
			y_pred = model(X_train)
			train_rmse = np.sqrt(mseloss(y_pred, y_train))
			y_pred = model(X_test)
			test_rmse = np.sqrt(mseloss(y_pred, y_test))
			
		print("Epoch %d: train RMSE %.4f, test RMSE %.4f" % (epoch, train_rmse, test_rmse))

	return model

def model_forecast(model, X_forecast):
	print("(5) Forecasting from the model ...")
	print("")

	with torch.no_grad():
	  y_forecast = model(X_forecast)

	print("Forecast input = ", X_forecast)
	print("Forecast output = ", y_forecast)
	return y_forecast