import os
import shutil
# 根据 train_csv 中的文件筛选 train_node 和 train_edge 中的文件
def find_train_sample(csv_path):
    train_csv_count = 0
    train_edge2_count = 0
    train_node2_count = 0
    for root, dirs, files in os.walk(csv_path):
        for file in files:
            if file.endswith("csv"):
                train_csv_count += 1
                print("csv_file:", file)
                train_csv_name = file.split('.csv')[0]
                # print("csv_name:", train_csv_name)
                train_edge_file = train_csv_name + '.npy'
                print("edge_file", train_edge_file)

                # 移动符合条件的edge文件从 train_edge 到 train_edge2 文件夹
                edge_dir = "./all_data/comlog_edge"
                src_edge_path = os.path.join(edge_dir, train_edge_file)
                edge_dir2 = "./all_data/train_edge"
                dest_edge_path = os.path.join(edge_dir2, train_edge_file)
                shutil.copy2(src_edge_path, dest_edge_path)
                train_edge2_count += 1

                # 移动符合条件的node文件从 train_node 到 train_node2 文件夹中
                node_embedding_dir = "./all_data/comlog_node"
                src_node_path = os.path.join(node_embedding_dir, train_edge_file)
                node_embedding_dir2 = "./all_data/train_node"
                dest_node_path = os.path.join(node_embedding_dir2, train_edge_file)
                shutil.copy2(src_node_path, dest_node_path)
                train_node2_count += 1
                print()

    print("comlog_csv 文件夹中 csv 文件个数为:", train_csv_count, "个")
    print(f"移动到 train_edge 文件个数为: {train_edge2_count} 个")
    print(f"移动到 train_node 文件个数为: {train_node2_count} 个")

if __name__ == '__main__':
    csv_path = "./all_data/comlog_csv"
    find_train_sample(csv_path)
