import concurrent.futures
import subprocess
from pathlib import Path
import time
from collections import Counter
import shutil
import uuid
from datetime import datetime
import asyncio
import os

while True:
    confirmed = None
    max_workers_input_validation = None
    original_total_size = 0
    processed_total_size = 0

    while not confirmed:
        user_input = input("Enter the directory path to convert image files to .jxl: ")
        user_input = user_input.strip('"').strip("'")
        
        directory_path = Path(user_input)

        if not directory_path.exists() or not user_input:
            print(f"The directory '{directory_path}' does not exist. Please enter a valid path.")
        else:
            print(f"The directory '{directory_path}' has been validated.")
            while True:
                user_confirmation = input("Confirm directory to continue. (Y/N): ").lower()
                if user_confirmation == "n":
                    print ("Resetted inputted directory")
                    break
                elif user_confirmation == "y":
                    confirmed = True
                    break
                else:
                    print("Invalid input. Enter 'Y' or 'N'.")

    while True:
        max_workers = input("Input the number of max workers (Recommended number of CPU cores): ")
        if max_workers.isdigit():
            max_workers = int(max_workers)
            if max_workers > 0:
                break
            else:
                print(f"Invalid input, try again")
        else:
            print(f"Invalid input, try again")
    
    while True:
        effort = input("Input the effort processing setting (1-9): ")
        if effort.isdigit():
            effort = int(effort)
            if effort >= 1 and effort <= 9:
                break
            else:
                print(f"Invalid input, try again")
        else:
            print(f"Invalid input, try again")

    #calculate inputted directory foldersize
    for dirpath, _, filenames in os.walk(directory_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            original_total_size += os.path.getsize(file_path)

    current_time = datetime.now().strftime("Date=%Y-%m-%d & Time=%H.%M.%S")
    temporary_path = directory_path.joinpath("#Temporary")
    log_file = Path(fr"C:\Users\Leo\Documents\Gallery-dl\gallery-dl\mangadex\#Done\#Logs\cjxl log - {current_time}.txt")
    log_file_error = Path(fr"C:\Users\Leo\Documents\Gallery-dl\gallery-dl\mangadex\#Done\#Logs\cjxl error log - {current_time}.txt")

    current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
    with log_file_error.open(mode='a', encoding='utf-8') as f:
        f.write(f"{current_time} - Script started\n")
    with log_file.open(mode='a', encoding='utf-8') as f:
        f.write(f"{current_time} - Script started\n")
    print(f"{current_time} - Script started")

    def is_valid_filename(filename):
        try:
            filename.encode('ascii')
        except UnicodeEncodeError:
            return False
        else:
            return True

    def process_image(file):
        if not is_valid_filename(file.name):
            with log_file_error.open(mode='a', encoding='utf-8') as f:
                current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                f.write(f"{current_time} | {file} - Skipped (contains non-ASCII characters)\n{'-' * 260}\n")
                print(f"{file} - Skipped (contains non-ASCII characters)")
            return

        input_file = file
        unique_id = str(uuid.uuid4())
        output_file = temporary_path.joinpath(file.stem + "_" + unique_id + file.suffix)
        temporary_file = output_file.with_suffix('.jxl')
        destination_file = file.with_suffix(file.suffix)
        temp = "_temp"

        # Log the original and temporary file names
        with log_file.open(mode='a', encoding='utf-8') as f:
            current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
            f.write(f"{current_time} | '{input_file}' - Original File Name to '{output_file}' - Temporary File Name\n")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_file.parent.mkdir(parents=True, exist_ok=True)

        # Move the image to the temporary directory
        file.rename(output_file)

        async def compress_and_decode():
            try:
                subprocess.run(["cjxl", str(output_file), "--distance", "0", "--effort", f"{effort}", str(temporary_file)], stderr=subprocess.PIPE, check=True)

            except subprocess.CalledProcessError as error:
                with log_file_error.open(mode='a', encoding='utf-8') as f:
                    current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                    error_msg = error.stderr.decode('utf-8').strip()
                    f.write(f"{current_time} | {input_file} - Failed: {error_msg}\n{'-' * 260}\n")
                    print(f"{input_file} - Failed: {error_msg}")
                    # Preserve the source file if cjxl returns an error
                    output_file.rename(destination_file)
                    print(f"Moving {output_file}")
                    # Removes the output_file2 temp file and cjxl processed temporary_file file
                    temporary_file.unlink()
            except Exception as e:
                with log_file_error.open(mode='a', encoding='utf-8') as f:
                    current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                    f.write(f"{current_time} | {input_file} - Failed: {str(e)}\n{'-' * 260}\n")
                    print(f"{input_file} - Failed: {str(e)}")
                    # Preserve the source file if cjxl returns an error
                    output_file.rename(destination_file)
                    # Removes the output_file2 temp file and cjxl processed temporary_file file
                    temporary_file.unlink()
                raise
            else:
                # Creates an object called output_file2 with the work temp added to output_file, decodes the processed image from cjxl to the temporary file output_file2 with the same extension as output_file
                output_file2 = output_file.with_name(output_file.stem + temp + output_file.suffix)
                decoded_file = output_file2.with_suffix(file.suffix)
                subprocess.run(["djxl", str(temporary_file), str(decoded_file)], stderr=subprocess.PIPE, check=True)
                # Run magick compare command and log the result
                compare_cmd = ['magick', 'compare', '-metric', 'ae', str(output_file), str(decoded_file), 'NUL']
                result = subprocess.run(compare_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # If magick compare returns a 0 then move the cjxl processed temporary_file to the original file location
                if result.returncode == 0:
                    with log_file.open(mode='a', encoding='utf-8') as f:
                        current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                        f.write(f"{current_time} | {destination_file} - Done: magick compare returned {result.returncode}\n")
                        print(f"{destination_file} - Done")
                        temporary_file.rename(destination_file.with_suffix('.jxl'))
                        # Removes the original moved image file and output_file2 temp file
                        decoded_file.unlink()
                        output_file.unlink()
                    total_counter['processed'] += 1
                    print(f"Current images processed: {total_counter['processed']}/{total_counter['submitted']}")
                else:
                    with log_file_error.open(mode='a', encoding='utf-8') as f:
                        current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                        f.write(f"{current_time} | {input_file} - Failed: magick compare returned {result.returncode}\n{'-' * 260}\n")
                        print(f"{input_file} - Failed: magick compare returned {result.returncode}")
                        # Preserve the source file if magick compare returns an error
                        output_file.rename(destination_file)
                        # Removes the output_file2 temp file and cjxl processed temporary_file file
                        decoded_file.unlink()
                        temporary_file.unlink()
        asyncio.run(compress_and_decode())

    total_counter = Counter()
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for file in directory_path.glob('**/*'):
            if file.is_file() and file.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.webp'):
                executor.submit(process_image, file)
                total_counter['submitted'] += 1

    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    def format_size(size):
        # Define the possible units and their corresponding labels
        units = ['B', 'KB', 'MB', 'GB', 'TB']
    
        # Initialize the index and divide the size by 1024 until it's less than 1024
        index = 0
        while size >= 1024 and index < len(units) - 1:
            size /= 1024.0
            index += 1
    
        # Format the size with two decimal places and the appropriate unit
        return f"{size:.2f} {units[index]}"

    #calculate inputted directory foldersize after processing
    for dirpath, _, filenames in os.walk(directory_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            processed_total_size += os.path.getsize(file_path)
    total_size_difference = original_total_size - processed_total_size
    total_size_difference = format_size(total_size_difference)
    percentage_processed_to_original = (processed_total_size / original_total_size) * 100
    percentage_processed_to_original = f"{percentage_processed_to_original:.3f}%"

    # Remove the temporary directory if it exists
    if temporary_path.exists():
        shutil.rmtree(temporary_path)

    with log_file.open(mode='a', encoding='utf-8') as f:
        f.write(f"Total images submitted: {total_counter['submitted']}\n")
        f.write(f"Total images processed: {total_counter['processed']}\n")
        f.write(f"Total space saved: {total_size_difference} ({percentage_processed_to_original} of original size)\n")
        f.write(f"Total elapsed time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds\n{'-' * 260}\n")
    print(f"Total images submitted: {total_counter['submitted']}")
    print(f"Total images processed: {total_counter['processed']}")
    print(f"Total space saved: {total_size_difference} ({percentage_processed_to_original} of original size)")
    print(f"Total elapsed time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")
