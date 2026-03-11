import os
import shutil
def find_train_sample(csv_path):
    slf4j_csv_count = 0
    train_csv_count = 0
    slf4j_label_count = 0
    train_label_count = 0
    for root, dirs, files in os.walk(csv_path):
        for csv_file in files:
            if csv_file.endswith(".csv"):
                slf4j_csv_count += 1
                print("csv_file:", csv_file)

                # 移动符合条件的 csv 文件从 slf4j_csv 到 train_csv 文件夹
                slf4j_csv_dir = "./all_data/slf4j_csv"
                src_path = os.path.join(slf4j_csv_dir, csv_file)

                train_csv_dir = "./all_data/train_csv"
                dest_path = os.path.join(train_csv_dir, csv_file)
                shutil.copy2(src_path, dest_path)
                train_csv_count += 1

                # 移动符合条件的 all_label 文件从 slf4j_label 到 train_label 文件夹
                slf4j_label_dir = "./all_data/slf4j_label"
                src_path2 = os.path.join(slf4j_label_dir, csv_file)

                train_label_dir = "./all_data/train_label"
                dest_path2 = os.path.join(train_label_dir, csv_file)
                shutil.copy2(src_path2, dest_path2)
                train_label_count += 1

    print("slf4j_csv 文件夹中 csv 文件个数为:", slf4j_csv_count, "个")
    print(f"移动到 train_csv 文件个数为: {train_csv_count} 个")
    print(f"移动到 train_label 文件个数为: {train_label_count} 个")

if __name__ == '__main__':
    slf4j_csv_path = "./all_data/slf4j_csv"
    find_train_sample(slf4j_csv_path)
