# Behavioral Cloning Project

## Data

To generate the data used for this project, I drove the car around both tracks for multiple laps (at least 4 laps around both tracks 1 and 2).  The driving involved both centerline driving as well as recovery from weaving out to the right and left edges of the road.  My driving generated a dataset of 9622 frames with their associated steering angles.  The graph below illustrates a histogram of the recorded steering angles.  The histogram shows that the steering angles are between -1 and 1 with a significant fraction of the steering angles equal to 0.  In fact, ~50% of the recorded frames are associated with a steering angle of zero.

![Screenshot](images/data_histogram.png)

The recorded frames (9622 frames) were **shuffled and split** into a training (7698 frames), testing (962 frames), and validation (962) sets.  Furthermore, only frames with non-zero steering angles were used to train, test, and validate the model.  The distribution of the train, test, and validation datasets are shown below.

![Screenshot](images/train_test_validate_histogram.png)

