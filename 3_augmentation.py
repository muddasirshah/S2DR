import os
from geotile import GeoTile
from pathlib import Path
from tqdm import tqdm
import numpy as np
from PIL import Image
import rasterio

def augment_patch_pair(msi_path, naip_path, output_dir_msi, output_dir_naip, prefix, tile_size=256):
    """
    Augment a pair of MSI and NAIP patches with flip techniques and save as GeoTIFF.
    
    Args:
        msi_path (str): Path to the input MSI GeoTIFF patch
        naip_path (str): Path to the input NAIP GeoTIFF patch
        output_dir_msi (str): Directory to save augmented MSI patches
        output_dir_naip (str): Directory to save augmented NAIP patches
        prefix (str): Prefix for output filenames (e.g., 2019-07-13_p0)
        tile_size (int): Size of the patch (default: 256)
    Returns:
        bool: True if augmentation was successful, False if skipped
    """
    try:
        # Open MSI GeoTIFF
        with rasterio.open(msi_path) as src_msi:
            msi_array = src_msi.read()  # Shape: (bands, height, width)
            msi_profile = src_msi.profile

        # Open NAIP GeoTIFF
        with rasterio.open(naip_path) as src_naip:
            naip_array = src_naip.read()  # Shape: (bands, height, width)
            naip_profile = src_naip.profile

        # Validate band count
        if msi_array.shape[0] != 3:
            print(f"Skipping {msi_path}: Expected 3 bands, got {msi_array.shape[0]}")
            return False
        if naip_array.shape[0] != 3:
            print(f"Skipping {naip_path}: Expected 3 bands, got {naip_array.shape[0]}")
            return False

        # Check zero-pixel ratio
        msi_total_pixels = msi_array.size
        msi_zero_pixels = np.sum(msi_array == 0)
        msi_zero_ratio = msi_zero_pixels / msi_total_pixels
        naip_total_pixels = naip_array.size
        naip_zero_pixels = np.sum(naip_array == 0)
        naip_zero_ratio = naip_zero_pixels / naip_total_pixels

        if msi_zero_ratio > 0.1:
            print(f"Skipping {msi_path}: {msi_zero_ratio:.2%} zero pixels (>10%)")
            return False
        if naip_zero_ratio > 0.1:
            print(f"Skipping {naip_path}: {naip_zero_ratio:.2%} zero pixels (>10%)")
            return False

        # Transpose arrays to (height, width, bands) for PIL
        msi_array = np.transpose(msi_array, (1, 2, 0))
        naip_array = np.transpose(naip_array, (1, 2, 0))

        # Convert to PIL Images
        msi_img = Image.fromarray(msi_array)
        naip_img = Image.fromarray(naip_array)

        # Apply transformations to both MSI and NAIP
        transformations = [
            ("_0", lambda img: img),  # Original
            ("_flip_h", lambda img: img.transpose(Image.FLIP_LEFT_RIGHT)),  # Horizontal Flip
            ("_flip_v", lambda img: img.transpose(Image.FLIP_TOP_BOTTOM)),  # Vertical Flip
            ("_flip_hv", lambda img: img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.FLIP_TOP_BOTTOM)),  # H then V
            ("_flip_vh", lambda img: img.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)),  # V then H
        ]

        for suffix, transform in transformations:
            # Transform and save MSI
            msi_transformed = transform(msi_img)
            save_geotiff(msi_transformed, output_dir_msi, f"{prefix}_msi{suffix}", msi_profile)

            # Transform and save NAIP
            naip_transformed = transform(naip_img)
            save_geotiff(naip_transformed, output_dir_naip, f"{prefix}_naip{suffix}", naip_profile)

        return True
    except Exception as e:
        print(f"Failed to process pair {prefix}: {str(e)}")
        return False

def save_geotiff(img, output_dir, suffix, profile):
    """
    Save a PIL Image as GeoTIFF with the given profile.
    
    Args:
        img (PIL.Image): Image to save
        output_dir (str): Directory to save the GeoTIFF
        suffix (str): Suffix for the filename
        profile (dict): Rasterio profile for GeoTIFF
    """
    array = np.array(img).transpose((2, 0, 1))  # Convert back to (bands, height, width)
    output_path = os.path.join(output_dir, f"{suffix}.tif")
    os.makedirs(output_dir, exist_ok=True)
    try:
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(array)
    except Exception as e:
        print(f"Failed to save {output_path}: {str(e)}")

def find_naip_match(msi_filename, naip_files):
    """
    Find a matching NAIP file for an MSI file by comparing date and patch number.
    
    Args:
        msi_filename (str): MSI filename (e.g., 2019-07-13_msi_msi_p0.tif)
        naip_files (list): List of NAIP filenames
    Returns:
        str or None: Matching NAIP filename or None if no match
    """
    # Extract date and patch number from MSI filename
    msi_parts = msi_filename.split('_')
    if len(msi_parts) < 4:
        print(f"Invalid MSI filename format: {msi_filename}")
        return None
    date = msi_parts[0]  # e.g., 2019-07-13
    patch = msi_parts[3].split('.')[0]  # e.g., p0
    match_key = f"{date}_naip_naip_{patch}.tif"

    if match_key in naip_files:
        return match_key
    print(f"No NAIP match for {msi_filename}: Expected {match_key}")
    return None

def process_geotiffs(input_dir, output_dir, tile_size=256, stride=256):
    """
    Process paired MSI and NAIP GeoTIFF patches for augmentation.
    
    Args:
        input_dir (str): Directory containing msi and naip subfolders
        output_dir (str): Directory to save augmented patches
        tile_size (int): Size of each patch (default: 256)
        stride (int): Stride for patch generation (default: 256)
    """
    # Use absolute path for input directory
    input_dir = os.path.abspath(os.path.join(os.path.expanduser("~"), "Desktop", "s2dr", "2_model_training_data", "gtiff"))
    
    # Create output directories
    aug_output = os.path.abspath(os.path.join(os.path.expanduser("~"), "Desktop", "s2dr", output_dir, "augmentation"))
    output_dir_msi = os.path.join(aug_output, "msi")
    output_dir_naip = os.path.join(aug_output, "naip")
    os.makedirs(output_dir_msi, exist_ok=True)
    os.makedirs(output_dir_naip, exist_ok=True)
    
    # Get MSI and NAIP file lists
    msi_path = os.path.join(input_dir, "msi")
    naip_path = os.path.join(input_dir, "naip")
    
    if not (os.path.exists(msi_path) and os.path.exists(naip_path)):
        print(f"MSI or NAIP directory not found in {input_dir}")
        return
    
    # Get MSI and NAIP files
    msi_files = [f for f in os.listdir(msi_path) if f.endswith(".tif")]
    naip_files = [f for f in os.listdir(naip_path) if f.endswith(".tif")]
    processed_pairs = 0
    skipped_pairs = 0
    
    for msi_file in tqdm(msi_files, desc="Augmenting MSI-NAIP pairs"):
        # Find matching NAIP file
        naip_file = find_naip_match(msi_file, naip_files)
        if naip_file:
            msi_full_path = os.path.join(msi_path, msi_file)
            naip_full_path = os.path.join(naip_path, naip_file)
            # Create a clean prefix for output (e.g., 2019-07-13_p0)
            msi_parts = msi_file.split('_')
            prefix = f"{msi_parts[0]}_{msi_parts[3].split('.')[0]}"
            # Augment the pair
            success = augment_patch_pair(
                msi_path=msi_full_path,
                naip_path=naip_full_path,
                output_dir_msi=output_dir_msi,
                output_dir_naip=output_dir_naip,
                prefix=prefix,
                tile_size=tile_size
            )
            if success:
                processed_pairs += 1
                print(f"Processed pair: MSI={msi_file}, NAIP={naip_file}")
            else:
                skipped_pairs += 1
                print(f"Skipped pair due to invalid data: MSI={msi_file}, NAIP={naip_file}")
        else:
            skipped_pairs += 1
    
    print(f"Processed {processed_pairs} pairs, skipped {skipped_pairs} pairs")

def main():
    # Configuration
    INPUT_DIR = "2_model_training_data/gtiff"
    OUTPUT_DIR = "4_model_training_data"
    
    try:
        process_geotiffs(INPUT_DIR, OUTPUT_DIR)
        print(f"Augmented patches generated and saved to {OUTPUT_DIR}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()