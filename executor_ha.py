import json
import boto3
import time
from boto3.dynamodb.conditions import Key, Attr
region = 'ap-northeast-1'

route_id='rtb-45da5e23'
docname = 'AWS-RunShellScript'


def send_command(event):
    Action = event['Action']
    instance_id = event['instance_id']
    pip_address = event['pip']
    app_name = event['appname']
    curr_instance = event['curr_instance']
    eip = event['eip']
    ssm_client = boto3.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=[ instance_id ],
        DocumentName=docname,
        TimeoutSeconds = 60,
        #Parameters={'commands': ["ifconfig eth0:0 "pip_address" netmask 255.255.255.255 up;systemctl start httpd"]}, )
        Parameters={'commands': ["ifconfig eth0:0 "+pip_address+" netmask 255.255.255.255 up;cd /efs/"+app_name+";sh /efs/"+app_name+"/start.sh"]}, )
    command_id = response['Command']['CommandId']
    print('send command id: %s' % command_id)
    return {'command_id':command_id,'Action':'step2','instance_id':instance_id,'pip':pip_address,'appname':app_name,'curr_instance':curr_instance,'eip':eip}
    #return("xxx")

def get_command_status(event):
    command_id = event['command_id']
    Action = event['Action']
    instance_id = event['instance_id']
    pip_address = event['pip']
    app_name = event['appname']
    curr_instance = event['curr_instance']
    eip = event['eip']
    ssm_client = boto3.client('ssm')
    response = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=instance_id
    )
    print(response)
    if response['Status'] =='Success':
        #return {'Finished':'True'}
        return {'Action':'step3','Finished':'True','instance_id':instance_id,'pip':pip_address,'appname':app_name,'curr_instance':curr_instance,'eip':eip}
    elif response['Status'] =='Failed':
        #return {'Finished':'True'}
        return {'Action':'step1','Finished':'Failed','instance_id':instance_id,'pip':pip_address,'appname':app_name,'curr_instance':curr_instance,'eip':eip}
    else:
        #return {'Finished':'False'}
        return {'Action':'step2','Finished':'False','instance_id':instance_id,'pip':pip_address,'appname':app_name,'curr_instance':curr_instance,'eip':eip}


def modify_instance(instance_id):
    #modify instance to set no-source-dest-check
    #modify="aws ec2 modify-instance-attribute --instance-id i-0eee0d892e1f7e830 --no-source-dest-check"
    client = boto3.client('ec2')
    response = client.modify_instance_attribute(
        InstanceId=instance_id,
        SourceDestCheck={
            'Value': False
        }
    )
    print('Change no-source-dest-check instance id: %s' % instance_id)
def change_route(instance_id,pip_address):
    client = boto3.client('ec2')
    response = client.replace_route(
    DestinationCidrBlock=pip_address+"/32",
    InstanceId=instance_id,
    ###route table id
    RouteTableId=route_id
    )
    print('Change route table for pip: %s' % pip_address)
    
    
    
def faileover_eip(instance_id, eip_address):
    client = boto3.client('ec2')
    response = client.associate_address(
        AllocationId= eip_address,
        InstanceId= instance_id
    )
    print('Change eip to new instance id: %s' % instance_id)
def change_network(event):
    Action = event['Action']
    instance_id = event['instance_id']
    pip_address = event['pip']
    app_name = event['appname']
    curr_instance = event['curr_instance']
    eip = event['eip']
    #change eip address to new instance
    faileover_eip(instance_id,eip)
    #change route to new instnace
    change_route(instance_id,pip_address)
    #mod instance to disable des check
    modify_instance(instance_id)
    print('Change network to new instance id: %s' % instance_id)
    return {'Action':'step4','instance_id':instance_id,'pip':pip_address,'appname':app_name,'curr_instance':curr_instance,'eip':eip}




def update_cmdb(event):
    Action = event['Action']
    instance_id = event['instance_id']
    pip_address = event['pip']
    app_name = event['appname']
    curr_instance = event['curr_instance']
    eip = event['eip']
    faileover_eip(instance_id,eip)
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('hatable')
    
    table.update_item(
    Key={
        'appname': app_name,
    },
    UpdateExpression='SET curr_instance = :val1',
    ExpressionAttributeValues={
        ':val1': instance_id
    }
    )
    return "OK"

def lambda_handler(event, context):
    print(event)
    if event['Action'] == 'step1':
        output1 = send_command(event)
    elif event['Action'] == 'step2':
        print(event)
        output1 = get_command_status(event)    
    elif event['Action'] == 'step3':
        print(event)
        output1 = change_network(event)
    elif event['Action'] == 'step4':
        print(event)
        output1 = update_cmdb(event)
    return output1
