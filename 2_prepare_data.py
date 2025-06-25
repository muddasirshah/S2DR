import os
from geotile import GeoTile
from pathlib import Path
from tqdm import tqdm

def process_geotiffs(input_dir, output_dir, tile_size=256, stride=256):
    """
    Process geotiff files to generate 256x256 patches in GeoTIFF format.
    
    Args:
        input_dir (str): Directory containing msi and naip subfolders
        output_dir (str): Directory to save processed patches
        tile_size (int): Size of each patch (default: 256)
        stride (int): Stride for patch generation (default: 256)
    """
    # Create output directory
    gtiff_output = os.path.join(output_dir, "gtiff")
    os.makedirs(os.path.join(gtiff_output, "msi"), exist_ok=True)
    os.makedirs(os.path.join(gtiff_output, "naip"), exist_ok=True)
    
    # Process each block folder with a single progress bar
    block_folders = [f for f in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, f))]
    for block_folder in tqdm(block_folders, desc="Processing blocks"):
        block_path = os.path.join(input_dir, block_folder)
        if os.path.isdir(block_path):
            msi_path = os.path.join(block_path, "msi")
            naip_path = os.path.join(block_path, "naip")
            
            if os.path.exists(msi_path) and os.path.exists(naip_path):
                msi_files = [f for f in os.listdir(msi_path) if f.endswith(".tif")]
                naip_files = [f for f in os.listdir(naip_path) if f.endswith(".tif")]
                
                # Match msi and naip files by date
                for msi_file, naip_file in zip(msi_files, naip_files):
                    if msi_file.split("_")[0] == naip_file.split("_")[0]:  # Assuming date is first part
                        msi_full_path = os.path.join(msi_path, msi_file)
                        naip_full_path = os.path.join(naip_path, naip_file)
                        
                        # Process MSI
                        gt_msi = GeoTile(msi_full_path)
                        gt_msi.generate_tiles(output_folder=os.path.join(gtiff_output, "msi"), 
                                           tile_x=tile_size, tile_y=tile_size, 
                                           stride_x=stride, stride_y=stride, 
                                           prefix=f"{msi_file.split('.')[0]}_msi_p", 
                                           save_tiles=True)
                        gt_msi.convert_nan_to_zero()
                        gt_msi.normalize_tiles()
                        gt_msi.close()
                        
                        # Process NAIP
                        gt_naip = GeoTile(naip_full_path)
                        gt_naip.generate_tiles(output_folder=os.path.join(gtiff_output, "naip"), 
                                            tile_x=tile_size, tile_y=tile_size, 
                                            stride_x=stride, stride_y=stride, 
                                            prefix=f"{naip_file.split('.')[0]}_naip_p", 
                                            save_tiles=True)
                        gt_naip.convert_nan_to_zero()
                        gt_naip.normalize_tiles()
                        gt_naip.close()

def main():
    # Configuration
    INPUT_DIR = "1_Downloads/superresolution"
    OUTPUT_DIR = "2_model_training_data"
    
    try:
        process_geotiffs(INPUT_DIR, OUTPUT_DIR)
        print(f"Patches generated and saved to {OUTPUT_DIR}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()