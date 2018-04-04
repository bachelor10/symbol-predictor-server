from PIL import Image
import os, random


def split_images(pathname, train_pathname, validation_pathname, validation=0.16):
    for dir_name in os.listdir(pathname):
        sub_dir = pathname + '/' + dir_name
        print(sub_dir)
        for subdir_filename in os.listdir(sub_dir):
            img = Image.open(sub_dir + '/' + subdir_filename)

            if random.random() < validation:
                img_dir = validation_pathname + '/' + dir_name
            else:
                img_dir = train_pathname + '/' + dir_name
            
            if not os.path.exists(img_dir):
                os.makedirs(img_dir)

            img.save(img_dir + '/' + subdir_filename)
        

split_images(os.getcwd() + '/images_unfiltered', os.getcwd() + '/unfiltered_training_data',  os.getcwd() + '/unfiltered_validation_data')