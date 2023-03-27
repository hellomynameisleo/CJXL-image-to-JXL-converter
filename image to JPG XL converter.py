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
    destination_file = file.with_suffix(file.suffix)
    temp = "_temp"
	
    output_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file.parent.mkdir(parents=True, exist_ok=True)
    
    file.rename(output_file)

    async def compress_and_decode():
        try:
            subprocess.run(["cjxl", str(output_file), "--distance", "0", "--effort", "9", str(temporary_file)], stderr=subprocess.PIPE, check=True)
        
        except subprocess.CalledProcessError as error:
            with log_file_error.open(mode='a', encoding='utf-8') as f:
                current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                error_msg = error.stderr.decode('utf-8').strip()
                f.write(f"{current_time} | {input_file} - Failed: {error_msg}\n{'-' * 260}\n")
                print(f"{input_file} - Failed: {error_msg}")
                output_file.rename(destination_file)
                print(f"Moving {output_file}")
                temporary_file.unlink()
        except Exception as e:
            with log_file_error.open(mode='a', encoding='utf-8') as f:
                current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                f.write(f"{current_time} | {input_file} - Failed: {str(e)}\n{'-' * 260}\n")
                print(f"{input_file} - Failed: {str(e)}")
                output_file.rename(destination_file)
                temporary_file.unlink()
            raise
        else:
            output_file2 = output_file.with_name(output_file.stem + temp + output_file.suffix)
            decoded_file = output_file2.with_suffix(file.suffix)
            subprocess.run(["djxl", str(temporary_file), str(decoded_file)], stderr=subprocess.PIPE, check=True)
            compare_cmd = ['magick', 'compare', '-metric', 'ae', str(output_file), str(decoded_file), 'NUL']
            result = subprocess.run(compare_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                with log_file.open(mode='a', encoding='utf-8') as f:
                    current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                    f.write(f"{current_time} | {destination_file} - Done: magick compare returned {result.returncode}\n")
                    print(f"{destination_file} - Done")
                    temporary_file.rename(destination_file.with_suffix('.jxl'))
                    decoded_file.unlink()
                    output_file.unlink()
                total_counter['processed'] += 1
                print(f"Current images processed: {total_counter['processed']}/{total_counter['submitted']}")
            else:
                with log_file_error.open(mode='a', encoding='utf-8') as f:
                    current_time = datetime.now().strftime("Date=%d-%m-%Y | Time=%H:%M:%S")
                    f.write(f"{current_time} | {input_file} - Failed: magick compare returned {result.returncode}\n{'-' * 260}\n")
                    print(f"{input_file} - Failed: magick compare returned {result.returncode}")
                    output_file.rename(destination_file)
                    decoded_file.unlink()
                    temporary_file.unlink()
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
