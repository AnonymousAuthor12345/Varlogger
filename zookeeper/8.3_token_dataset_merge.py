import os
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
import torch
import numpy as np

# 最大句子填充长度
seq_max_len = 300
# 最大局部变量表填充长度
local_table_max_len = 10
model = SentenceTransformer('mchochlov/codebert-base-cd-ft')

def token_dataset_merge(pkl_path,token_pkl_name,token_split_dir):
    train_csv_count = 0
    data_list = []

    # 获取pkl文件中的 csv 文件名
    data_name_list = []
    with open(pkl_path, mode="rb") as pkl_file:
        total_pkl_data_list = pickle.load(pkl_file)
        print(type(total_pkl_data_list))
        print(total_pkl_data_list[0])
        for one in total_pkl_data_list:
            # print(one["train_name"])
            data_name_list.append(one["train_name"])
            train_csv_count += 1
    # print(data_name_list)

    for csv_name in data_name_list:
        # print(csv_name)

        # 读取对比方法 token_embedding 文件
        token_embedding_dir = "./all_data/token_embedding"
        token_embedding_name = csv_name.split('.csv')[0] + '.pt'
        token_embedding_path = os.path.join(token_embedding_dir, token_embedding_name)

        # 从文件加载 tensor
        token_embedding_matrix = torch.load(token_embedding_path)
        # print("token_embedding_matrix.shape:", token_embedding_matrix.shape)

        # 读取对比方法的 all_label
        token_label_dir = "./all_data/token_label"
        token_label_name = csv_name.split('.csv')[0] + '.csv'
        token_label_path = os.path.join(token_label_dir, token_label_name)
        token_label_data = pd.read_csv(token_label_path)

        token_label_tensor = torch.tensor(token_label_data["token_label"].tolist(), dtype=torch.float32)
        token_label_mask_tensor = torch.tensor(token_label_data["token_label_mask"].tolist(), dtype=torch.float32)
        var_location = torch.tensor(token_label_data["var_location"].tolist())

        # 构建样本数据
        data = {
            "token_embedding_tensor": token_embedding_matrix,
            "token_label_tensor": token_label_tensor,
            "token_label_mask_tensor": token_label_mask_tensor,
            "var_location": var_location,
            "train_name": csv_name}
        data_list.append(data)

    pkl_dir = token_split_dir
    pkl_path = os.path.join(pkl_dir, token_pkl_name)
    with open(pkl_path, 'wb') as pkl_file:
        pickle.dump(data_list, pkl_file)

    print(f"读取了{train_csv_count}个csv文件")

if __name__ == '__main__':
    token_split_dir = "./all_data/token_split_data"
    pkl_dir = "./all_data/split_data/train_pkl.pkl"
    token_pkl_name = "token_train_pkl.pkl"
    token_dataset_merge(pkl_dir, token_pkl_name, token_split_dir)

    token_split_dir = "./all_data/token_split_data"
    pkl_dir = "./all_data/split_data/val_pkl.pkl"
    token_pkl_name = "token_val_pkl.pkl"
    token_dataset_merge(pkl_dir, token_pkl_name, token_split_dir)

    token_split_dir = "./all_data/token_split_data"
    pkl_dir = "./all_data/split_data/test_pkl.pkl"
    token_pkl_name = "token_test_pkl.pkl"
    token_dataset_merge(pkl_dir, token_pkl_name, token_split_dir)
