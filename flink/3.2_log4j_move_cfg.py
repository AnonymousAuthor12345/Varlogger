import os
import shutil

#  根据 train_csv 中方法名, 把该方法的cfg文件从cfg文件夹移动到当前项目中cfg文件夹中
def find_classfile(csv_path, cfg_path, save_path):
    csv_file_count = 0
    has_log_cfg_count = 0
    method_log_var_count_set = set()  # 用于记录cfg中日志监控局部变量的方法名字
    # 遍历 train_csv 文件夹, 统计方法名
    for root, dirs, files in os.walk(csv_path):
        for file in files:
            if file.endswith('.csv'):
                csv_file_count += 1
                print("csv_name: ", file)
                # 分割csv文件名,获取cfg方法名
                cfg_name = file.split("_Log")[0]+'.txt'
                print("cfg_name: ", cfg_name)
                print()
                method_log_var_count_set.add(cfg_name)
                # 根据train_csv中的方法名,把它的 all_cfg 图复制到 cfg_log_var 文件夹中
                source_path = os.path.join(cfg_path, cfg_name)
                dest_path = os.path.join(save_path, cfg_name)
                shutil.copy2(source_path, dest_path)
    print(f"读取了 {csv_file_count} 条日志 csv 训练数据")
    print(f"共计 {len(method_log_var_count_set)} 个方法的 cfg 文件中有日志语句记录了局部变量")

if __name__ == '__main__':
    cfg_path  = "/flink/class-cfg"
    csv_path  = "./all_data/log4j_csv"
    save_path = "./all_data/log4j_cfg"
    find_classfile(csv_path, cfg_path, save_path)
