import json
import boto3
import time
from boto3.dynamodb.conditions import Key, Attr
region = 'ap-northeast-1'

queue_url='https://sqs.ap-northeast-1.amazonaws.com/107400677947/hasqs.fifo'



client = boto3.client('stepfunctions',region_name='ap-northeast-1')


def get_instance_attr(remove_inst_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('hatable')
    response = table.scan(
        FilterExpression=Attr('curr_instance').eq(remove_inst_id)
    )
    items = response['Items']
    print('Received current instance items from ddb: %s' % items)
    return items

# when termanite instance send SQS messages

def get_remove_ins_id():
    client = boto3.client('sqs')
    response = client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        VisibilityTimeout=60,
        WaitTimeSeconds=10
    )

    message = response['Messages'][0]
    body = message['Body']
    message_json = json.loads(body)
    instance_id = message_json['detail']['EC2InstanceId']
    print('Received instance id from SQS: %s' % instance_id)
    # Delete received message from queue
    receipt_handle = message['ReceiptHandle']
    print('get sqs message ReceiptHandle from SQS to delete  message: %s' % receipt_handle)
    client.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    print('Received and deleted message completed: %s' % message)
    # return instance id
    return instance_id

def lambda_handler(event, context):
    print(event)
    message = json.loads(event['Records'][0]['Sns']['Message'])
    #print(message)
    instance_id = message['detail']['EC2InstanceId']
    remove_inst_id = get_remove_ins_id()
    print('Get remove instance id is: %s' % remove_inst_id)
    instance_attr = get_instance_attr(remove_inst_id)
    print('Get instance attr from ddb is: %s' % instance_attr)
    eip_address = instance_attr[0]['eip']
    print(eip_address)
    pip_address = instance_attr[0]['pip']
    print(pip_address)
    app_name = instance_attr[0]['appname']
    print(app_name)

    response = client.start_execution(
        stateMachineArn="arn:aws:states:ap-northeast-1:107400677947:stateMachine:ec2ha",
        #input = "{\"first_name\" : \"test\"}"
        input = "{\"Action\": \"step1\",\"instance_id\": \""+instance_id+"\",\"appname\": \""+app_name+"\",\"curr_instance\": \""+remove_inst_id+"\",\"eip\": \""+eip_address+"\",\"pip\": \""+pip_address+"\"}" 
        #input = "{\"Action\": \"step1\",\"instance_id\": \"i-0e7f8f2dcc16b25a2\",\"appname\": \"webserver101\",\"curr_instance\": \"i-0fc086b4495d04538\",\"eip\": \"eipalloc-0729921e87d906fd8\",\"pip\": \"192.168.1.101\"}" 

    )
