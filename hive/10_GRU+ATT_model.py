import json
import os
import pickle
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torch.nn.functional as F

def calculate_precision_at_k(recommended_variables, k, true_logged_variables):
    relevant = [var for var in recommended_variables[:k] if var in true_logged_variables]
    precision = len(relevant) / k
    return precision


def calculate_average_precision(recommended_variables, true_logged_variables):
    precisions = [calculate_precision_at_k(recommended_variables, k + 1, true_logged_variables)
                  for k in range(len(recommended_variables)) if recommended_variables[k] in true_logged_variables]
    if not precisions:
        return 0.0
    average_precision = sum(precisions) / len(true_logged_variables)
    return average_precision


def calculate_map(recommendations, true_logged_variables_list):
    average_precisions = [calculate_average_precision(recs, true_vars)
                          for recs, true_vars in zip(recommendations, true_logged_variables_list)]
    map_score = sum(average_precisions) / len(average_precisions)
    return map_score

def top_k_acc(ground_truth_list, pred_list, k):
    # 取前k个预测结果
    pred_top_k_list = pred_list[0:k]
    # 遍历 pred_top_k_list 查询预测的变量是否在ground_truth_list中
    for pred_var1 in pred_top_k_list:
        if pred_var1 in ground_truth_list:
            return 1
    return 0

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


def find_top_three_indices(lst):
    # 创建列表,其中列表的元素是元组，每个元组包含预测值和对应的索引
    indexed_lst = [(index1, value) for index1, value in enumerate(lst)]
    # print("排序前:", indexed_lst)
    # 对indexed_lst 按每个元组的第1个子元素从大到小顺序排序
    indexed_lst.sort(reverse=True, key=lambda x: x[1])
    # print("排序后:", indexed_lst)
    return indexed_lst


class MaskedBCEWithLogitsLoss(nn.Module):
    def __init__(self, reduction='mean'):
        super(MaskedBCEWithLogitsLoss, self).__init__()
        self.reduction = reduction

    def forward(self, logits, targets, mask):
        # 应用 Sigmoid 激活函数
        logits = torch.sigmoid(logits)

        # 计算二进制交叉熵损失
        loss = - (targets * torch.log(logits + 1e-7) + (1 - targets) * torch.log(1 - logits + 1e-7))

        # 将损失张量与掩码相乘以过滤掉不想考虑的样本的损失
        loss = loss * mask

        if self.reduction == 'mean':
            # 计算平均损失
            loss = torch.sum(loss) / torch.sum(mask)
        elif self.reduction == 'sum':
            # 计算总损失
            loss = torch.sum(loss)
        return loss


class LstmDataset(torch.utils.data.Dataset):
    def __init__(self, pkl_path):
        # 加载pkl文件
        with open(pkl_path, 'rb') as file:
            pkl_data_list = pickle.load(file)
        self.pkl_data_list = pkl_data_list
        self.pkl_data_len = len(self.pkl_data_list)
        print("pkl_path:", pkl_path)
        # print("pkl_data_len:", self.pkl_data_len)

    def __len__(self):
        return self.pkl_data_len

    def __getitem__(self, idx):
        # 获取第 index 个样本
        train_data = self.pkl_data_list[idx]
        # print(train_data)
        return (train_data['token_embedding_tensor'], train_data['token_label_tensor'],
                train_data['token_label_mask_tensor'], train_data['var_location'],
                train_data['train_name'])


# 实例化数据集对象
train_dataset = LstmDataset("./all_data/split_data/train_pkl.pkl")
val_dataset = LstmDataset("./all_data/split_data/val_pkl.pkl")
test_dataset = LstmDataset("./all_data/split_data/test_pkl.pkl")

train_dataset_size = len(train_dataset)
val_dataset_size = len(val_dataset)
test_dataset_size = len(test_dataset)


# 加载数据集,构造dataloader
train_loader = DataLoader(train_dataset, batch_size=80, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=1, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False)


# 构建网络模型
class BiGRU_with_Att(nn.Module):
    def __init__(self):
        super().__init__()
        self.GRU = nn.GRU(input_size=100,
                          hidden_size=128,
                          num_layers=1,
                          batch_first=True,
                          bidirectional=True)
        self.multi_att = nn.MultiheadAttention(num_heads=4, embed_dim=256)

        self.linear1 = nn.Linear(2 * 128, 1)
        self.classifier = nn.Sigmoid()

    def forward(self, x):

        # GRU层
        output, h = self.GRU(x)

        # 多头注意力层
        output, attn_weights = self.multi_att(output, output, output)

        # sigmoid 层
        output = self.classifier(self.linear1(output))
        output = output.squeeze(-1)
        return output


# 模型实例化
model1 = BiGRU_with_Att()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model1.to(device)


# 定义损失和优化器
criterion = torch.nn.BCELoss(reduction="mean")
optimizer = torch.optim.Adam(model1.parameters(), lr=1e-3)

# 模型训练和测试
if __name__ == '__main__':
    epoch_list = []
    epoch_train_loss_sum_list = []
    epoch_val_acc_list = []  # 统计所有 epoch 下 val 集的平均acc
    best_accuracy = 0
    for epoch in range(200):
        # 模型训练
        model1.train()
        train_loss_sum = 0
        print(f"============ 第 {epoch} 轮训练开始 ============")
        # 记录当前的epoch
        epoch_list.append(epoch)
        for batch_index, data in enumerate(train_loader):
            # print("batch_index:", batch_index)
            # print("all_data:")
            # print(all_data)
            # print("len(all_data):", len(all_data))

            token_inputs, token_targets, token_targets_mask, var_locations, train_names = data
            token_inputs, token_targets, token_targets_mask = token_inputs.to(device), token_targets.to(device), token_targets_mask.to(device)


            optimizer.zero_grad()

            # forward
            outputs = model1(token_inputs)
            # print("token_outputs.shape:", outputs.shape)
            loss = criterion(outputs, token_targets)

            # backward
            loss.backward()

            # update
            optimizer.step()
            train_loss_sum += loss.item()
            # print("   batch_index:", batch_index, "loss:", loss.item())
        # print("train_loss_sum:", train_loss_sum)
        # 记录当前epoch下的 current_train_loss_sum
        epoch_train_loss_sum_list.append(train_loss_sum)

        # 模型验证(评估当前训练模型的性能)
        model1.eval()
        with torch.no_grad():
            val_acc_list = []  # 统计当前 epoch 中每个样本的准确率
            val_mrr_list = []
            val_top1_list = []
            val_top2_list = []
            val_loss_sum = 0
            for batch_index, data in enumerate(val_loader):
                val_inputs, val_target, val_target_mask, val_var_location, val_csv_name = data
                val_inputs, val_target, val_target_mask = val_inputs.to(device), val_target.to(device), val_target_mask.to(device)
                csv_name = val_csv_name[0]

                outputs = model1(val_inputs)  # [1, 5664]
                # print("val_outputs:", outputs)
                loss = criterion(outputs, val_target)
                val_loss_sum += loss.item()

                # 读取 token_text文件夹下的方法体,获取每个位置的token
                token_text_dir = "./all_data/token_text"
                token_json_name = csv_name.split(".csv")[0] + ".json"
                token_text_path = os.path.join(token_text_dir, token_json_name)
                with open(token_text_path, 'r') as json_file:
                    # 加载 JSON 数据
                    token_list = json.load(json_file)
                # print("token_list:", token_list)
                new_token_list = []
                for one in token_list:
                    # print(one["token"])
                    new_token_list.append(one["token"])
                # print("new_token_list:")
                # print(new_token_list)

                # 取 output 里的前 token_len 个有效的预测结果
                token_len = len(new_token_list)
                outputs_list1 = outputs.squeeze().tolist()[0:token_len]

                # 使用 zip 将token 跟每个token的预测结果进行匹配
                pred_list = list(zip(new_token_list, outputs_list1))

                # 根据 var_location 取 output 中有效的预测结果
                val_var_location = val_var_location.squeeze().tolist()
                # print("val_var_location:", val_var_location)

                sorted_pred_list = []
                # 根据 var_location为 1 的位置, 取出 pred_list 中对应位置的元素
                for token_index, token_label in enumerate(val_var_location):
                    if token_label == 1:
                        sorted_pred_list.append(pred_list[token_index])
                # print("未排序 sorted_pred_list:", sorted_pred_list)
                # 按照概率值大小对预测结果进行排序
                sorted_pred_list.sort(reverse=True, key=lambda x: x[1])
                # print("排序后 sorted_pred_list:", sorted_pred_list)

                # 读取 train_label 获取日志中记录的变量名
                label_dir = "./all_data/train_label"
                label_path = os.path.join(label_dir, csv_name)
                label_csv = pd.read_csv(label_path)
                # var_name_list 列表
                var_name_list = label_csv['var_name'].tolist()
                # print("var_name_list:", var_name_list)
                # all_label 列表
                label_list = label_csv['label'].tolist()
                # print("label_list:", label_list)
                # 根据 label_list 获得日志中记录的变量名
                ground_truth_list = []
                for index0, label in enumerate(label_list):
                    if label == 1:
                        ground_truth_list.append(var_name_list[index0])
                # print("ground_truth_list:", ground_truth_list)

                # 根据模型预测结果, 取出对应的预测的变量名
                pred_var_name_list = []
                # print("概率从大到小排序后的局部变量推荐表:")
                for ele in sorted_pred_list:
                    var_name = ele[0]  # 取出变量名
                    # 不添加同名变量
                    if var_name not in pred_var_name_list:
                        pred_var_name_list.append(var_name)
                # print("pred_var_name_list:", pred_var_name_list)

                # 从 pred_var_name_list 中取跟 ground_truth_list 变量个数一样的前几个预测变量
                limit_pred_var_name_list = pred_var_name_list[0:len(ground_truth_list)]
                # print("limit_pred_var_name_list:", limit_pred_var_name_list)
                # print("ground_truth_list :", ground_truth_list)

                # 计算模型预测的正确率
                correct_count = 0
                total_count = len(ground_truth_list)  # 日志中记录的变量个数
                for pred_var_name in limit_pred_var_name_list:  # 遍历 pred_var_name_list 中每个变量名
                    if pred_var_name in ground_truth_list:
                        correct_count += 1
                sample_acc = correct_count / total_count
                # 添加模型预测的准确率
                val_acc_list.append(sample_acc)

                # 计算当前样本的 mrr
                mrr_result = calculate_mrr(ground_truth_list, pred_var_name_list)
                val_mrr_list.append(mrr_result)

                # 计算当前样本的top1_acc
                top1_result = top_k_acc(ground_truth_list, pred_var_name_list, k=1)
                val_top1_list.append(top1_result)

                # 计算当前样本的top2_acc
                top2_result = top_k_acc(ground_truth_list, pred_var_name_list, k=2)
                val_top2_list.append(top2_result)

        # 当前epoch下的loss_sum
        print("val_loss_sum:", val_loss_sum)

        # 计算当前epoch下,模型在验证集下的平均预测准确率
        current_epoch_average_acc = sum(val_acc_list) / len(val_acc_list)
        print("val_acc:", current_epoch_average_acc)
        epoch_val_acc_list.append(current_epoch_average_acc)

        # 输出当前epoch下的 val_mrr
        val_mrr = sum(val_mrr_list) / len(val_mrr_list)
        print("val_mrr:", val_mrr)

        # 计算当前epoch下,模型的top1_acc
        val_top1_acc = sum(val_top1_list) / len(val_top1_list)
        print("val_top1_acc:", val_top1_acc)

        # 计算当前epoch下,模型的top2_acc
        val_top2_acc = sum(val_top2_list) / len(val_top2_list)
        print("val_top2_acc:", val_top2_acc)

        # Save the model if the accuracy is the best
        if current_epoch_average_acc > best_accuracy:
            # 模型保存
            model_dir = "./model_save"
            model_name = "GRU+ATT_model.pth"
            model_path = os.path.join(model_dir, model_name)
            torch.save(model1, model_path)
            best_accuracy = current_epoch_average_acc
            print("模型已经保存")

    print("=============模型开始测试=============")
    # 模型测试
    test_model = torch.load("./model_save/GRU+ATT_model.pth")
    test_model.eval()
    test_acc_list = []  # 统计每个样本的准确率
    test_mrr_list = []
    test_top1_list = []
    test_top2_list = []
    with torch.no_grad():
        for batch_index, data in enumerate(test_loader):
            test_inputs, test_target, test_target_mask, test_var_location, test_csv_name = data
            test_inputs, test_target, test_target_mask = test_inputs.to(device), test_target.to(device), test_target_mask.to(device)
            csv_name = test_csv_name[0]

            outputs = model1(test_inputs)  # [1, 5664]
            loss = criterion(outputs, test_target)

            # 读取 token_text文件夹下的方法体,获取每个位置的token
            token_text_dir = "./all_data/token_text"
            token_json_name = csv_name.split(".csv")[0] + ".json"
            token_text_path = os.path.join(token_text_dir, token_json_name)
            with open(token_text_path, 'r') as json_file:
                # 加载 JSON 数据
                token_list = json.load(json_file)
            # print("token_list:", token_list)
            new_token_list = []
            for one in token_list:
                # print(one["token"])
                new_token_list.append(one["token"])

            # 取 output 里的前 token_len 个有效的预测结果
            token_len = len(new_token_list)
            outputs_list1 = outputs.squeeze().tolist()[0:token_len]

            # 使用 zip 将token 跟每个token的预测结果进行匹配
            pred_list = list(zip(new_token_list, outputs_list1))
            # print("pred_list:", pred_list)

            # 根据 var_location 取 output 中有效的预测结果
            test_var_location = test_var_location.squeeze().tolist()
            # print("val_var_location:", val_var_location)

            sorted_pred_list = []
            # 根据 var_location为1的位置, 取出pred_list中对应位置的元素
            for token_index, token_label in enumerate(test_var_location):
                if token_label == 1:
                    sorted_pred_list.append(pred_list[token_index])
            # print("未排序 sorted_pred_list:", sorted_pred_list)
            # 按照概率值大小对预测结果进行排序
            sorted_pred_list.sort(reverse=True, key=lambda x: x[1])
            # print("排序后 sorted_pred_list:", sorted_pred_list)

            # 读取 train_label 获取日志中记录的变量名
            label_dir = "./all_data/train_label"
            label_path = os.path.join(label_dir, csv_name)
            label_csv = pd.read_csv(label_path)
            # var_name_list 列表
            var_name_list = label_csv['var_name'].tolist()
            # print("var_name_list:", var_name_list)
            # all_label 列表
            label_list = label_csv['label'].tolist()
            # print("label_list:", label_list)
            # 根据 label_list 获得日志中记录的变量名
            ground_truth_list = []
            for index0, label in enumerate(label_list):
                if label == 1:
                    ground_truth_list.append(var_name_list[index0])
            # print("ground_truth_list:", ground_truth_list)

            # 根据模型预测结果, 取出对应的预测的变量名
            pred_var_name_list = []
            # print("概率从大到小排序后的局部变量推荐表:")
            for ele in sorted_pred_list:
                var_name = ele[0]  # 取出变量名
                # 不添加同名变量
                if var_name not in pred_var_name_list:
                    pred_var_name_list.append(var_name)
            # print("pred_var_name_list:", pred_var_name_list)

            # 从 pred_var_name_list 中取跟 ground_truth_list 变量个数一样的前几个预测变量
            limit_pred_var_name_list = pred_var_name_list[0:len(ground_truth_list)]
            # print("pred_var_name_list:", pred_var_name_list)
            # print("ground_truth_list :", ground_truth_list)

            # 计算模型预测的 acc
            correct_count = 0
            total_count = len(ground_truth_list)  # 日志中记录的变量个数
            for pred_var_name in limit_pred_var_name_list:  # 遍历 pred_var_name_list 中每个变量名
                if pred_var_name in ground_truth_list:
                    correct_count += 1
            sample_acc = correct_count / total_count
            # 添加模型预测的准确率
            test_acc_list.append(sample_acc)

            # 计算当前样本的 mrr
            mrr_result = calculate_mrr(ground_truth_list, pred_var_name_list)
            test_mrr_list.append(mrr_result)

            # 计算当前样本的top1_acc
            top1_result = top_k_acc(ground_truth_list, pred_var_name_list, k=1)
            test_top1_list.append(top1_result)

            # 计算当前样本的top2_acc
            top2_result = top_k_acc(ground_truth_list, pred_var_name_list, k=2)
            test_top2_list.append(top2_result)

    # 模型在测试集下的平均预测acc
    current_epoch_average_acc = sum(test_acc_list) / len(test_acc_list)
    print("test_acc:", current_epoch_average_acc)

    # 模型在测试集下的平均预测mrr
    test_mrr = sum(test_mrr_list) / len(test_mrr_list)
    print("test_mrr:", test_mrr)

    # 计算top1_acc
    test_top1_acc = sum(test_top1_list) / len(test_top1_list)
    print("test_top1_acc:", test_top1_acc)

    # 计算top2_acc
    test_top2_acc = sum(test_top2_list) / len(test_top2_list)
    print("test_top2_acc:", test_top2_acc)
