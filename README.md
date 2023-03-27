# CJXL-image-to-JXL-converter
converts all jpg, jpeg, webp and png images in a directory recursively to JXL

Will skip files with ascii filenames in them as CJXL can't handle it

Will work with filepaths in the directory with ascii using a temp folder and move

Will create 2 seperate log file with a normal one and a error log file

Has multi process, just change the default amount of workers in the script

Will only work with lossless mode -d 0 or -q 100 as it uses imagemagick

Will use decode the processed jxl image and use imagemagick magick compare to verify the image is lossless and if not keep the original image file and discard the processed jxl image

If CJXL throws an error it will keep the original image



How to use:
images must be in a subdirectory to work, don't use images right in the directory path or it won't work and the images will be deleted.
