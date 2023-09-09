'''
Determines if an image is greyscale, black & white,
or color.

ACKNOWLEDGEMENTS:
This algorithm is from Stack Exchange by author Noah Whitman.
This algorithm was posted in April 2014 and is licensed under
Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0).

Link to license: https://creativecommons.org/licenses/by-sa/3.0/
Link to original post: https://stackoverflow.com/questions/20068945/detect-if-image-is-color-grayscale-or-black-and-white-using-python

I have made some modifications to the original code.
'''

#determines if an image is black an white
from PIL import Image, ImageStat

def detect_color_image(file, thumb_size=40, MSE_cutoff=10, adjust_color_bias=True):
    #open the image
    pil_img = Image.open(file)
    #get color data from image
    bands = pil_img.getbands()
    if bands == ('R','G','B') or bands== ('R','G','B','A'):
        #generate smaller image for analysis
        thumb = pil_img.resize((thumb_size,thumb_size))
        SSE, bias = 0, [0,0,0]
        if adjust_color_bias:
            bias = ImageStat.Stat(thumb).mean[:3]
            bias = [b - sum(bias)/3 for b in bias ]
        #calculate sum of squared error
        for pixel in thumb.getdata():
            mu = sum(pixel)/3
            SSE += sum((pixel[i] - mu - bias[i])*(pixel[i] - mu - bias[i]) for i in [0,1,2])
        #calculate mean square error for image
        MSE = float(SSE)/(thumb_size*thumb_size)
        if MSE <= MSE_cutoff:
            #image is greyscale
            return 1
        else:
            #image is color
            return 2
    elif len(bands)==1:
        #image is back and white
        return 3
    else:
        #an error occured/image color cannot be determined
        return -1
