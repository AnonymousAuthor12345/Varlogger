# 遍历方法 all_cfg 文件, 迭代删除日志语句节点, 每删除一个日志节点就构造一条图训练数据
import re
import numpy as np
import os
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('mchochlov/codebert-base-cd-ft')
# 构造删除一个日志节点(该节点中记录了局部变量)的方法的控制流图
def delete_log_node(cfg_path, bytecode_txt_path):
    cfg_count = 0
    cfg_log_count = 0
    bytecode_count = 0
    bytecode_log_count = 0
    match_log_count = 0
    match_method_count = 0
    not_match_method_count = 0
    not_match_method_name_list = []
    empty_node_method = 0
    save_edge_file_count = 0
    save_node_embedding_count = 0
    delete_csv_count = 0
    delete_label_count = 0

    # 遍历文件夹中的 all_cfg 方法, 其中每个 all_cfg 文件都包含日志对应train_csv中的方法.
    for root, dirs, files in os.walk(cfg_path):
        for file in files:
            if file.endswith(".txt"):
                print("==========================", file, "==========================")
                cfg_count += 1
                cfg_file_path = os.path.join(root, file)
                # 读取方法 all_cfg 文件, 获取里面的内容
                cfg_file = open(cfg_file_path, "r")
                cfg_content = cfg_file.read()
                # print("方法控制流图 cfg_content: ")
                # print(cfg_content)
                cfg_file.close()

                # 用于匹配cfg_content中日志语句的正则表达式
                cfg_pattern = re.compile(r"^\$r\d+ = (?:staticinvoke |r\d+\.|\$r\d+\.)?<[\w\.\$\_\']+: org\.apache\.commons\.logging\.Log (?:\w+|access\$\d+\(\))>[\(\)]{0,2};"
                                         r"(?:(?!^Block\s\d+:)[\w\W])*?"
                                         r"interfaceinvoke \$r\d+\.<org\.apache\.commons\.logging\.Log: void (?:trace|debug|info|warn|error|fatal)\([\w\W]+?\)>\([\w\W]+?\);\n"
                                         , re.MULTILINE)

                # 寻找方法 all_cfg 中的日志语句, 并把找到的日志语句以列表的形式返回
                cfg_log_list = cfg_pattern.findall(cfg_content)
                # 统计方法cfg中有多少条日志
                cfg_log_num = len(cfg_log_list)
                cfg_log_count += cfg_log_num
                print(f"方法cfg中有 {cfg_log_num} 条日志")
                # print("cfg_log_list:", cfg_log_list)
                # print()

                # 读取对应方法名的 bytecode 文件
                bytecode_file_path = os.path.join(bytecode_txt_path, file)
                bytecode_file = open(bytecode_file_path, "r")
                bytecode_content = bytecode_file.read()
                bytecode_file.close()
                bytecode_count += 1
                # print("bytecode_content:")
                # print(bytecode_content)

                # 用于匹配 bytecode_content 中日志的正则表达式
                bytecode_pattern = re.compile(r"(?:L\d+\n)?"
                                              r"(?:GETSTATIC|INVOKESTATIC|GETFIELD) [\w/$().]+?\.(?:\w+ : |access\$\d+\s+\(\))Lorg/apache/commons/logging/Log;"
                                              r"(?:(?!\nINVOKEINTERFACE org/apache/commons/logging/Log\.(?:isTraceEnabled|isDebugEnabled|isInfoEnabled|isWarnEnabled|isErrorEnabled|isFatalEnabled) \(\)Z \(itf\))[\w\W]+?)"
                                              r"(?:INVOKEINTERFACE|INVOKEVIRTUAL) org/apache/commons/logging/Log\.(?:trace|debug|info|warn|error|fatal) [\w\/;[\$\(\)]+ \(itf\)\n"
                                              r"(?:GOTO L\d+\n)?")


                # 找到 bytecode 中的日志,以列表的形式返回
                bytecode_log_list = bytecode_pattern.findall(bytecode_content)
                # print("bytecode_log_list:", bytecode_log_list)
                bytecode_log_num = len(bytecode_log_list)
                print(f"方法字节码中有 {bytecode_log_num} 条日志")
                bytecode_log_count += bytecode_log_num

                # 如果方法 all_cfg 跟 bytecode 中找到的日志数量相匹配
                if bytecode_log_num == cfg_log_num:
                    # print("=====================", file, "=====================")
                    # 统计cfg与bytecode日志数量匹配的方法个数
                    match_method_count += 1
                    # 统计 all_cfg 与 bytecode 中匹配的日志数量
                    match_log_count += bytecode_log_num
                    # print(f"方法cfg中有 {cfg_log_num} 条日志")

                    # 遍历 cfg_log_list 中每条日志语句, 迭代的从 cfg_content 中删除
                    for log_index, cfg_log in enumerate(cfg_log_list):
                        # print(f"---------- log{log_index}: ----------")
                        # print(cfg_log)
                        # 判断日志的内容是否多匹配了
                        if ("Block " in cfg_log) or ("[preds:" in cfg_log) or ("[succs:" in cfg_log):
                            print("正则写的有错误, 多匹配了内容")
                            print(cfg_log)

                        # 从 cfg_content 中删除该条日志,构建不含该日志的 new_cfg_content
                        new_cfg_content = cfg_content.replace(cfg_log, "", 1)
                        # print(f"删除 log{log_index} 后 new_cfg_content:")
                        # print(new_cfg_content)

                        # 按两个换行符切分 new_cfg_content 为一个个Block代码块
                        blocks = new_cfg_content.split('\n\n')
                        # print("blocks:", blocks)

                        empty_block_num = -1  # 记录删除日志后空的节点的编号
                        block_num_list = []  # 记录方法cfg中节点的编号
                        edge_index = []  # 邻接矩阵
                        method_node_content = []  # 保存每个节点的内容,用于节点嵌入

                        # 遍历 blocks 中的每个 block
                        for i, block in enumerate(blocks):
                            # 排除分割后的空字符串
                            if block:
                                # print()
                                # print(f"123 Block {i}:")
                                # print(block)
                                # 对每个block代码块按换行符进行切割
                                block_lines = block.splitlines()
                                # print("321 block_lines:", block_lines)
                                # 提取block_lines中的 block 序号
                                block_index = block_lines[0]
                                # print("111 block_index:", block_index)
                                if 'Block ' not in block_index:
                                    print("block 分割错误")
                                # 提取 block 的节点序号
                                block_index = block_index.split(" ")[1]
                                # print("222 block_index:", block_index)
                                block_index = block_index.split(':')[0]
                                # print("333 block_index:", block_index)
                                block_num = int(block_index)
                                # print("444 block_num:", block_num)
                                block_num_list.append(block_num)

                                # 提取 block 中节点的边信息
                                edge_info = block_lines[1]
                                if "[preds:" not in edge_info or "[succs:" not in edge_info:
                                    print("edge 分割错误")
                                # print("555 edge_info:", edge_info)
                                succs = edge_info.split(']')[1]
                                # print("666 succs:", succs)
                                succs = succs.split('succs:')[1]
                                # print("777 succs:", succs)
                                succs = succs.split(' ')
                                # print("888 succs:", succs)
                                # 遍历 succs 提取每个后继结点
                                for succs_num in succs:
                                    if succs_num:
                                        # [起点,终点]
                                        edge = [block_num, int(succs_num)]
                                        # print("999 block_edge:", edge)
                                        # 添加该节点的边的信息 [起点,终点]
                                        edge_index.append(edge)

                                # 获取该节点中的代码内容 (除了block序号和节点的前继后继节点信息)
                                # print("000 block_content:", block_lines)
                                block_content = block_lines[2:]
                                # print("000 block_content:", block_content)
                                # 如果该节点除了是空节点, 则 block_content 为空列表
                                block_num_content = [block_num, block_content]
                                # 如果节点内容不为空
                                if block_content:
                                    method_node_content.append(block_num_content)
                                # 如果 block_lines 列表中元素只有2个(节点编号和边信息), 表示该节点是空节点
                                elif len(block_lines) == 2:
                                    empty_block_num = block_num
                                    # print(f"注意! 节点 {empty_block_num} 是空节点")
                                # print()
                        # print("方法节点列表 block_num_list:", block_num_list)
                        # print("方法中最大 block 编号:", max(block_num_list))
                        # 如果 empty_block_num 不是-1, 表示该方法中存在空节点
                        if empty_block_num != -1:
                            empty_node_method += 1
                            # print("方法空节点编号:", empty_block_num)
                        if block_num_list != sorted(block_num_list):
                            print("原有的block没有按照循序排序")

                        # 方法节点的内容按照节点的编号进行排序
                        method_node_content = sorted(method_node_content, key=lambda x: x[0])
                        # 对 method_node_content 中的每个节点的内容做节点嵌入
                        method_node_embedding_list = []
                        # print("000 method_node_content:")
                        for node_content in method_node_content:
                            # print(node_content)
                            # print(f"node {node_content[0]}:")
                            # print(f"node_content:", node_content[1])
                            sentence_embedding = model.encode(node_content[1], convert_to_numpy=True)  # nx768
                            # print("sentence_embedding.shape:", sentence_embedding.shape)

                            # 按列求所有句嵌入特征的平均句嵌入作为该节点的嵌入(按列求均值)
                            node_embedding = np.mean(sentence_embedding, axis=0)  # 1x768
                            # print("node_embedding.shape:", node_embedding.shape)
                            method_node_embedding_list.append(node_embedding)


                        # 使用 np.vstack 将向量列表堆叠成 (n,768) 矩阵,n表示节点的个数
                        method_node_embedding_arr = np.vstack(method_node_embedding_list)
                        # print("method_node_embedding_arr.shape:", method_node_embedding_arr.shape)

                        # 保存 method_node_embedding 文件
                        node_emedding_path = "./all_data/comlog_node"
                        method_name = file.split(".txt")[0]
                        node_embedding_name = f"{method_name}_Log{log_index}.npy"

                        node_emedding_path = os.path.join(node_emedding_path, node_embedding_name)
                        np.save(node_emedding_path, method_node_embedding_arr)
                        save_node_embedding_count += 1

                        # 构建每个节点之间的邻接矩阵
                        if empty_block_num != -1:
                            # print("方法中的空节点index:", empty_block_num)
                            # print("edge_index:", edge_index)
                            # 取方法中节点的最大值, 构建 (n+1)*(n+1) 的全为0邻接矩阵
                            max_blcok_num = max(block_num_list)
                            Adjacency_matrix = np.zeros((max_blcok_num + 1, max_blcok_num + 1))
                            # print("Adjacency_matrix.shape:", Adjacency_matrix.shape)
                            # 遍历 edge_index 中每个元素 [起点,终点]
                            # 给Adjacency_matrix邻接矩阵对应位置的元素赋值
                            for edge in edge_index:
                                # print("123edge:", edge)
                                Adjacency_matrix[edge[0], edge[1]] = 1
                            # print("Adjacency_matrix:")
                            # print(Adjacency_matrix)

                            # 删除 Adjacency_matrix 空节点的行和列
                            Adjacency_matrix = np.delete(Adjacency_matrix, empty_block_num, axis=0)
                            Adjacency_matrix = np.delete(Adjacency_matrix, empty_block_num, axis=1)
                            # print("new_Adjacency_matrix:")
                            # print(Adjacency_matrix)

                            # 返回 Adjacency_matrix 中 >0 的元素的索引
                            new_edge_index = np.argwhere(Adjacency_matrix > 0)
                            # print(f"删除节点 {empty_block_num} new_edge_index:")
                            # print(new_edge_index)

                            # 把 new_edge_index 转换为 NumPy 数组
                            edge_array = np.array(new_edge_index).T
                            # print("1222 new_edge_array.shape:", edge_array.shape)
                            method_name = file.split(".txt")[0]
                            # print("1222file_name  :", file)
                            # print("1222method_name:", method_name)
                            edge_npy_name = f"{method_name}_Log{log_index}.npy"
                            # print("1222edge_npy_name:", edge_npy_name)

                            # 保存edge_npy文件
                            train_edge_path = "./all_data/comlog_edge"
                            edge_path = os.path.join(train_edge_path, edge_npy_name)
                            np.save(edge_path, edge_array)
                            save_edge_file_count += 1

                        # 如果 empty_block_num1=-1, 说明该方法的 all_cfg 中没有空节点
                        elif empty_block_num == -1:
                            # print("该方法没有空节点 new_edge_index:")
                            # print(edge_index)
                            # 把 edge_index 转换为NumPy数组
                            edge_array = np.array(edge_index).T
                            # print("1222edge_array.shape:", edge_array.shape)
                            method_name = file.split(".txt")[0]
                            # print("1222 file_name  :", file)
                            # print("1222 method_name:", method_name)
                            edge_npy_name = f"{method_name}_Log{log_index}.npy"
                            # print("1222 edge_npy_name:", edge_npy_name)

                            # 保存edge_npy文件
                            train_edge_path = "./all_data/comlog_edge"
                            edge_path = os.path.join(train_edge_path, edge_npy_name)
                            np.save(edge_path, edge_array)
                            save_edge_file_count += 1

                elif bytecode_log_num != cfg_log_num:
                    not_match_method_count += 1
                    print(f">>> 方法 {file} bytecode 与 cfg 中日志数量不匹配")
                    # print("     cfg_log_num:", len(cfg_log_list))
                    # print("     bytecode_log_num:", len(bytecode_log_list))
                    not_match_method_name_list.append(file)

                    # 删除 train_csv 中方法 all_cfg 与 bytecode 日志数量不匹配的训练数据
                    method_name = file.split('.txt')[0]
                    # print("需要删除文件的 method_name:", method_name)
                    train_csv_dir = "./all_data/comlog_csv"
                    for root1, dirs1, csv_files in os.walk(train_csv_dir):
                        for csv_file in csv_files:
                            # 如果 train_csv 中存在该方法的数据
                            if method_name in csv_file:
                                # print("需要删除的 train_csv_file:", csv_file)
                                csv_file_path = os.path.join(train_csv_dir, csv_file)
                                # 删除文件
                                os.remove(csv_file_path)
                                print(f"{csv_file_path} 已删除")
                                delete_csv_count += 1

                    train_lable_dir = "./all_data/comlog_label"
                    # 删除 train_label 中 方法 all_cfg 与 bytecode 日志数量不匹配的训练数据
                    for root2, dirs2, label_files in os.walk(train_lable_dir):
                        for label_file in label_files:
                            if method_name in label_file:
                                # print("需要删除的 train_label_file:", label_file)
                                label_file_path = os.path.join(train_lable_dir, label_file)
                                # 删除文件
                                os.remove(label_file_path)
                                print(f"{label_file_path} 已删除")
                                delete_label_count += 1

    print("=========================== 总结 ===========================")
    print(f"读取了 {cfg_count} 个方法控制流图 cfg 文件, 一共有 {cfg_log_count} 条日志语句")
    print(f"读取了 {bytecode_count} 个方法字节码文件, 一共有 {bytecode_log_count} 条日志语句")
    print(f"一共有 {match_method_count} 个方法的 cfg 与 bytecode 中日志数量相同, 相同的日志条数为: {match_log_count} 条")
    print(f"日志数量不匹配的方法为 {len(not_match_method_name_list)} 个")
    print(f"删除了 {delete_csv_count} 个csv文件, 删除了 {delete_label_count} 个label文件")


if __name__ == '__main__':
    cfg_path = "./all_data/comlog_cfg"
    bytecode_txt_path = "./hive/class-txt2"
    delete_log_node(cfg_path, bytecode_txt_path)
