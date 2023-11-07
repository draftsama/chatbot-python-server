


#get all images (png | jpg) in folder and order them by date
import os


def reduct_images(path, limit_image = 20):
    images = []
    
    for f in os.listdir(path):
        if f.endswith(('.png', '.jpg')):
            images.append(f)
    images.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)))
    
    #if image count > 5 then remove another images
    if len(images) > limit_image:
        for i in range(len(images) - limit_image):
            os.remove(os.path.join(path, images[i]))
            images.pop(i)
    

    