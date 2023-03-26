import concurrent.futures
import subprocess
from pathlib import Path
import time
from collections import Counter
import urllib.parse
import shutil
import uuid
from datetime import datetime
import asyncio

directory_path = Path(r"D:\pathtodirectory")
temporary_path = directory_path.joinpath("#Temporary")
log_file = Path(r"C:\logs\cjxl log.txt")
log_file_error = Path(r"C:\logs\cjxl error log.txt")

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
    destination_file = file.with_suffix('.jxl')
    temp = "_temp"
	
    output_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Move the image to the temporary directory
    file.rename(output_file)

    async def compress_and_decode():
        try:
            # Compress the image using cjxl
            subprocess.run(["cjxl", str(output_file), "--distance", "0", "--effort", "9", str(temporary_file)], stderr=subprocess.PIPE, check=True)

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
                    temporary_file.rename(destination_file)
					# Removes the original moved image file and output_file2 temp file
                    decoded_file.unlink()
                    output_file.unlink()
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
        
            total_counter['processed'] += 1
            print(f"Current images processed: {total_counter['processed']}/{total_counter['submitted']}")
        except subprocess.CalledProcessError as error:
            # Log the error message and continue processing remaining files
            error_msg = error.stderr.decode('utf-8').strip()
            with log_file_error.open(mode='a', encoding='utf-8') as f:
                current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                f.write(f"{current_time} | {input_file} - Failed: {error_msg}\n{'-' * 260}\n")
                print(f"{input_file} - Failed: {error_msg}")
                # Preserve the source file if subprocess returns an error
                output_file.rename(destination_file)
        except Exception as e:
            # Log any other exceptions and raise them
            with log_file_error.open(mode='a', encoding='utf-8') as f:
                current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                f.write(f"{current_time} | {input_file} - Failed: {str(e)}\n{'-' * 260}\n")
                print(f"{input_file} - Failed: {str(e)}")
                # Preserve the source file if there is any other exception
                output_file.rename(destination_file)
            raise
        finally:
            # Move the image back to the original location and delete the temporary files
            if output_file.exists() and result.returncode == 0:
                output_file.rename(file)
            elif destination_file.exists() and result.returncode != 0:
                destination_file.rename(file)
            if temporary_file.exists():
                temporary_file.unlink
            
            # Move the image back to the original location
            destination_file.rename(destination_file.with_suffix('.jxl'))
    asyncio.run(compress_and_decode())
	
total_counter = Counter()
start_time = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=23) as executor:
    for file in directory_path.glob('**/*'):
        if file.is_file() and file.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp', '.webp'):
            executor.submit(process_image, file)
            total_counter['submitted'] += 1

elapsed_time = time.time() - start_time
hours, remainder = divmod(elapsed_time, 3600)
minutes, seconds = divmod(remainder, 60)

# Remove the temporary directory if it exists
if temporary_path.exists():
    shutil.rmtree(temporary_path)

with log_file.open(mode='a', encoding='utf-8') as f:
    f.write(f"Total images submitted: {total_counter['submitted']}\n")
    f.write(f"Total images processed: {total_counter['processed']}\n")
    f.write(f"Total elapsed time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds\n{'-' * 260}\n")
print(f"Total images submitted: {total_counter['submitted']}")
print(f"Total images processed: {total_counter['processed']}")
print(f"Total elapsed time: {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds")
input("Press Enter to exit...")
