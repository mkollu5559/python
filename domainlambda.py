import json
import os
import boto3

def handle_publish_sns(event, topic_arn):
    """Publishes an event to an SNS topic"""
    try:
        s3_record = event["Records"][0]["s3"]
        bucket = s3_record["bucket"]["name"]
        object_key = s3_record["object"]["key"]
        object_size = s3_record["object"]["size"]
        
        message_json = {
            "bucket": bucket,
            "key": object_key,
            "Object Time": event["Records"][0]["eventTime"],
            "object_Size": object_size
        }
        
        message = json.dumps(message_json)
        sns = boto3.client("sns", region_name="us-east-1")
        response = sns.publish(TopicArn=topic_arn, Message=message)
        return response  # ✅ Ensure this always returns a response
    
    except Exception as ex:
        print(f"Error publishing to SNS: {ex}")
        return {"error": str(ex)}  # ✅ Prevent returning None

def lambda_handler(event, context):
    """AWS Lambda handler"""
    try:
        print(f"Received event: {json.dumps(event, indent=2)}")
        
        topic_arn = os.getenv("TOPIC_ARN")
        if not topic_arn:
            raise ValueError("Missing TOPIC_ARN environment variable")

        response = handle_publish_sns(event, topic_arn)
        print(f"Lambda Handler Response: {response}")

        return response  # ✅ Ensure this always returns a response

    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {"error": str(e)}  # ✅ Prevent returning None
