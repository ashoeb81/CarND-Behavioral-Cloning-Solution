# Behavioral Cloning Project

## Data

To generate the data used for this project, I drove the car around both tracks for multiple laps (at least 4 laps around both tracks 1 and 2).  The driving involved both centerline driving as well as recovery from weaving out to the right and left edges of the road.  My driving generated a dataset of 9622 frames with their associated steering angles.  


The graph below illustrates a histogram of the recorded steering angles.  The histogram shows that a significant fractin of the steering angles are 0.  In fact, ~50% of the recorded frames are associated with a steering angle of zero.

<p align="center">
  ![Screenshot](images/data_histogram.png)
</p>


These frames were **shuffled and split** into a training (7698 frames), testing (962 frames), and validation (962) sets.


![Screenshot](images/truth_vs_prediction.png)

