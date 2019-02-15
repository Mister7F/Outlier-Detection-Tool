import numpy as np
import keras
from keras import Model
from keras.models import Sequential
from keras.layers import *


class DenseNetwork:
	def __init__(self, layers):
		self.layers = layers

		self._init_model()

	def _init_model(self):
		self.model = Sequential()

		self.model.add(Dense(self.layers[1], activation='relu', input_dim=self.layers[0]))

		for l in self.layers[2:]:
			self.model.add(Dense(l))

		self.model.compile('adam', 'mse')

	def train_model(self, epochs, x_data, y_data):
		self.model.fit(x=x_data, y=y_data, epochs=epochs, validation_split=0, verbose=1)
	
	def measure_error(self, data):
		'''
		Return item index order by abnomaly, and the 
		corresponding score (hight is anormal, low is normal)
		'''
		predicted_vector = self.model.predict(data)

		errors = np.square(predicted_vector - data).sum(axis=1)

		return errors

