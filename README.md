# ec2_high_available

![Auto ec2 recovery Architecture](./architecture.png)

<img src="./architecture.png" height=64px/> 

## dynamodb table design(hatable)


columname | type 
--- | --- 
appname | string
curr_instance|string
eip|string
pip|string


## sqs desgin
hasqs.fifo

## step function


## autoscaling group

