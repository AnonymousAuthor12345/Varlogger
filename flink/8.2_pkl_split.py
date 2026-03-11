import os.path
import pickle
import random

# 将train_data.pkl数据划分成训练集pkl,验证集pkl,测试集pkl
def split_data(pkl_path):
    with open(pkl_path, mode="rb") as pkl_file:
        total_pkl_data = pickle.load(pkl_file)
        print("total_pkl_data 数据集长度为:", len(total_pkl_data))
        print("total_pkl_data[0]:")
        print(total_pkl_data[0])
        print('====================', "数据进行 shuffle ", '====================')
        random.shuffle(total_pkl_data)
        random.shuffle(total_pkl_data)
        print("total_pkl_data[0]:")
        print(total_pkl_data[0])

        # 计算数据集划分点
        train_size = int(len(total_pkl_data) * 0.8)
        print("train_size:", train_size)
        validate_size = int(len(total_pkl_data) * 0.1)
        print("validate_size:", validate_size)
        test_size = len(total_pkl_data) - train_size - validate_size
        print("test_size:", test_size)

        # 划分数据集
        train_data = total_pkl_data[0: train_size]
        val_data = total_pkl_data[train_size: train_size + validate_size]
        test_data = total_pkl_data[train_size + validate_size:]

        print("train_data 长度为 :", len(train_data))
        print("validate_data 长度为 :", len(val_data))
        print("test_data 长度为 :", len(test_data))

        # 保存训练集, 验证集, 测试集的文件夹
        split_data_dir = "./all_data/split_data"

        # 训练集保存
        train_data_path = os.path.join(split_data_dir, "train_pkl.pkl")
        with open(train_data_path, 'wb') as file1:
            # 使用pickle的dump函数来保存数据到文件
            pickle.dump(train_data, file1)

        # 验证集保存
        val_pkl_path = os.path.join(split_data_dir, "val_pkl.pkl")
        with open(val_pkl_path, 'wb') as file2:
            # 使用pickle的dump函数来保存数据到文件
            pickle.dump(val_data, file2)

        # 测试集保存
        test_pkl_path = os.path.join(split_data_dir, "test_pkl.pkl")
        with open(test_pkl_path, 'wb') as file3:
            # 使用pickle的dump函数来保存数据到文件
            pickle.dump(test_data, file3)

        # 保存图神经网络需要的数据
        graph_train_dir = "./all_data/graph_train/raw"
        graph_val_dir  = "./all_data/graph_val/raw"
        graph_test_dir = "./all_data/graph_train/raw"

        # 图训练集保存
        graph_train_data_path = os.path.join(graph_train_dir, "graph_data.pkl")
        with open(graph_train_data_path, 'wb') as file1:
            # 使用pickle的dump函数来保存数据到文件
            pickle.dump(train_data, file1)

        # 图验证集保存
        graph_val_data_path = os.path.join(graph_val_dir, "graph_data.pkl")
        with open(graph_val_data_path, 'wb') as file2:
            # 使用pickle的dump函数来保存数据到文件
            pickle.dump(val_data, file2)

        # 图测试集保存
        graph_test_data_path = os.path.join(graph_test_dir, "graph_data.pkl")
        with open(graph_test_data_path, 'wb') as file3:
            # 使用pickle的dump函数来保存数据到文件
            pickle.dump(test_data, file3)

if __name__ == '__main__':
    # 分割数据
    pkl_path = "./all_data/pkl/total_data.pkl"
    split_data(pkl_path)


