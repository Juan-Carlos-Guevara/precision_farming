#importar paquetes keras

import sys
import os
from keras.models import Sequential
from keras.layers import Dense,Flatten,Dropout
from keras.optimizers import Adam 
from keras.layers.convolutional import Conv2D,Convolution2D
from keras.layers.convolutional import MaxPooling2D
from keras.preprocessing.image import ImageDataGenerator
from tensorflow.python.keras import backend as K

import tensorflow as tf

K.clear_session()

training_data = 'data/training'
validation_data ='data/validation'

#Parameters

epochs = 20 # Epocas
length, height = 150, 150 #Altura, Longitud
batch_size = 32 
steps = 1000 #Pasos
validation_steps = 300
filtersConv1 = 32 #filtros1
filtersConv2 = 64 #filtros2
filter_size1 = (3, 3) #tamaño del filtro
filter_size2 = (2, 2)
pool_size = (2, 2) #tamaño del pool
classes = 6
lr = 0.0005

cnn = Sequential()
cnn.add(Convolution2D(filtersConv1, filter_size1, padding ="same", input_shape=(length, height, 3), activation='relu'))
cnn.add(MaxPooling2D(pool_size=pool_size))

cnn.add(Convolution2D(filtersConv2, filter_size2, padding ="same"))
cnn.add(MaxPooling2D(pool_size=pool_size))

cnn.add(Flatten())
cnn.add(Dense(256, activation='relu'))
cnn.add(Dropout(0.5))
cnn.add(Dense(classes, activation='softmax'))

optimizer = Adam(lr=lr, decay=1e-6)

cnn.compile(loss='categorical_crossentropy',
            optimizer=optimizer,
            metrics=['accuracy'])

train_datagen = ImageDataGenerator(
    rescale=1./255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True)

test_datagen = ImageDataGenerator(rescale=1./255)

training_set = train_datagen.flow_from_directory(
    training_data,
    target_size=(height, length),
    batch_size=batch_size,
    class_mode='categorical')

test_set = test_datagen.flow_from_directory(
    validation_data,
    target_size=(height, length),
    batch_size=batch_size,
    class_mode='categorical')

cnn.fit(
    training_set,
    steps_per_epoch=steps,
    epochs=epochs,
    validation_data=test_set,
    validation_steps=validation_steps)

target_dir = './model/'

if not os.path.exists(target_dir):
    os.mkdir(target_dir)
cnn.save('./model/model.h5')
cnn.save_weights('./model/weight.h5')

print(training_set.class_indices)
#{'gato': 0, 'gorila': 1, 'perro': 2}
#{'Etapa 1': 0, 'Etapa 2': 1, 'Etapa 3': 2, 'Etapa 4': 3, 'Producto_final': 4, 'Terreno': 5}