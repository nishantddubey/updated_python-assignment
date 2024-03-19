from flask import Flask, render_template, request, redirect, url_for
import boto3
import os
import json

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# Load AWS credentials from a separate file

with open('aws_credentials.json', 'r') as f:
    aws_credentials = json.load(f)

s3 = boto3.client(
    's3',
    aws_access_key_id=aws_credentials['aws_access_key_id'],
    aws_secret_access_key=aws_credentials['aws_secret_access_key'],
)
try:
    BUCKETS =  [bucket['Name'] for bucket in s3.list_buckets()['Buckets']]
    BUCKET_NAME=""
    for bucket in BUCKETS:
        BUCKET_NAME = bucket
        break
except Exception as e:
        
        BUCKET_NAME=None
    

@app.route('/')
@app.route('/home')
def index():
    try:
        if BUCKET_NAME:
            # List contents of the S3 bucket
            response = s3.list_objects(Bucket=BUCKET_NAME)
            files = []
            folders = {}
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('/'):
                        folder_name = obj['Key']
                        folders[folder_name] = []
                    else:
                        file_name = obj['Key']
                        folder_name = '/'.join(file_name.split('/')[:-1])
                        folders[folder_name].append(file_name)
                        files.append(file_name)  # Collect all file names
                        
            # Fetch the list of buckets
            buckets = [bucket['Name'] for bucket in s3.list_buckets()['Buckets']]
            
            return render_template('index.html', buckets=buckets, folders=folders, files=files)
        else:
            return render_template('error.html', error="AWS credentials not available. Please check configuration.")
    except Exception as e:
        return render_template('no_bucket_case.html', error=str("No Bucket exist!! Please create bucket"))


# To create bucket from AWS account
@app.route('/create-bucket', methods=['POST'])
def create_bucket():
    try:
        bucket_name = request.form['bucket-name']
        if bucket_name:
            if bucket_name in BUCKETS:
                return render_template('error.html', error=str("Bucket Already Exist. Please try with different Bucket Name.")), 500

            # Create S3 bucket
            s3.create_bucket(Bucket=bucket_name)
            return redirect(url_for('index'))
        else:
            return render_template('error.html', error="Bucket name is required."), 400
    except Exception as e:
        return render_template('error.html', error=str("Unable to create bucket. Please try again.")), 500


# To delete a bucket from AWS account
@app.route('/delete-bucket', methods=['POST'])
def delete_bucket():
    try:
        bucket_name = request.form['bucket-name']
        if bucket_name:
            # Delete S3 bucket
            s3.delete_bucket(Bucket=bucket_name)
            return redirect(url_for('index'))
        else:
            return render_template('error.html', error="Bucket name is required."), 400
    except Exception as e:
        return render_template('error.html', error=str("Unable to delete bucket. Please try again.")), 500

#To create folder in buckets
@app.route('/create-folder', methods=['POST'])
def create_folder():
    try:
        folder_name = request.form['folder-name']
        if folder_name:
            # Create folder in S3 bucket
            s3.put_object(Bucket=BUCKET_NAME, Key=(folder_name + '/'))
        return redirect(url_for('index'))
    except Exception as e:
        return render_template('error.html', error=str("Unabble to CREATE FOLDER,Try again")), 500

#To delete folder from bucket
@app.route('/delete-folder', methods=['POST'])
def delete_folder():
    try:
        folder_name = request.form['folder-name']
        if folder_name:
            # Delete folder and its contents from S3 bucket
            s3.delete_object(Bucket=BUCKET_NAME, Key=(folder_name))
        return redirect(url_for('index'))
    except Exception as e:
        return render_template('error.html', error=str("Unable to DELETE FOLDER")), 500

#To delete file from folders
@app.route('/delete-file', methods=['POST'])
def delete_file():
    try:
        file_name = request.form['file-name']
        if file_name:
            # Delete file from S3 bucket
            s3.delete_object(Bucket=BUCKET_NAME, Key=file_name)
        return redirect(url_for('index'))
    except Exception as e:
        return render_template('error.html', error=str("Unable to DELETE file")), 500


#To upload file in folders
@app.route('/upload-file', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        folder = request.form['folder']
        if file:
            # Upload file to S3 bucket in the selected folder
            s3.upload_fileobj(file, BUCKET_NAME, folder + '/' + file.filename)
        return redirect(url_for('index'))
    except Exception as e:
        return render_template('error.html', error=str("Unable to UPLOAD file, Select file & folder properly")), 500


#To copy file from one folder to another folder
@app.route('/copy-file', methods=['POST'])
def copy_file():
    try:
        source_file = request.form['source-file']
        destination_folder = request.form['destination-folder']
        if source_file and destination_folder:
            # Copy file within S3 bucket
            s3.copy_object(Bucket=BUCKET_NAME, CopySource=f"{BUCKET_NAME}/{source_file}", Key=(destination_folder + '/' + os.path.basename(source_file)))
        return redirect(url_for('index'))
    except Exception as e:
            return render_template('error.html', error=str("Unable to COPY file, Select file & folder properly")), 500


#To move file from one folder to another folder
@app.route('/move-file', methods=['POST'])
def move_file():
    try:
        source_file = request.form['source-file']
        destination_folder = request.form['destination-folder']
        if source_file and destination_folder:
            # Move file within S3 bucket (copy then delete)
            s3.copy_object(Bucket=BUCKET_NAME, CopySource=f"{BUCKET_NAME}/{source_file}", Key=(destination_folder + '/' + os.path.basename(source_file)))
            s3.delete_object(Bucket=BUCKET_NAME, Key=source_file)
        return redirect(url_for('index'))
    except Exception as e:
        return render_template('error.html', error=str("Unable to MOVE file,Select file & folder properly")), 500

#if no bucket exist then it will redirect to error page which also give option to create bucket
@app.route('/create-bucket-in-none-case', methods=['POST'])
def create_new_bucket():
    try:
        bucket_name = request.form['bucket-name']
        if bucket_name:
            # Create S3 bucket
            s3.create_bucket(Bucket=bucket_name)
            return render_template('success.html')
        else:
            return render_template('error.html', error="Bucket name is required."), 400
    except Exception as e:
        return render_template('no_bucket_case.html', error=str("Unable to create bucket. Please try again."))


if __name__ == '__main__':
    app.run(debug=True)
