# This file is aimed at comparing labels from different doctors to the same picture
# new comparasion pictures will generate

'''
E.g.:

#提供tct_data所在目录，CSV文件所在路径以及生成的比较奥图片的保存目录
data_dir = '/data/AlgProj/niezl/TCT/1_DataBase/20190702/'
csv_path = '/data/AlgProj/niezl/TCT/TCT_Data/Misc/TCT标注_0702/影像标注结果.csv'
save_dir = '/data/AlgProj/tct_yaoms/data/tct_0702_doctor_labels_comparasion/'

生成对象并调用comparasion函数即可：
tct_0702 = doctor_labels_comparasion(data_dir, csv_path, save_dir)
tct_0702.comparasion()
'''

class doctor_labels_comparasion():
    def __init__(self, data_dir, csv_path, save_dir):
        self.data_dir = data_dir
        self.labels = pd.read_csv(csv_path)
        self.save_dir = save_dir
        self.float2int()
        
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
    
    def comparasion(self):
        series = self.labels['序列编号'].unique()
        for s in series:
            dataframe = self.labels.loc[self.labels['序列编号']==s]
            doctors = dataframe['用户姓名'].unique()
            if len(doctors) == 2:
                df_doc1 = dataframe.loc[dataframe['用户姓名']==doctors[0]]
                df_doc2 = dataframe.loc[dataframe['用户姓名']==doctors[1]]
                
                #read img
                series = df_doc1['序列编号'].unique()
                img_dir = self.data_dir + series[0] + '/'
                img_name = os.listdir(img_dir)[0]
                img_path = img_dir + img_name
                img = cv2.imread(img_path)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                color = ((255, 0, 0),(0, 0, 255))
                location = ((50, 50), (50, 100))
                img = self.draw_box(img, df_doc1, color[0], location[0])
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = self.draw_box(img, df_doc2, color[1], location[1])
            elif len(doctors) < 2:
                df_doc1 = dataframe.loc[dataframe['用户姓名']==doctors[0]]
                series = df_doc1['序列编号'].unique()
                img_dir = self.data_dir + series[0] + '/'
                img_name = os.listdir(img_dir)[0]
                img_path = img_dir + img_name
                img = cv2.imread(img_path)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                color = (255, 0, 0)
                location = (50, 50)
                img = self.draw_box(img, df_doc1, color, location)
            
            #save img
            self.save_img(img, s, doctors)
            
    def draw_box(self, img, df, color, location):
        d_cate = {'1':'ASC-US', '2':'ASC-H', '3':'L-SIL', '4':'H-SIL', '5':'SCC', '6':'AGC-NOS', '7':'AGC-neoplastic', '8':'AIS', '9':'AC'}
        height, width = img.shape[:2]
        font_path = '/usr/share/fonts/truetype/simsun.ttf'
        
        for idx in df.index:
            x_min = max(0, df.loc[idx, 'x_min'])
            y_min = max(0, df.loc[idx, 'y_min'])
            x_max = min(width, df.loc[idx, 'x_max'])
            y_max = min(height, df.loc[idx, 'y_max'])
            img = cv2.rectangle(img, (x_min, y_min), (x_max, y_max), color, 5)
            label_num = df.loc[idx, '恶性细胞分类']
            label = d_cate[str(label_num)]
            locate_x = x_min
            if (y_min - 50 < 0):
                locate_y = y_max - 5
            else:
                locate_y = y_min - 5
            cv2.putText(img, label, (locate_x, locate_y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
            
        doctor = df['用户姓名'].unique()

        img = Image.fromarray(img)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font_path, 45, encoding='utf-8')
        draw.text(location, doctor[0], color, font)
        
        img = cv2.cvtColor(np.array(img),cv2.COLOR_RGB2BGR) 
        return img
    
            
    def save_img(self,img, series,doctors):
        img_save_dir = self.save_dir + series + '/'
        if not os.path.exists(img_save_dir):
            os.mkdir(img_save_dir)
        
        img_name_pre = ''
        if len(doctors) == 1:
            img_name_pre = doctors[0] + '-标注'
        else:
            doctors =list(doctors)
            img_name_pre = '-'.join(doctors) + '-共同标注'
        
        img_name = img_name_pre + '.jpg'
        img_save_path = img_save_dir + img_name
        if not os.path.exists(img_save_path):
            cv2.imwrite(img_save_path, img)
###
