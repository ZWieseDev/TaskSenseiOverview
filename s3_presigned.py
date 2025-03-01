import boto3
import os
from datetime import datetime

# ✅ Initialize S3 Client
s3_client = boto3.client('s3')

# ✅ Environment Variables (Placeholders for Security)
BUCKET_NAME = os.getenv('BUCKET_NAME', '<S3_BUCKET_NAME>')
AUDIT_BUCKET_NAME = os.getenv('AUDIT_BUCKET_NAME', '<AUDIT_LOG_BUCKET>')
AUDIT_LOG_KEY = 'audit_logs.txt'

# ✅ Disallowed file extensions for security
DISALLOWED_EXTENSIONS = {'.exe', '.bat', '.cmd', '.sh', '.bin', '.js', '.vbs', '.ps1', '.py', '.rb', '.pl', '.html', '.htm', '.php', '.asp', '.aspx', '.dll', '.sys', '.drv'}

# ✅ Max file size limit (4GB)
MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB in bytes

# ✅ Main Lambda Handler
def lambda_handler(event, context):
    user_id = event.get('user_id')
    filename = event.get('filename')
    action = event.get('action', 'upload')
    file_size = event.get('file_size', 0)
    user_role = event.get('role', 'free')

    # ✅ Validate file extension
    if any(filename.endswith(ext) for ext in DISALLOWED_EXTENSIONS):
        return {"statusCode": 400, "body": {"error": "File type not allowed."}}
    
    # ✅ Validate user role
    if user_role not in ['owner', 'subscriber', 'free']:
        return {"statusCode": 403, "body": {"error": "Forbidden: Invalid user role"}}
    
    # ✅ Enforce max file size for uploads
    if action == 'upload' and file_size > MAX_FILE_SIZE:
        return {"statusCode": 400, "body": {"error": "File size exceeds the 4GB limit."}}
    
    # ✅ Log action to S3 Audit Log
    log_to_s3(user_id, action, filename)
    
    # ✅ Generate Pre-Signed URL
    presigned_url = generate_presigned_url(action, user_id, filename, file_size)
    if not presigned_url:
        return {"statusCode": 400, "body": {"error": "Invalid action specified."}}
    
    return {"statusCode": 200, "body": {"presigned_url": presigned_url, "expires_in": 3600}}

# ✅ Function to log user actions in S3 Audit Log
def log_to_s3(user_id, action, filename):
    log_entry = f"User: {user_id}, Action: {action}, File: {filename}, Timestamp: {datetime.now().isoformat()}\n"
    s3_client.put_object(
        Bucket=AUDIT_BUCKET_NAME,
        Key=AUDIT_LOG_KEY,
        Body=log_entry.encode('utf-8'),
        ContentType='text/plain'
    )

# ✅ Function to generate Pre-Signed URLs
def generate_presigned_url(action, user_id, filename, file_size=0):
    object_key = f'UserData/{user_id}/{filename}'
    
    try:
        if action == 'upload':
            return s3_client.generate_presigned_url(
                'put_object',
                Params={'Bucket': BUCKET_NAME, 'Key': object_key, 'ContentLength': file_size},
                ExpiresIn=3600
            )
        elif action == 'delete':
            return s3_client.generate_presigned_url(
                'delete_object',
                Params={'Bucket': BUCKET_NAME, 'Key': object_key},
                ExpiresIn=3600
            )
        else:
            return None
    except Exception:
        return None
