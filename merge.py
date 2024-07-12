from PIL import Image
import os

def remove_padding_and_concatenate(thermal_path, rgb_path, padding):
    # Open thermal and RGB images
    thermal_img = Image.open(thermal_path)
    rgb_img = Image.open(rgb_path)
    
    # Get image dimensions
    width_t, height_t = thermal_img.size
    width_rgb, height_rgb = rgb_img.size
    
    # Remove padding from thermal image
    thermal_img = thermal_img.crop((0, padding, width_t, height_t - padding))
    
    # Remove padding from RGB image
    rgb_img = rgb_img.crop((0, padding, width_rgb, height_rgb - padding))
    
    # Concatenate images side by side
    new_width = thermal_img.width + rgb_img.width
    new_height = max(thermal_img.height, rgb_img.height)
    new_img = Image.new('RGB', (new_width, new_height))
    new_img.paste(thermal_img, (0, 0))
    new_img.paste(rgb_img, (thermal_img.width, 0))
    
    return new_img

def process_directory(directory, padding):
    # Iterate over files in the directory
    for filename in os.listdir(directory):
        if filename.endswith("_thermal.png"):
            thermal_path = os.path.join(directory, filename)
            rgb_path = os.path.join(directory, filename.replace("_thermal.png", "_rgb.png"))
            
            if os.path.exists(rgb_path):
                # Process the pair
                print(f"Processing pair: {thermal_path} and {rgb_path}")
                result_img = remove_padding_and_concatenate(thermal_path, rgb_path, padding)
                
                # Save the result with a new name
                output_filename = filename.replace("_thermal.png", "_combined.png")
                output_path = os.path.join(directory, output_filename)
                result_img.save(output_path)
                print(f"Saved combined image: {output_path}")
            else:
                print(f"Warning: RGB image {rgb_path} not found for {thermal_path}")

if __name__ == "__main__":  
    directory_path = "./Spill"
    padding_to_remove = 64  # Set the number of pixels to remove from top and bottom
    
    process_directory(directory_path, padding_to_remove)
                                                              