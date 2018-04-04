from PIL import Image
import os, random, uuid


def resize_img(input_pathname, output_pathname, new_size, max_entries=100000, validation=0.15):
    count = 0
    for dir_name in os.listdir(input_pathname):
        sub_dir = input_pathname + '/' + dir_name
        for subdir_filename in os.listdir(sub_dir):

            img = Image.open(sub_dir + '/' + subdir_filename)
            img.thumbnail(new_size)


            new_dir = output_pathname + '/' + dir_name + '/'

            new_filename = new_dir + dir_name + '_' + str(uuid.uuid4()) + '.png'
            
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)

            img.save(new_filename)
            count += 1

            if count > max_entries: 
                count = 0
                break
        

resize_img(os.getcwd() + '/origin_jpg', os.getcwd() + '/images_unfiltered', [26, 26], max_entries=25000)