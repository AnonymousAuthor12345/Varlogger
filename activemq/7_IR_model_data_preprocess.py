# 读取训练的csv数据 用glove做词嵌入
import os
import pandas as pd
import torch
import re
from torchtext.vocab import GloVe

# 加载GloVe模型
glove_model = GloVe(name='6B', dim=100)

def calculate_mrr(true_labels, predicted_lst):
    """ 计算 MRR """
    reciprocal_rank_list = []
    # 查询 true_labels 中每个变量在 predicted_lst 中的位置
    for var_name in true_labels:
        # 如果变量在预测的列表里
        if var_name in predicted_lst:
            # 查询 var_name 在 predicted_lst 列表中的第一个位置
            first_occurrence_index = predicted_lst.index(var_name)
            # 求该变量索引的倒数值
            var_result = 1 / (first_occurrence_index + 1)
            # print("var_result:", var_result)
            reciprocal_rank_list.append(var_result)
        # 如果变量不在预测的列表中
        elif var_name not in predicted_lst:
            var_result = 0
            reciprocal_rank_list.append(var_result)
    return max(reciprocal_rank_list)
def split_compound_word(word):
    # Split snake_case and camelCase
    tokens = re.split(r'[_]+', word)
    simple_tokens = []
    for token in tokens:
        simple_tokens.extend(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', token))
    return simple_tokens

# 获取单词的词向量
def get_word_embedding(word):
    # 按照snake_case and camelCase 分割单词
    tokens = split_compound_word(word)
    if len(tokens) > 1:  # 复合词:求各个子的词嵌入的平均值当做复合词的词嵌入
        vectors = glove_model.get_vecs_by_tokens(tokens, lower_case_backup=True)
        return vectors.mean(dim=0)
    else:  # 简单词
        return glove_model.get_vecs_by_tokens([word], lower_case_backup=True)[0]


# 分割文本为单词
def split_text(text):
    return re.split(r'(\W+)', text)  # 按照非字母数字下划线进行分割单词


# 处理文本
def process_text(text):
    # 对整段文本进行分词
    words = split_text(text)
    new_words = []
    for word in words:
        # 如果 token不是纯数字
        if not word.isdigit():
            new_words.append(word)

    # 遍历每个 token, 使用 glove 进行词嵌入
    text_embedding = []
    for word in new_words:
        word_embedding = get_word_embedding(word)
        text_embedding.append(word_embedding)
    stacked_tensor = torch.stack(text_embedding, dim=0)
    return stacked_tensor, new_words


def data_process(train_csv_dir):
    train_csv_count = 0
    max_word2 = 0  # 统计代码中token数量最大数
    max_token = 3317  # 基于 max_word2 用于限制代码中 token 数量
    select_count = 0

    for root, dirs, files in os.walk(train_csv_dir):
        for file in files:
            if file.endswith('.csv'):
                print("======================", file, "======================")
                print("csv_file:", file)
                train_csv_count += 1

                # 根据 csv 路径,读取 csv 中方法体代码数据
                csv_path = os.path.join(root, file)
                csv_data = pd.read_csv(csv_path)

                # 读取 csv_data 中方法体字节码指令语句
                bytecode_data_list = csv_data["methodContent"].tolist()
                # print("bytecode_data_list:", bytecode_data_list)
                # 把每行数据拼成一个长字符串
                bytecode_str = '\n'.join(bytecode_data_list)
                # print("bytecode_str:")
                # print(bytecode_str)

                # 把 bytecode_str 进行词嵌入, 返回嵌入后的矩阵和分词后的文本
                text_embedding, text_words = process_text(bytecode_str)
                print("text_embedding.shape:", text_embedding.shape)
                print("分词后的方法:")
                print(text_words)

                # 统计分词后方法中 token 个数
                bytecode_token_len = text_embedding.shape[0]
                if max_word2 < bytecode_token_len:
                    max_word2 = bytecode_token_len
                print("bytecode_token_len:", bytecode_token_len)

                # 创建一个 [max_token, 100] 的全零矩阵
                zero_matrix = torch.zeros((max_token, 100))

                # 将 text_embedding 矩阵的内容复制到全零矩阵中
                zero_matrix[0:text_embedding.shape[0], 0:text_embedding.shape[1]] = text_embedding
                print("填充后的 zero_matrix:")
                print(zero_matrix)
                print("zero_matrix.shape:", zero_matrix.shape)

                # 构建用于预测的每个 token 是否是重要变量的 all_label
                label_dir = "./all_data/train_label"
                label_file_name = file.split('.csv')[0] + ".csv"
                label_file_path = os.path.join(label_dir, label_file_name)
                label_csv_data = pd.read_csv(label_file_path)
                print("label_csv_data:")
                print(label_csv_data)

                # 获取局部变量表中的变量名 var_name 和它对应的 all_label
                var_name_list = label_csv_data["var_name"].tolist()
                label_list = label_csv_data["all_label"].tolist()
                print("var_name_list:", var_name_list)
                print("label_list   :", label_list)
                # 查找日志中记录的变量
                log_var_list = []  # 用于存储日志中记录的变量名
                for index1, one in enumerate(label_list):
                    if one == 1:
                        log_var_list.append(var_name_list[index1])
                print("log_var_list :", log_var_list)

                # 构建以 token 为单位的 all_label 列表
                token_label = [0] * max_token
                # 查询日志中记录的变量在分词后的 text_words 位置, 并把该位置标记为 1
                for log_var_name in log_var_list:
                    for token_index, token in enumerate(text_words):
                        if token == log_var_name:
                            token_label[token_index] = 1

                token_label_mask = [0] * max_token  # 记录 token_label 中实际的有效位置,排除填充位置,用于计算loss
                token_label_mask[0: bytecode_token_len] = [1] * bytecode_token_len
                # print("token_label_mask中 1 的数量为:", token_label_mask.count(1))
                # print("bytecode_token_len:", bytecode_token_len)

                # 识别分词后 text_words 中哪些 token 的位置是变量名, 用于计算模型预测的准确率
                var_location = [0] * max_token
                for var_name in var_name_list:
                    for token_index, token in enumerate(text_words):
                        if var_name == token:
                            var_location[token_index] = 1

                # 存储分词后的方法, 用于计算预测的准确率
                token_text_name = file.split('.csv')[0] + ".json"
                df0 = pd.DataFrame({'token': text_words})
                token_label_path = os.path.join("./all_data/token_text", token_text_name)
                # 将 DataFrame 保存为 JSON 文件
                df0.to_json(token_label_path, orient="records")

                # 存储嵌入后的基于token的文本
                tensor_name = file.split('.csv')[0]+".pt"
                print("tensor_name:", tensor_name)
                tensor_path = os.path.join("./all_data/token_embedding", tensor_name)
                # 保存 tensor 到文件
                torch.save(zero_matrix, tensor_path)

                # 保存基于token的 all_label 信息
                # 创建 DataFrame
                df1 = pd.DataFrame({
                    'token_label': token_label,
                    'token_label_mask': token_label_mask,
                    'var_location': var_location
                })

                token_label_name = file.split('.csv')[0]+".csv"
                token_label_path = os.path.join("./all_data/token_label", token_label_name)

                # 保存为 CSV
                df1.to_csv(token_label_path, index=False)

    print(f"总共遍历了 {train_csv_count} 个 bytecode_csv 数据")
    print(f"所有方法中最大的token数为:{max_word2}")  # 所有方法中最大的token数为:5664
    # print(f"所有的方法中小于512个 token 数的方法数量为:{select_count}")


if __name__ == '__main__':
    bytecode_csv_path = "./all_data/train_csv"
    data_process(bytecode_csv_path)
