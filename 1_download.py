import os
from google.cloud import storage
from pathlib import Path

def download_bucket(bucket_name, project_id, destination_dir):
    """
    Download all files from a GCS bucket to a local directory, preserving folder structure.
    
    Args:
        bucket_name (str): Name of the GCS bucket
        project_id (str): Google Cloud project ID
        destination_dir (str): Local directory to save files
    """
    # Initialize GCS client
    client = storage.Client(project=project_id)
    bucket = client.get_bucket(bucket_name)
    
    # Create destination directory if it doesn't exist
    Path(destination_dir).mkdir(parents=True, exist_ok=True)
    
    # List all objects in the bucket
    blobs = bucket.list_blobs()
    
    # Download each file
    for blob in blobs:
        # Get the relative path of the file
        file_path = blob.name
        
        # Create the full local path
        local_path = os.path.join(destination_dir, file_path)
        
        # Create any necessary directories
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Download the file
        print(f"Downloading {file_path} to {local_path}")
        blob.download_to_filename(local_path)
    
    print(f"All files downloaded to {destination_dir}")

def main():
    # Configuration
    BUCKET_NAME = "farmdar_rnd"
    PROJECT_ID = "ee-farmdar"
    DESTINATION_DIR = "1_Downloads"
    
    try:
        download_bucket(BUCKET_NAME, PROJECT_ID, DESTINATION_DIR)
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()