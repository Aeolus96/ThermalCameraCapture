import os
import random
import shutil

# This Script should be run in a directory with the following structure:
# root directory -> spill directory & no-spill directory 

# # Set the root directory where your original folders are located
root_dir = './Combined'  # change this to your root path if different

# Names of the classes
classes = ['spill', 'no-spill']

# Split ratios
train_ratio = 0.7
val_ratio = 0.2
test_ratio = 0.1

# Destination folders
split_names = ['train', 'validation', 'test']

# Create the new folder structure
for split in split_names:
    for cls in classes:
        dir_path = os.path.join(root_dir, split, cls)
        os.makedirs(dir_path, exist_ok=True)

# Function to split files into train/val/test
def split_files(file_list, train_ratio, val_ratio, test_ratio):
    random.shuffle(file_list)
    n = len(file_list)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    train_files = file_list[:train_end]
    val_files = file_list[train_end:val_end]
    test_files = file_list[val_end:]
    return train_files, val_files, test_files

# Process each class folder
for cls in classes:
    src_dir = os.path.join(root_dir, cls)
    files = [f for f in os.listdir(src_dir) if os.path.isfile(os.path.join(src_dir, f))]

    train_files, val_files, test_files = split_files(files, train_ratio, val_ratio, test_ratio)

    # Move files to train
    for f in train_files:
        src_path = os.path.join(src_dir, f)
        dst_path = os.path.join(root_dir, 'train', cls, f)
        shutil.move(src_path, dst_path)

    # Move files to validation
    for f in val_files:
        src_path = os.path.join(src_dir, f)
        dst_path = os.path.join(root_dir, 'validation', cls, f)
        shutil.move(src_path, dst_path)

    # Move files to test
    for f in test_files:
        src_path = os.path.join(src_dir, f)
        dst_path = os.path.join(root_dir, 'test', cls, f)
        shutil.move(src_path, dst_path)

print("Done! Files have been split and moved.")
