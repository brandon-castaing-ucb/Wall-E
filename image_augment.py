import sys, os, re, traceback
from os.path import isfile
from multiprocessing.dummy import Pool
from augmentations.fliph import FlipH
from augmentations.zoom import Zoom
from augmentations.blur import Blur
from augmentations.noise import Noise
from augmentations.translate import Translate
from skimage.io import imread, imsave

class ImageAugment:
    EXTENSIONS = ['png', 'jpg', 'jpeg', 'bmp']
    WORKER_COUNT = max(4, 1)
    OPERATIONS = [FlipH, Translate, Noise, Zoom, Blur]

    '''
    ## Leveraging image augmnetation code from HW7 ##
    Augmented files will have names matching the regex below, eg

        original__rot90__crop1__flipv.jpg

    '''
    AUGMENTED_FILE_REGEX = re.compile('^.*(__.+)+\\.[^\\.]+$')
    EXTENSION_REGEX = re.compile('|'.join(map(lambda n : '.*\\.' + n + '$', EXTENSIONS)))

    thread_pool = None
    count = 0

    @staticmethod
    def build_augmented_file_name(original_name, ops):
        root, ext = os.path.splitext(original_name)
        result = root
        for op in ops:
            result += '__' + op.code
        return result + ext

    @staticmethod
    def work(d, f, op_lists):
        try:
            in_path = os.path.join(d,f)
            for op_list in op_lists:
                out_file_name = ImageAugment.build_augmented_file_name(f, op_list)
                if isfile(os.path.join(d,out_file_name)):
                    continue
                img = imread(in_path)
                for op in op_list:
                    img = op.process(img)
                imsave(os.path.join(d, out_file_name), img)

                ImageAugment.count += 1
        except:
            traceback.print_exc(file=sys.stdout)

    @staticmethod
    def process(dir, file, op_lists):
        ImageAugment.thread_pool.apply_async(ImageAugment.work, (dir, file, op_lists))

    @staticmethod
    def execute(image_dir, op_codes):
        print('Starting image processing...')

        if not os.path.isdir(image_dir):
            print('Invalid image directory: {}'.format(image_dir))
            return None

        op_lists = []
        for op_code_list in op_codes:
            op_list = []
            for op_code in op_code_list.split(','):
                op = None
                for op in ImageAugment.OPERATIONS:
                    op = op.match_code(op_code)
                    if op:
                        op_list.append(op)
                        break

                if not op:
                    print('Unknown operation {}'.format(op_code))
                    return None
            op_lists.append(op_list)

        ImageAugment.thread_pool = Pool(ImageAugment.WORKER_COUNT)
        print('Thread pool initialised with {} worker{}'.format(ImageAugment.WORKER_COUNT, '' if ImageAugment.WORKER_COUNT == 1 else 's'))

        matches = []
        for dir_info in os.walk(image_dir):
            dir_name, _, file_names = dir_info
            print(f"Processing {image_dir}/{dir_name}...")

            for file_name in file_names:
                if ImageAugment.EXTENSION_REGEX.match(file_name):
                    if ImageAugment.AUGMENTED_FILE_REGEX.match(file_name):
                        print(f"Skipped Augmentation for {dir_name}/{file_name}")
                    else:
                        ImageAugment.process(dir_name, file_name, op_lists)
                else:
                    print(f"Skipped {dir_name}/{file_name}")

        print("Waiting for workers to complete...")
        ImageAugment.thread_pool.close()
        ImageAugment.thread_pool.join()

        print(f"Processed Images: {ImageAugment.count}")

if __name__ == '__main__':
    ImageAugment().execute("../data", ["fliph","noise_0.01","noise_0.03","noise_0.05","trans_10_10","trans_20_20","blur_1.0","blur_2.0"])
