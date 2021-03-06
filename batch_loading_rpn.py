from utils         import *
from sklearn.utils import shuffle



def load(file_names, is_testset=False):
    first_item = file_names[0].split('/')
    prefix = '/'.join(first_item[:-4])
    frame_num_list = ['/'.join(name.split('/')[-3:]) for name in file_names]

    train_tops = [np.load(os.path.join(prefix, 'top', file + '.npy')) for file in frame_num_list]

    if is_testset == True:
        train_gt_boxes3d = None
        train_gt_labels = None
    else:
        train_gt_boxes3d = [np.load(os.path.join(prefix, 'gt_boxes3d', file + '.npy')) for file in frame_num_list]

        train_gt_labels = [np.load(os.path.join(prefix, 'gt_labels', file + '.npy')) for file in frame_num_list]
    list = []

    for i in range(len(frame_num_list)):
        list.append( np.array(train_gt_labels[i][:,3]))
    return train_tops, list, train_gt_boxes3d


class batch_loading:
    def __init__(self, dir_path, dates_to_drivers=None, indice=None, cache_num=5, is_testset=False):
        self.dates_to_drivers = dates_to_drivers
        self.indice = indice
        self.cache_num = cache_num
        self.preprocess_path = dir_path
        self.is_testset = is_testset

        if indice is None:
            self.load_file_names = self.get_all_load_index(self.preprocess_path, self.dates_to_drivers, is_testset)
        else:
            self.load_file_names = indice
            self.load_once = True
        self.size = len(self.load_file_names)

        self.batch_start_index = 0

        # num_frame_used means how many frames are used in current batch, if all frame are used, load another batch
        self.num_frame_used = cache_num

        # current batch contents
        self.train_tops = []
        self.train_gt_labels = []
        self.train_gt_boxes3d = []
        self.current_batch_file_names = []

    def get_shape(self):

        # print("file name is here: ", self.load_file_names[0])
        train_tops, train_gt_labels, train_gt_boxes3d = load([self.load_file_names[0]], is_testset=self.is_testset)

        top_shape = train_tops[0].shape

        return top_shape

    def get_all_load_index(self, data_seg, dates_to_drivers, gt_included):

        check_preprocessed_data(data_seg, dates_to_drivers, gt_included)
        top_dir = os.path.join(data_seg, "top")
        # print('lidar data here: ', lidar_dir)
        load_indexs = []
        for date, drivers in dates_to_drivers.items():
            for driver in drivers:

                file_prefix = os.path.join(data_seg, "top", driver, date)
                driver_files = get_file_names(data_seg, "top", driver, date)
                if len(driver_files) == 0:
                    raise ValueError('Directory has no data starts from {}, please revise.'.format(file_prefix))

                name_list = [file.split('/')[-1].split('.')[0] for file in driver_files]
                name_list = [file.split('.')[0] for file in driver_files]
                load_indexs += name_list
        load_indexs = sorted(load_indexs)
        return load_indexs

    def load_test_frames(self, size, shuffled):
        # just load it once
        if self.load_once:
            if shuffled:
                self.load_file_names = shuffle(self.load_file_names)
            self.train_tops, self.train_gt_labels, self.train_gt_boxes3d = \
                load(self.load_file_names)
            self.num_frame_used = 0
            self.load_once = False
        # if there are still frames left
        self.current_batch_file_names = self.load_file_names
        frame_end = min(self.num_frame_used + size, self.cache_num)
        train_tops = self.train_tops[self.num_frame_used:frame_end]
        train_gt_labels = self.train_gt_labels[self.num_frame_used:frame_end]
        train_gt_boxes3d = self.train_gt_boxes3d[self.num_frame_used:frame_end]
        handle_id = self.current_batch_file_names[self.num_frame_used:frame_end]
        handle_id = ['/'.join(name.split('/')[-3:]) for name in handle_id]
        print("start index is here: ", self.num_frame_used)
        self.num_frame_used = frame_end
        if self.num_frame_used >= self.size:
            self.num_frame_used = 0
        # return number of batches according to current size.

        return train_tops, train_gt_labels, train_gt_boxes3d


    # size is for loading how many frames per time.
    def load_batch(self, size, shuffled):
        if shuffled:
            self.load_file_names = shuffle(self.load_file_names)

        # if all frames are used up, reload another batch according to cache_num
        if self.num_frame_used >= self.cache_num:
            batch_end_index = self.batch_start_index + self.cache_num

            if batch_end_index < self.size:
                loaded_file_names = self.load_file_names[self.batch_start_index:batch_end_index]
                self.batch_start_index = batch_end_index

            else:
                # print("end of the data is here: ", self.batch_start_index)
                diff_to_end = self.size - self.batch_start_index
                start_offset = self.cache_num - diff_to_end

                file_names_to_end = self.load_file_names[self.batch_start_index:self.size]
                if shuffled:
                    self.load_file_names = shuffle(self.load_file_names)

                file_names_from_start = self.load_file_names[0:start_offset]

                loaded_file_names = file_names_to_end + file_names_from_start
                self.batch_start_index = start_offset

            self.current_batch_file_names = loaded_file_names
            self.train_tops, self.train_gt_labels, self.train_gt_boxes3d = \
                load(loaded_file_names, is_testset=self.is_testset)
            self.num_frame_used = 0

        # if there are still frames left
        frame_end = min(self.num_frame_used + size, self.cache_num)
        train_tops = self.train_tops[self.num_frame_used:frame_end]
        if self.is_testset:
            train_gt_labels = None
            train_gt_boxes3d = None
        else:
            train_gt_labels = self.train_gt_labels[self.num_frame_used:frame_end]
            train_gt_boxes3d = self.train_gt_boxes3d[self.num_frame_used:frame_end]
        # print("start index is here: ", self.num_frame_used)
        handle_id = self.current_batch_file_names[self.num_frame_used:frame_end]
        handle_id = ['/'.join(name.split('/')[-3:]) for name in handle_id]
        # print('handle id here: ', handle_id)
        self.num_frame_used = frame_end
        # return number of batches according to current size.

        return train_tops, train_gt_labels, train_gt_boxes3d, handle_id

    def get_date_and_driver(self, handle_id):
        date_n_driver = ['/'.join(item.split('/')[0:2]) for item in handle_id]
        return date_n_driver

    def get_frame_info(self, handle_id):
        return handle_id

    def load(self, size, batch=True, shuffled=False):
        if batch:
            train_tops, train_gt_labels, train_gt_boxes3d, frame_id = self.load_batch(size,shuffled)
        else:
            train_tops, train_gt_labels, train_gt_boxes3d, frame_id = self.load_test_frames(size, shuffled)

        return np.array(train_tops), np.array(train_gt_labels), np.array(train_gt_boxes3d), frame_id






