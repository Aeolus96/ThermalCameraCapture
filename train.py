import matplotlib.pyplot as plt
import numpy as np
from keras import layers, optimizers

from keras.preprocessing.image import load_img
from keras.utils import image_dataset_from_directory
from tensorflow import keras
from tensorflow.keras.callbacks import EarlyStopping

# Directories
b_dir = './thermal'
train_dir = b_dir+'/train'
vali_dir = b_dir+'/validation'


train_noWater_dir =b_dir+'/train/no-spill'
train_water_dir =b_dir+'/train/spill'
vali_noWater_dir = b_dir+'/validation/no-spill'
vali_water_dir = b_dir+'/validation/spill'

import os

print('total training noWater images:', len(os.listdir(train_noWater_dir)))
print('total training water images:', len(os.listdir(train_water_dir)))
print('total validation noWater images:', len(os.listdir(vali_noWater_dir  )))
print('total validation water images:', len(os.listdir(vali_water_dir )))


#Create image dataset
train_dataset = image_dataset_from_directory(
    train_dir,
    image_size=(256, 192),
    batch_size=8)

validation_dataset = image_dataset_from_directory(
    vali_dir,
    image_size=(256, 192),
    batch_size=8)

noWater_img = os.listdir(train_noWater_dir)
water_img = os.listdir(train_water_dir)

print(noWater_img)

fig = plt.figure(figsize=(10, 6))
for i in range(8):
    plt.subplot(4, 2, i+1)
    plt.imshow(load_img(train_noWater_dir + '/'+ noWater_img [i]), cmap='gray')
    plt.suptitle("noWater",fontsize=20)
    plt.axis('off')

plt.show()

fig = plt.figure(figsize=(10, 6))
for i in range(8):
    plt.subplot(4, 2, i+1)
    plt.imshow(load_img(train_water_dir + '/'+ water_img [i]), cmap='gray')
    plt.suptitle("water",fontsize=20)
    plt.axis('off')

plt.show()
#conv_base = keras.applications.vgg16.VGG16(
conv_base = keras.applications.vgg19.VGG19(
#conv_base = keras.applications.resnet50.ResNet50(
#conv_base = keras.applications.ResNet50V2(
#conv_base = keras.applications.EfficientNetB3(
#conv_base = keras.applications.inception_v3.InceptionV3(


#conv_base = keras.applications.inception_resnet_v2.InceptionResNetV2(
#conv_base = keras.applications.xception.Xception(
#conv_base = keras.applications.densenet.DenseNet121(
#conv_base = keras.applications.nasnet.NASNetMobile(
#conv_base = keras.applications.efficientnet.EfficientNetB3(
#conv_base = keras.applications.efficientnet_v2.EfficientNetV2B3(
#conv_base = keras.applications.ConvNeXtBase(    
    weights="imagenet",
    include_top=False,
    input_shape=(256, 192, 3))

conv_base.trainable = True

for layer in conv_base.layers[:-5]:
  layer.trainable = False

# Adding a data augmentation stage and a classifier to the convolutional base
data_augmentation = keras.Sequential(
    [
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.01),
        layers.RandomZoom(0.0),
        layers.RandomContrast(0.01)
    ]
)

inputs = keras.Input(shape=(256, 192, 3))

x = data_augmentation(inputs)

#x = keras.applications.vgg16.preprocess_input(x)
x = keras.applications.vgg19.preprocess_input(x)
#x = keras.applications.resnet50.preprocess_input(x)
#= keras.applications.resnet_v2.preprocess_input(x)
#x = keras.applications.efficientnet.preprocess_input(x)
#x = keras.applications.inception_v3.preprocess_input(x)


#x = keras.applications.inception_resnet_v2.preprocess_input(x)
#x = keras.applications.xception.preprocess_input(x)
#x = keras.applications.densenet.preprocess_input(x)
#x = keras.applications.nasnet.preprocess_input(x)

# EfficientNets
#x = keras.applications.efficientnet.preprocess_input(x)
#x = keras.applications.efficientnet_v2.preprocess_input(x)

# Modern CNN
#x = keras.applications.convnext.preprocess_input(x)


x = conv_base(x)
x = layers.Flatten()(x)
x = layers.Dense(1024)(x)
x = layers.Dense(512)(x)
x = layers.Dense(256)(x)
x = layers.Dropout(0.3)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)
model.compile(loss='binary_crossentropy',
              optimizer=optimizers.RMSprop(learning_rate=1e-5),
              metrics=['accuracy'])
model.summary()

# Early stopping setup
early_stopping = EarlyStopping(
    monitor='val_loss',       # Monitor the validation loss
    patience=5,               # Stop after 5 epochs of no improvement
    verbose=1,                # Print messages when stopping occurs
    restore_best_weights=True # Restore the best model weights
)
callbacks = [
    keras.callbacks.ModelCheckpoint(
        filepath="./Model/best_model.keras",
        save_best_only=True,
        monitor="val_loss"),
        early_stopping
]
history = model.fit(
    train_dataset,
    epochs=50,
    validation_data=validation_dataset,
    callbacks=callbacks)

acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
loss = history.history['loss']
val_loss = history.history['val_loss']

epochs = range(len(acc))
fig, (ax1, ax2) = plt.subplots(1, 2)
fig.set_size_inches(12, 4)

ax1.plot(epochs, acc, 'bo', label='Training acc')
ax1.plot(epochs, val_acc, 'b', label='Validation acc')
ax1.set_title('Training and validation accuracy')
ax1.legend()

ax2.plot(epochs, loss, 'bo', label='Training loss')
ax2.plot(epochs, val_loss, 'b', label='Validation loss')
ax2.set_title('Training and validation loss')
ax2.legend()

plt.show()

test_dir = b_dir+'/test'
test_noWater_dir = test_dir+'/no-spill/'
test_water_dir = test_dir+'/spill/'

test_dataset = image_dataset_from_directory(
    test_dir,
    image_size=(256, 192),
    batch_size=2,
    shuffle=False
)

loaded_model = keras.models.load_model("./Model/best_model.keras")
test_loss, test_acc = loaded_model.evaluate(test_dataset)
