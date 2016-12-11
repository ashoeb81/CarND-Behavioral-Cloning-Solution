"""Build, Train, Evaluate, and Serialize Steering Angle Prediction Model.

Usage:
To train with data read from disk.
python model.py --train_logs driving_log_train.csv --num_train 7698 \
                --test_logs driving_log_test.csv --num_test 962 \
                --validate_logs driving_log_validate.csv --num_validate 962 \

To train with data loaded in memory.
python model.py --train_logs driving_log_train.csv --num_train 7698 \
                --test_logs driving_log_test.csv --num_test 962 \
                --validate_logs driving_log_validate.csv --num_validate 962 \
                --in_memory True

"""

import argparse
import csv  
import json
import h5py
import keras
import numpy as np

from keras.models import Sequential
from keras.layers import Dense, Activation, Conv2D, MaxPooling2D, Flatten, Dropout
from keras.layers.normalization import BatchNormalization
from skimage.data import imread
from skimage.transform import resize
from sklearn.metrics import mean_squared_error


def GetDataGenerator(driving_log_path):
    """Generator that returns images and their labels for model training and evaluation.

    Generator resized input images to dimenstions (25x25x3) and only returns those images
    if associated steering angle != 0.

    Args:
      driving_log_path: Path to log file generator by simulator during training mode.
    Returns:
      Generator of tuples of image and desired steering angle.
    """
    while 1:
        with open(driving_log_path) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
            # For each row of a driving log, yield the center image with the steering angle if non-zero.
            for row in reader:
                center_image = resize(imread(row[0], as_grey=False), (25,25,3))
                steering_angle = np.array([float(row[3])])
                if steering_angle != 0:
                    yield(center_image[np.newaxis,:,:,:], steering_angle)



def CreateModel(num_conv_layers, num_conv_kernels, kernel_dims, num_fc_layers, num_fc_nodes, keep_prob):
    """Construct a Convolutional Neural Network Model with Adam Optimizer and Mean Squared Error Loss.

    Args:
      num_conv_layers: (integer) Number of convolutional layers.
      num_conv_kernels: (list of integers) Number of kernels in each convolutional layer.
      kernel_dims: (list of tuples) Height and width of kernels used by each convolutional layer.
      num_fc_layers: (integer) Number of fully-connected layers.
      num_fc_nodes: (list of integers) Number nodes in each fully-connected layer.
    Returns:
      Keras Sequential Model object.
    """
    # Instantiate keras model object.
    model = Sequential()
    # Add layer to normalize inputs.
    model.add(BatchNormalization(mode=0, axis=3, input_shape=(25, 25, 3)))
    # Add convolutional layers (with ReLu activation) followed by max-pooling layers.
    for conv_layer in range(num_conv_layers):
        model.add(Conv2D(num_conv_kernels[conv_layer], 
                         kernel_dims[conv_layer][0], kernel_dims[conv_layer][1], 
                         border_mode='same', dim_ordering='tf', activation='relu'))
        model.add(MaxPooling2D(dim_ordering='tf'))
    # Flatten feature maps in order to feed into fully-connected layers and add dropout.
    model.add(Flatten())
    model.add(Dropout(keep_prob))
    # Add fully-connected layers (with ReLU activation) follwed by dropout.
    for fc_layer in range(num_fc_layers):
        model.add(Dense(num_fc_nodes[fc_layer], activation='relu'))
        model.add(Dropout(keep_prob))
    # Add read-out layers with no activation.
    model.add(Dense(1, activation=None))
    model.compile(optimizer='adam', loss='mse')
    return model



def TrainModel(model, data_generator, samples_per_epoch=7698, nb_epoch=25, in_memory=True):
    """Trains model on training data provided by a generator.

    Args:
      model: Keras Sequential model object.
      data_generator: Generator of data and labels as returned by GetDataGenerator.
      samples_per_epoch: (integer) Number of training samples per training epoch. 
      nb_epoch: (integer) Number of training epochs.
      in_memory: (boolean) If True, reads all data into memory prior to training.
    Returns:
      Nothing, but modifies model object by calling model.fit_generator(...).  When in_memory=True,
      model object is modified by calling model.fit(...)
    """
    if in_memory:
        X, Y = zip(*[next(data_generator) for i in range(samples_per_epoch)])
        model.fit(np.squeeze(np.array(X)),  np.array(Y), nb_epoch=nb_epoch, batch_size=32)
    else:
        model.fit_generator(data_generator, samples_per_epoch=samples_per_epoch, nb_epoch=nb_epoch, pickle_safe=True,
            nb_worker=4)



def EvaluateModel(model, data_generator, num_samples, in_memory=True):
    """Evaluates model on test data provided by a generator.

    Args:
      model: Keras Sequential model object.
      data_generator: Generator of data and labels as returned by GetDataGenerator.
      num_samples: Total number of samples to generate from generator for evaluation.
      in_memory: (boolean) If True, reads all data into memory prior to evaluation.
    Returns:
      Mean Squared Error of model on evaluation data.  If in_memory=True, then also returns 
      model predictions and target values as numpy arrrays.
    """
    if in_memory:
        X, Y = zip(*[next(data_generator) for i in range(num_samples)])
        Y_hat = model.predict(np.squeeze(np.array(X)))
        return mean_squared_error(Y, Y_hat), Y_hat, Y
    else:
        mse = model.evaluate_generator(data_generator, num_samples)
        return mse, None, None


def SaveModel(model):
    """Saves Keras model and model weights to disk.

    Args:
      model: Keras Sequential model object.
    Returns:
      Nothing.
    """
    json.dump(model.to_json(), open('model.json','w'))
    model.save_weights('model.h5')


def BuildSteeringAnglePredictor(train_logs, num_train_samples,
                                test_logs, num_test_samples,
                                validate_logs, num_validate_samples,
                                in_memory=True):
    """Build, Train, Evaluate, and Serialize Steering Angle Prediction Model.


    Args:
      train_logs: Path to CSV file of training driving log data.
      num_train_samples: Number of training samples.
      test_logs: Path to CSV file of testing driving log data.
      num_test_samples: Number of test samples.
      validate_logs: Path to CSV file of validation driving log data.
      num_validate_samples: Train/Evaluate/Validate with data in memory.
    Returns:
      Nothing.  Serializes trained Keras model to disk by calling SaveModel(...)
    """

    # Build model and train.
    steering_angle_model = CreateModel(2, [8, 16], [(4,4), (4,4)],  1, [32], 0.30)
    train_data_generator = GetDataGenerator(train_logs)
    TrainModel(steering_angle_model, train_data_generator, samples_per_epoch=num_train_samples, 
        nb_epoch=25, in_memory=in_memory)

    # Evaluate model on test data.
    test_data_generator = GetDataGenerator(test_logs) 
    test_mse, _, _ = EvaluateModel(steering_angle_model, test_data_generator, num_test_samples,
        in_memory=in_memory)
    print('Test MSE: %f' % test_mse)

    # Evaluate MSE on validation data.
    validate_data_generator = GetDataGenerator(validate_logs) 
    validate_mse, _, _ = EvaluateModel(steering_angle_model, validate_data_generator, num_validate_samples, 
        in_memory=in_memory)
    print('Validation MSE: %f' % validate_mse)

    # Save model to disk.
    SaveModel(steering_angle_model)



if __name__ == '__main__':
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(description='Train, Evaluate, and Serialize Steering Angle Predictor.')
    parser.add_argument('--train_logs', type=str, help='Path to CSV file of training driving log data.')
    parser.add_argument('--num_train', type=int, default=7698, help='Number of training samples.')
    parser.add_argument('--test_logs', type=str, help='Path to CSV file of testing driving log data.')
    parser.add_argument('--num_test', type=int, default=962, help='Number of test samples.')
    parser.add_argument('--validate_logs', type=str, help='Path to CSV file of validation driving log data.')
    parser.add_argument('--num_validate', type=int, default=962, help='Number of validation samples.')
    parser.add_argument('--in_memory', type=bool, default=False, help='Train/Evaluate/Validate with data in memory.')
    args = parser.parse_args()
    # Construct, train, evaluate, and serialize steering angle prediction model.
    BuildSteeringAnglePredictor(
        args.train_logs, args.num_train,
        args.test_logs, args.num_test,
        args.validate_logs, args.num_validate,
        args.in_memory)