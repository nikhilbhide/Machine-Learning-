import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import keras
from keras.preprocessing.image import ImageDataGenerator
from keras.applications import ResNet50
from keras.applications.resnet50 import preprocess_input
from keras import Model, layers
from keras.models import load_model, model_from_json
import cv2
import os
import tensorflow as tf
import PIL
from sklearn.metrics import confusion_matrix 
from sklearn.metrics import accuracy_score 
from sklearn.metrics import classification_report 


train_data_dir = 'dataset/train'
validation_data_dir = 'dataset/validation'
image_size = 224
value_to_class = {}
test_dir = 'dataset/test_images/classes'
test_images_dir = 'dataset/test_images/classes'

#create model with decorated resnetwithout final dense layer
#attach dense layer with 128 nodes and output layer with two nodes
def create_model_decorated_with_resnet():
    conv_base = ResNet50(
    include_top=False,
    weights='imagenet')

    for layer in conv_base.layers:
        #set layers as non trainable
        layer.trainable = False
        
    x = conv_base.output
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation='relu')(x) 
    x = layers.Dropout(0.5)(x)
    outputLayer = layers.Dense(2, activation='softmax')(x)
    model = Model(conv_base.input, outputLayer)

    #use adam as an optimizer
    optimizer = keras.optimizers.Adam()
    #use sparse_categorical_crossentropy as objective function
    model.compile(loss='sparse_categorical_crossentropy',
              optimizer=optimizer,
              metrics=['accuracy'])
    
    return model


def generate_data():
    #this is the augmentation configuration we will use for training
    train_datagen = ImageDataGenerator(
    shear_range=10,
    zoom_range=0.2,
    horizontal_flip=True,
    preprocessing_function=preprocess_input)
    train_generator = train_datagen.flow_from_directory(
        train_data_dir,
        batch_size=32,
        class_mode='binary',
        target_size=(image_size,image_size))

    validation_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)

    validation_generator = validation_datagen.flow_from_directory(
        validation_data_dir,
        shuffle=False,
        class_mode='binary',
        target_size=(224,224))

    return (train_generator, validation_generator)



#evaluate model by running it on train and validation generator
#save model architecture and weights so that it could be used later on
def evaluate_model(model, train_generator, validation_generator):
    history = model.fit_generator(generator=train_generator,
                              steps_per_epoch=347 // 32,  # added in Kaggle
                              epochs=25,
                              validation_data=validation_generator,
                              validation_steps=10,  # added in Kaggle
                              workers=8
                             )


    model.save('models/keras/resnet_model_more_batches.h5')
    model.save_weights('models/keras/resnet_weights_more_batches.h5')
    with open('models/keras/resnet_architecture_more_batches.json', 'w') as f:
        f.write(model.to_json())
        
    return history    
        
# plot diagnostic learning curves
def summarize_diagnostics(history):
    # summarize history for accuracy
    plt.plot(history.history['accuracy'])
    plt.plot(history.history['val_accuracy'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()
    
    # summarize history for loss
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()

def evaluate_model_on_test_data(model, test_directory):
    BATCH_SIZE_TESTING = 1
    test_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
    test_generator = test_datagen.flow_from_directory(
        directory = test_directory, 
        target_size = (image_size, image_size),
        batch_size = BATCH_SIZE_TESTING,
        class_mode = None,
        shuffle = False,
        seed = 123
    )  

    test_generator.reset()
    pred = model.predict_generator(test_generator, steps = len(test_generator), verbose = 1)
    predicted_class_indices = np.argmax(pred, axis = 1)

    cm = confusion_matrix(test_generator.classes, predicted_class_indices)

    print(cm) 
    print("Accuracy Score :",accuracy_score(test_generator.classes, predicted_class_indices))
    print("Report : ")
    print(classification_report(test_generator.classes, predicted_class_indices))
    
    plot_confusion_matrix(cm)

def plot_confusion_matrix(cm):
    plt.imshow(cm, cmap=plt.cm.Blues)
    plt.xlabel("Predicted labels")
    plt.ylabel("True labels")
    plt.xticks([], [])
    plt.yticks([], [])
    plt.title('Confusion matrix ')
    plt.colorbar()
    plt.show()

def perform_validation(model):
    validation_img_paths = ["dataset/test/test/cat.4001.jpg",
                            "dataset/test/test/dog.26.jpg",
                            "dataset/test/test/dog.95.jpg",
                            "dataset/test/test/cat.4057.jpg"]

    img_list = [Image.open(img_path) for img_path in validation_img_paths]


    validation_batch = np.stack([preprocess_input(np.array(img.resize((224,224))))
                                 for img in img_list])


    img_list = [Image.open(img_path) for img_path in validation_img_paths]

    pred_probs = model.predict(validation_batch)
    predicted_class_indices = np.argmax(pred_probs, axis = 1)    
    
    fig, axs = plt.subplots(1, len(img_list), figsize=(20, 5))
    for i, img in enumerate(img_list):
        ax = axs[i]
        ax.axis('off')
        ax.set_title("{:.0f}% Cat, {:.0f}% Dog".format(100*pred_probs[i,0],
                                                                100*pred_probs[i,1]))
        ax.imshow(img)
            
        plt.show()

def create_value_to_label_map(indices):
    label_map = indices
    for key in label_map:
        value_to_class[label_map[key]] = key
    
def get_label(label_value):
    label = value_to_class[label_value]
    print(label)
    return label
            
training_generator, validation_generator = generate_data()
label_map = (validation_generator.class_indices)
model = create_model_decorated_with_resnet()
history = evaluate_model(model, training_generator, validation_generator)
summarize_diagnostics(history)
create_value_to_label_map(training_generator.class_indices)
evaluate_model_on_test_data(model,test_dir)
    