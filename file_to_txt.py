import os
import sys

def copy_files_to_txt(directory, output_directory=""):
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if not os.path.exists(output_directory) and not os.path.isdir(output_directory):
            output_directory = directory
            return

        # Skip if it's a directory
        if not os.path.isfile(filepath):
            continue

        # Read original file contents
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
            contents = infile.read()

        # Create output .txt file with same base name
        base_name = os.path.splitext(filename)[0]
        out_filename = f"{base_name}.txt"
        out_filepath = os.path.join(output_directory, out_filename)

        with open(out_filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(contents)

        print(f"Copied: {filename} -> {out_filename}")

if __name__ == "__main__":
    

    target_directory = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else ""
    if not os.path.isdir(target_directory):
        print("Error: Provided path is not a directory.")
        sys.exit(1)

    copy_files_to_txt(target_directory, output_directory=output_dir)
