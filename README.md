# bdt-video-processing
Scalable video processing demo project for BDT MUM class


## Group Members

Lamin Saidy (lsaidy@mum.edu)
Anthony Anyanwu (acanyanwu@mum.edu)


## file structure.

All the scripts which need to run has been specified in the supervisord.conf file.

Most of the scripts has been written in Python. They are contained in the videoprocessor folder.

The Java project is contained in the kafka-video-plain-spark-stream. 


## Description of scripts in Supervisor config file

There are 6 components utilized for this project. The task of corresponding component is configured on supervisor and it is mentioned in the relevant sections on the supervisord.conf file.

For clarity, see the same sections below:


[program:jupyter]               ; This is responsible for runninng the jupyter notebook


[program:video-spooler]         ; This program monitors the uploads directory and pushes all video found to kafka topic, frame by frame


[program:video-app]              ; This is a simple Flask app to allow video upload from user onn browser


[program:plainframe-streamer]    ; This runs the pure java spark stream and stores the results to HBase.


[program:rgbsplitter-streamer]    ; Python based spark streamer to which averages each frame's RGB component and stores it to DB 


[program:yolo-streamer]           ; Python based spark streamer which applies Yolo convolutional networks algorithm on each frame and stores the result to HBase 


## Project dependencies

### Java

Java 1.8 is required.


This is a maven project. All dependencies are contained in the pom file. 


### Python

Python3.5+ is required.


Run the following commands using the pip-requires.txt file in the videoprocessing folder.

> python3 -mpip install -r pip-requires.txt

 