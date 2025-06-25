import os
from google.cloud import storage
from pathlib import Path

def upload_folder_to_gcs(bucket_name, source_folder, destination_folder, project_id):
    """
    Upload a local folder to a GCS bucket with a specified destination folder.
    
    Args:
        bucket_name (str): Name of the GCS bucket
        source_folder (str): Local folder to upload
        destination_folder (str): Destination folder in GCS
        project_id (str): Google Cloud project ID
    """
    # Initialize GCS client
    client = storage.Client(project=project_id)
    bucket = client.get_bucket(bucket_name)
    
    # Ensure source folder exists
    source_folder = os.path.abspath(source_folder)
    if not os.path.exists(source_folder):
        raise FileNotFoundError(f"Source folder {source_folder} does not exist")
    
    # Walk through the source folder
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            local_path = os.path.join(root, file)
            # Calculate the relative path from the source folder
            relative_path = os.path.relpath(local_path, source_folder)
            # Destination blob path including the destination folder
            destination_blob_name = os.path.join(destination_folder, relative_path).replace(os.sep, '/')
            
            # Upload the file
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(local_path)
            print(f"Uploaded {local_path} to {destination_blob_name}")

def main():
    # Configuration
    BUCKET_NAME = "YOUR_GCP_BUCKET_NAME"
    PROJECT_ID = "YOUR_GCP_PROJECT_NAME"
    SOURCE_FOLDER = "compressed"
    DESTINATION_FOLDER = "SR/compressed"
    
    try:
        upload_folder_to_gcs(BUCKET_NAME, SOURCE_FOLDER, DESTINATION_FOLDER, PROJECT_ID)
        print(f"Folder {SOURCE_FOLDER} uploaded to gs://{BUCKET_NAME}/{DESTINATION_FOLDER}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()
