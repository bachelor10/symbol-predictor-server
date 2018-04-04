from PIL import Image
import os, random


def filter_img(train, validation, new_train, new_validation, min_greytone):
    count = 0

    if not os.path.exists(new_train):
        os.makedirs(new_train)

    for dir_name in os.listdir(train):
        sub_dir = train + '/' + dir_name

        if not os.path.exists(new_train + '/' + dir_name):
            os.makedirs(new_train + '/' + dir_name)
        
        for subdir_filename in os.listdir(sub_dir):
            im = Image.open(train + '/' + dir_name + '/' + subdir_filename)
            pixelMap = im.load()
            img = Image.new( im.mode, im.size)
            pixelsNew = img.load()
            
            for i in range(img.size[0]):
                for j in range(img.size[1]):
                    if pixelMap[i,j] < min_greytone:
                        pixelsNew[i,j] = 0
                    else:
                        pixelsNew[i,j] = 255
            
            img.save(new_train + '/' + dir_name + '/' + subdir_filename)

    if not os.path.exists(new_validation):
        os.makedirs(new_validation)

    for dir_name in os.listdir(validation):
        sub_dir = validation + '/' + dir_name

        if not os.path.exists(new_validation + '/' + dir_name):
            os.makedirs(new_validation + '/' + dir_name)
        
        for subdir_filename in os.listdir(sub_dir):
            im = Image.open(validation + '/' + dir_name + '/' + subdir_filename)
            pixelMap = im.load()
            img = Image.new( im.mode, im.size)
            pixelsNew = img.load()
            
            for i in range(img.size[0]):
                for j in range(img.size[1]):
                    if pixelMap[i,j] < min_greytone:
                        pixelsNew[i,j] = 0
                    else:
                        pixelsNew[i,j] = 255
            
            img.save(new_validation + '/' + dir_name + '/' + subdir_filename)



filter_img(os.getcwd() + '/unfiltered_training_data', os.getcwd() + '/unfiltered_validation_data', os.getcwd() + '/training_data', os.getcwd() + '/validation_data', 180)