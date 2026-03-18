import os
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
model = SentenceTransformer('mchochlov/codebert-base-cd-ft')

# 最大句子行数填充长度 和 最大局部变量表填充长度
seq_max_len = 300
local_table_max_len = 10

def dataset_merge(train_csv_dir):
    train_csv_count = 0
    train_localtable_count = 0
    train_node_count = 0
    train_edge_count = 0
    data_list = []
    for root, dirs, files in os.walk(train_csv_dir):
        for file in files:
            if file.endswith('.csv'):
                print("======================", file, "======================")
                print("csv_file:", file)
                train_csv_count += 1
                # 根据csv的路径读取csv中方法体代码数据
                csv_path = os.path.join(root, file)
                csv_data = pd.read_csv(csv_path)
                bytecode_data_list = csv_data["methodContent"].tolist()
                # print("bytecode_data_list:", bytecode_data_list)
                # 统计方法 bytecode 代码长度
                bytecode_data_len = len(bytecode_data_list)
                print("bytecode_data_len:", bytecode_data_len)

                # 对代码进行句嵌入
                bytecode_data_tensor = torch.from_numpy(model.encode(bytecode_data_list))
                print("bytecode_data_tensor.shape:", bytecode_data_tensor.shape)

                # 计算需要填充的行数
                num_rows_to_add = seq_max_len - bytecode_data_tensor.shape[0]

                # 创建一个列数相同但行数为 num_rows_to_add 的零张量
                padding_tensor = torch.zeros(num_rows_to_add, bytecode_data_tensor.shape[1])

                # 将原始张量和填充张量在第一个维度（行）上拼接
                bytecode_data_tensor = torch.cat((bytecode_data_tensor, padding_tensor), dim=0)
                print("padded_tensor.shape:", bytecode_data_tensor.shape)
                print(bytecode_data_tensor)

                # 读取 csv 文件对应的 label 数据
                localtable_dir = "./all_data/train_label"
                localtable_path = os.path.join(localtable_dir, file)
                localtable_data = pd.read_csv(localtable_path)
                print("localtable_data:")
                print(localtable_data)
                train_localtable_count += 1

                # 读取 localtable 中的变量名, 根据局部变量表中的变量个数, 生成 label_mask 列表
                var_name_list = localtable_data["var_name"].tolist()
                print("var_name_list:", var_name_list)
                var_count = len(var_name_list)
                print(f"局部变量表中有 {var_count} 个变量")
                label_mask = [0] * local_table_max_len  # 构造一个20个0的列表
                print("初始化label_mask:", label_mask)
                one_list = [1] * var_count  # 对应位置的变量index设置为1
                # 把 label_mask 中有局部变量的位置设置为1
                label_mask[0:var_count] = one_list
                print("赋值后label_mask:", label_mask)

                # 读取 localtable 中变量的 label
                label_data_list = localtable_data["label"].tolist()
                # 获取填充前 label 长度
                label_data_len = len(label_data_list)
                print("填充前 label_data_len:", label_data_len)

                # 填充 label_data_list
                label_pad_num = local_table_max_len - label_data_len
                pad_label_data_list = label_data_list + [0] * label_pad_num
                print("填充后 label_data_len:", len(pad_label_data_list))
                print("label_data_list    :", label_data_list)
                print("pad_label_data_list:", pad_label_data_list)

                label_mask_tensor = torch.tensor(label_mask, dtype=torch.float32)
                label_tensor = torch.tensor(pad_label_data_list, dtype=torch.float32)
                print("label_mask_tensor:", label_mask_tensor)
                print("label_tensor     :", label_tensor)

                # 读取方法节点嵌入向量
                train_node_dir = "./all_data/train_node"
                node_name = file.split('.csv')[0]
                node_name = node_name + '.npy'
                # print("csv_name :", file)
                # print("node_name:", node_name)
                node_path = os.path.join(train_node_dir, node_name)
                node_data = np.load(node_path)
                node_tensor = torch.from_numpy(node_data)
                # print("node_tensor.shape:", node_tensor.shape)
                train_node_count += 1

                # 读取方法节点邻接矩阵
                train_edge_dir = "./all_data/train_edge"
                edge_name1 = file.split('.csv')[0]
                edge_name = edge_name1 + '.npy'
                # print("edge_name:", file)
                # print("edge_name:", edge_name)
                edge_path = os.path.join(train_edge_dir, edge_name)
                edge_data = np.load(edge_path)
                edge_tensor = torch.from_numpy(edge_data)
                edge_tensor = edge_tensor.to(torch.long)
                # print("edge_tensor.shape:", edge_tensor.shape)
                train_edge_count += 1

                # 构建数据样本
                data = {'bytecode_tensor': bytecode_data_tensor,
                        'label_mask_tensor': label_mask_tensor,
                        'label_tensor': label_tensor,
                        'node_tensor': node_tensor,
                        'edge_tensor': edge_tensor,
                        "train_name": file}
                data_list.append(data)
                
    pkl_name = "total_data.pkl"
    pkl_dir = "./all_data/pkl"
    pkl_path = os.path.join(pkl_dir, pkl_name)
    with open(pkl_path, 'wb') as pkl_file:
        pickle.dump(data_list, pkl_file)

    print(f"读取了{train_csv_count}个csv文件")
    print(f"读取了{train_localtable_count}个label文件")
    print(f"读取了{train_node_count}个node文件")
    print(f"读取了{train_edge_count}个edge文件")


if __name__ == '__main__':
    train_csv_dir = "./all_data/train_csv"
    dataset_merge(train_csv_dir)
