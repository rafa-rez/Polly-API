import json
import random
import string
import os
import boto3
from botocore.exceptions import ClientError
import hashlib
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['DYNAMODB_CUSTOMER_TABLE']
table = dynamodb.Table(table_name)

def health(event, context):
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        #"input": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response

def v1_description(event, context):
    body = {
        "message": "TTS api version 1."
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response

#Gera um hash de 5 caracteres. A mesma string sempre terá o mesmo hash
def generate_id(string):
    hash_object = hashlib.sha256(string.encode())
    
    hex_dig = hash_object.hexdigest()

    hash_id = hex_dig[:5]
    
    return hash_id

#Busca no banco de dados a ocorrência de um registro com o mesmo hash
def get_item_by_phrase(phrase_id):
    try:
        response = table.scan(FilterExpression='primary_key = :p',ExpressionAttributeValues={':p': phrase_id})
    except ClientError as e:
        print(e.response['Error']['Message'])
        return None
    else:
        items = response.get('Items', [])
        if items:
            return items[0]
        else:
            return None

#Coleta a data atual para armazenar junto com o registro no bando de dados        
def get_current_datetime():
    nowGMT = datetime.now()

    #Ajustar para fuso horário de brasília
    nowGMTMinus3 = nowGMT - timedelta(hours=3)

    formatted_datetime = nowGMTMinus3.strftime('%d-%m-%Y %H:%M:%S')
    return formatted_datetime

def post(event, context):
    body = json.loads(event.get('body', '{}'))
    
    phrase = body.get('phrase', '')
    originalPhrase = phrase
    phrase = phrase.lower()
    
    phrase_id = generate_id(phrase)
    
    existing_item = get_item_by_phrase(phrase_id)
    if existing_item:
        response_body = {
            "received_phrase": f"{originalPhrase}",
            "url_to_audio": "[LINK AUDIO BUCKET]",
            "created_audio": existing_item['created_audio'],
            "unique_id": existing_item['primary_key']
        }

        response = {"statusCode": 200,"body": json.dumps(response_body),"headers": {"Content-Type": "application/json"}}

        return response

    date = get_current_datetime()

    item = {
        'created_audio': date,
        'primary_key': phrase_id,
        'phrase': phrase
    }

    try:
        table.put_item(Item=item)
    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"Error saving the phrase: {error_message}")
        response_body = {
            "message": "Error saving the phrase.",
            "error": error_message
        }
        response = {
            "statusCode": 500,
            "body": json.dumps(response_body),
            "headers": {
                "Content-Type": "application/json"
            }
        }
        return response

    response_body = {
        "received_phrase": f"{originalPhrase}",
        "url_to_audio": "[LINK AUDIO BUCKET]",
        "created_audio": f"{date}",
        "unique_id": f"{phrase_id}"
    }

    response = {"statusCode": 200,"body": json.dumps(response_body),"headers": {"Content-Type": "application/json"}}

    return response


