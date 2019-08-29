# TCT data preprocess, including:
# 1. obtain csv label file
# 2. find trusted region from csv file, crop single malignant cell
# 3. record one doctor or two doctors labeled data

'''
提供tct图像的目录，标注的CSV文件的路径以及生成文件的存储目录

可以对每个标注结果增加一个trusted属性，取值为-1时代表这张图片仅有一个医生进行了标注，取值为0代表两个医生标注不一致的区域，取值为1时代表两个医生标注了形同的细胞区域。对这三种分别进行crop，切割出的恶性细胞分开存储。而对于只有一个医生标注和两个医生标注不一致的图片，用txt文件分别存储下图片的序列号，以备将来在进行标注和检查。

生成了新的CSV文件（detail_infomation.csv）

E.g.:

文件加以及路径为：
save_dir = '/data/AlgProj/tct_yaoms/data/tct_0627_preprocess/'
data_dir = '/data/AlgProj/niezl/TCT/1_DataBase/20190627/'
csv_path = '/data/AlgProj/niezl/TCT/TCT_Data/Misc/TCT_0626_part1/影像标注结果.csv'

依次进行函数调用（注意顺序）
tct_0627 = TCTFilePreprocess(data_dir, csv_path, save_dir)

# remove_untrusted_label需要提供iou的阈值，已衡量两个医生标注的是否为同一区域
tct_0627.remove_untrusted_label(0.5)

#生成新的CSV文件
tct_0627.produce_new_label()

#切割出恶性细胞
tct_0627.crop_malignant()

'''

import os
import pandas as pd
import json
from PIL import Image
import random

class TCTFilePreprocess():
    def __init__(self, data_dir, csv_path, save_dir):
        self.data_dir = data_dir
        self.labels = pd.read_csv(csv_path)
        self.save_dir = save_dir
        self.series_id = self.labels['序列编号'].unique()
        
        self.labels['trusted'] = 0
        self.float2int()
    
    def IOU(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou
    
    def float2int(self):
        self.labels['x_min'] = 0
        self.labels['y_min'] = 0
        self.labels['x_max'] = 0
        self.labels['y_max'] = 0
        for idx in range(len(self.labels)):
            cur_dict = json.loads(self.labels.iloc[idx,:]['影像结果'])
            self.labels.loc[idx,'x_min'] = int(cur_dict['point1']['x'])
            self.labels.loc[idx,'y_min'] = int(cur_dict['point1']['y'])
            self.labels.loc[idx,'x_max'] = int(cur_dict['point2']['x'])
            self.labels.loc[idx,'y_max'] = int(cur_dict['point2']['y'])

    def remove_untrusted_label(self,iou_threshold):
        one_doctor_labeled = []
        for s_id in self.series_id:
            csv_s_id = self.labels.loc[self.labels['序列编号']==s_id]
            doctors = csv_s_id['用户姓名'].unique()
            if len(doctors) < 2:
                temp = csv_s_id['序列编号'].unique()[0]
                one_doctor_labeled.append(temp)
                self.labels.loc[self.labels['序列编号']==temp, 'trusted'] = -1
                continue
            doctor1_csv = csv_s_id.loc[csv_s_id['用户姓名']==doctors[0]]
            doctor2_csv = csv_s_id.loc[csv_s_id['用户姓名']==doctors[1]]

            for i in list(doctor1_csv.index):
                for j in list(doctor2_csv.index):
                    x11 = doctor1_csv.loc[i,'x_min']
                    y11 = doctor1_csv.loc[i,'y_min']
                    x12 = doctor1_csv.loc[i,'x_max']
                    y12 = doctor1_csv.loc[i,'y_max']
                    region1 = [x11, y11, x12, y12]
                    x21 = doctor2_csv.loc[j,'x_min']
                    y21 = doctor2_csv.loc[j,'y_min']
                    x22 = doctor2_csv.loc[j,'x_max']
                    y22 = doctor2_csv.loc[j,'y_max']
                    region2 = [x21, y21, x22, y22]
                    iou = self.IOU(region1, region2)
                    
                    num_i = doctor1_csv.loc[i,'影像结果编号']
                    num_j = doctor2_csv.loc[j,'影像结果编号']
                    if iou >= iou_threshold:
                        self.labels.loc[self.labels['影像结果编号']==num_i,'trusted'] = 1
                        self.labels.loc[self.labels['影像结果编号']==num_j,'trusted'] = 1
        
        #记录下trusted=0的序列号
        file_path = self.save_dir + 'untrusted_series_id.txt'
        if not self.check_exist(file_path):
            with open(file_path, 'a') as f:
                untrusted_series = self.labels.loc[self.labels['trusted']==0, '序列编号'].unique()
                for i in untrusted_series: 
                    f.write(i)
                    f.write('\n')
        else:
            print("'untrusted_series_id.txt'文件已存在")
        #记录一个医生标注的序列编号
        file_path = self.save_dir + 'one_doctor_labeled.txt'
        if not self.check_exist(file_path):
            with open(file_path, 'a') as f:
                for i in one_doctor_labeled:
                    type(i)
                    f.write(i)
                    f.write('\n')
        else:
            print('one_doctor_labeled.txt已存在')
        

    def produce_new_label(self):
        columns = ['序列编号','x_min','y_min','x_max','y_max','恶性细胞分类','TCT病灶类型','核膜形状','核仁','染色质','细胞核大小','细胞形态','trusted']
        path = self.save_dir + 'detail_infomation.csv'
        if not self.check_exist(path):
            self.labels.to_csv(path,columns=columns, index=False)
        else:
            print('detail_infomation.csv文件已存在')
        
    
    def crop_malignant(self):
        '''
        trusted: -1, 0, 1 stands for one doctor labeled, different cell two doctor labeled, the same cell two doctor labeled
        '''
        trusted_nums = self.labels['trusted'].unique()
        for trusted in trusted_nums:
            dataframe = self.labels.loc[self.labels['trusted'] == trusted]
            print('len of dataframe',len(dataframe))
            if trusted == -1:
                cur_dir = 'one_doctor_labeled/'
            elif trusted == 0:
                cur_dir = 'different_region_labeled/'
            elif trusted == 1:
                cur_dir = 'the_same_region_labeled/'
            
            save_dirs = self.save_dir + cur_dir
            if not self.check_exist(save_dirs):
                os.mkdir(save_dirs)

            unique_series = dataframe['序列编号'].unique()

            for series in unique_series:
                cur_df = dataframe.loc[dataframe['序列编号']==series]
                if trusted == 1:
                    doctors = cur_df['用户姓名'].unique()
                    doctor = random.choice(doctors)
                    cur_df = cur_df.loc[cur_df['用户姓名']==doctor]
                counter = 0
                for idx in cur_df.index:
                    series_name = cur_df.loc[idx, '序列编号']
                    temp_path = self.data_dir + series_name
                    file = os.listdir(temp_path)
                    read_path = temp_path + '/' + file[0]
                    crop_img_name = series + '_' + file[0] + '_'+ str(counter) + '.jpg'
                    save_path = save_dirs + crop_img_name
                    counter += 1
                    
                    if not self.check_exist(save_path):
                        img = Image.open(read_path)
                        shape = img.size

                        x_min = max(0, cur_df.loc[idx, 'x_min'])
                        y_min = max(0, cur_df.loc[idx, 'y_min'])
                        x_max = min(shape[0], cur_df.loc[idx, 'x_max'])
                        y_max = min(shape[1], cur_df.loc[idx, 'y_max'])
                        box = [x_min, y_min,x_max, y_max]

                        crop_img = img.crop(box)                        
                        crop_img.save(save_path, quality=95)
                    else:
                        continue
                        
    
    def check_exist(self, path):
        return os.path.exists(path)
###