import os
import re
import pandas as pd
import json

"""
遍历项目中的方法字节码txt文件,
并提取里面的与日志语句相关的代码块
构建该方法字节码指令的csv文件
"""

def walkFile(dir_path,csv_save_dir,label_save_dir):
    for root, dirs, files in os.walk(dir_path):
        # root 表示当前正在访问的文件夹路径
        # dirs 表示当前访问的文件夹下的子目录名的 list
        # files 表示当前访问的文件夹下的文件名 list
        method_count = 0
        method_has_log_count = 0
        project_log_count = 0  # 统计有多少条日志
        method_has_log_log_var_count = set()
        log_has_var_count = 0  # 统计有多少条日志记录了局部变量
        save_csv_count = 0
        log_logvarnum_count = 0  # 统计记录了变量的日志语句中一共记录了多少变量

        max_length = 300
        max_local = 10

        # 遍历文件
        for file in files:
            # file 保存 每个txt 方法文件名
            # 如果访问的文件字节码指令txt文件
            if file.endswith('.txt'):

                # method_count 为读取的方法 txt 文件个数
                method_count += 1

                # 拼接 txt 文件的绝对路径
                file_path1 = os.path.join(root, file)
                # print(file_path1)

                # 读取 txt 方法字节码文件,获取里面的内容
                f1 = open(file_path1, "r")
                # print(f1)
                # 读取整个文件，将该方法保存到一个字符串变量content中
                bytecode_content = f1.read()
                f1.close()

                # 用于匹配日志语句的正则表达式
                pattern = re.compile(r"(?:L\d+\n)?"
                                     r"(?:GETSTATIC|INVOKESTATIC|GETFIELD) [\w/$().]+?\.(?:\w+ : |access\$\d+\s+\(\))Lorg/apache/log4j/Logger;"
                                     r"(?:(?!\nINVOKEVIRTUAL org/apache/log4j/Logger\.(?:isTraceEnabled|isDebugEnabled|isInfoEnabled|isWarnEnabled|isErrorEnabled|isFatalEnabled) \(\)Z)[\w\W])+?"
                                     r"(?:INVOKEINTERFACE|INVOKEVIRTUAL) org/apache/log4j/Logger\.(?:trace|debug|info|warn|error|fatal) [\w\/;[\$\(\)]+V\n"
                                     r"(?:GOTO L\d+\n)?")


                # 寻找content方法中的日志语句, 并把找到的日志语句以列表的形式返回,列表中的每个元素是一条日志代码块
                # 正则表达式 findall 方法能够以列表的形式返回能匹配的子串
                log_list = pattern.findall(bytecode_content)
                # 如果该方法的 log_list 不为空, 说明该方法中存在若干条日志语句
                if log_list:
                    # 统计含有日志语句的方法的数量
                    method_has_log_count += 1
                    # 计算该方法中有多少条日志语句,并累加到项目统计中
                    print(f"==========", file, f"中有 {len(log_list)} 条日志 ==========")
                    project_log_count += len(log_list)
                    # 按行分割方法字节码内容
                    content_list = bytecode_content.splitlines()

                    # 遍历该方法的 log_list 中每条日志语句, 构建去除该条日志的新方法
                    for log_index, log in enumerate(log_list):
                        print()
                        print(f"对 log {log_index} 进行解析:")
                        print(log)

                        log = log.splitlines()

                        log_start_index = 0  # 记录该日志在 content_list 方法中起始行号
                        log_end_index = 0  # 记录该日志在 content_list 方法中结束行号

                        # 遍历原始方法 content_list, 查找日志在原文中的起始行号和结束行号
                        for line_num, instruction in enumerate(content_list):
                            if line_num + len(log) <= len(content_list):
                                # 检查 log 的第一句和最后一句是否与方法的指令相同
                                if instruction == log[0] and content_list[line_num + len(log) - 1] == log[-1]:
                                    # 检查log中间的元素是否匹配
                                    match = True
                                    for i in range(1, len(log) - 1):
                                        if content_list[line_num + i] != log[i]:
                                            match = False
                                            break
                                    if match:
                                        log_start_index = line_num
                                        log_end_index = line_num + len(log) - 1
                                        print("log_start_index:", log_start_index)
                                        print("log_end_index:", log_end_index)

                        # 获取日志语句的行号范围
                        log_linenum_list = list(range(log_start_index, log_end_index + 1))
                        # print('日志作用行号log_linenum_list:', log_linenum_list)
                        print(f"log_{log_index}的起始行号为:{log_start_index}")
                        print(f"log_{log_index}的结束行号为:{log_end_index}")

                        print("方法字节码指令(原始): ")
                        # 打印按行分割后的每行字节码指令
                        for index, ele in enumerate(content_list):
                            print(index, ele)
                        # 根据日志的起始行号和结束行号, 构建去除该条日志的新方法 new_content_list0
                        new_content_list0 = content_list[0: log_start_index] + content_list[log_end_index + 1:]

                        print(f"删除log_{log_index}后的方法:")
                        for index, one in enumerate(new_content_list0):
                            print(index, one)

                        # 遍历 new_content_list0 中的局部变量表语句, 并把这些局部变量按照索引排序
                        local_var_set = set()  # 用于添加局部变量的集合
                        for index, statement in enumerate(new_content_list0):
                            if 'LOCALVARIABLE ' in statement:
                                # print()
                                # print("局部变量语句:", index, statement)
                                # print("局部变量表语句:", statement)
                                # 按空格切分局部变量语句
                                statement_list = statement.split()
                                # print("statement_list:", statement_list)
                                localvariable_name = statement_list[1]
                                # print("localvariable_name:", localvariable_name)
                                localvariable_sort = statement_list[2]
                                # print('localvariable_sort:', localvariable_sort)
                                localvariable_start = statement_list[3]
                                # print('localvariable_start:', localvariable_start)
                                localvariable_end = statement_list[4]
                                # print('localvariable_end:', localvariable_end)
                                localvariable_index = statement_list[5]
                                # print('localvariable_index:', localvariable_index)
                                # var_info 存放每个局部变量的索引, 变量的名字, 是否是日志中记录的变量
                                var_info = (int(localvariable_index), localvariable_name, 0)
                                # print("var_info:", var_info)
                                local_var_set.add(var_info)
                        # print("local_var_set:", local_var_set)

                        # 如果 local_tabel_set 不为空, 说明该方法中定义了局部变量
                        if local_var_set:
                            local_var_list = list(local_var_set)  # 把 local_var_set 转换成 list
                            # print("local_tabel_list:", local_tabel_list)
                            # 把列表中的元素由元组转换成列表
                            local_var_list = [list(t) for t in local_var_list]
                            # print("local_var_list       :", local_var_list)
                            # 按照每个元素的局部变量索引和变量名, 对 local_tabel_list 中的变量进行排序
                            local_var_list.sort(key=lambda x: x[0])
                            # if len(local_tabel_list) > 11:
                            # print("sorted local_var_list:", local_var_list)

                            # 遍历日志中每行字节码语句,提取该条日志中记录了哪些局部变量 (无重复)
                            log_var_set = set()
                            for statement in log:
                                # 如果该条指令是包含 @_ 那么就是局部变量加载指令
                                if '@_' in statement:
                                    print(f"日志 {log_index} 中记录的变量:", statement, "按@_分割后:",
                                          statement.split("@_"))
                                    # 去除 @_ 结尾符号提取变量名字
                                    var_list = statement.split("@_")
                                    var_load_insn = var_list[0]  # var_list = ['ALOAD 6', 'e']
                                    var_index = var_load_insn.split(" ")[1]
                                    var_name = var_list[1]
                                    var_index_name = (int(var_index), var_name)
                                    # 把日志语句中记录的局部变量信息(索引和名字)添加到 log_var_set 集合中
                                    log_var_set.add(var_index_name)
                                    print("var_index_name:", var_index_name)

                            # 如果 log_var_set 集合不为空, 说明该条日志中记录了局部变量
                            if log_var_set:
                                log_has_var_count += 1  # 统计所有日志语句中记录了局部变量的日志语句数量
                                log_logvarnum_count += len(log_var_set)  # 统计该条日志语句中记录了多少局部变量, 并累加到项目中
                                log_var_list = list(log_var_set)
                                print("log_var_list  :", log_var_list)
                                print("local_var_list:", local_var_list)
                                # 遍历 log_var_list中的日志变量, 查询它在 local_var_list 位置,并把该变量的 all_label 标记为 1
                                print("遍历日志变量:")
                                for log_var_index, log_var in enumerate(log_var_list):
                                    print(f"log_var{log_var_index}:", log_var)
                                    for local_var in local_var_list:
                                        # 如果变量的索引相同并且变量名相同,变量的label就标记为1
                                        if log_var[0] == local_var[0] and log_var[1] == local_var[1]:
                                            # if log_var[1] == local_var[1]:
                                            local_var[2] = 1
                                print("打标后local_var_list:", local_var_list)

                                if len(new_content_list0) <= max_length and len(local_var_list) <= max_local:
                                    save_csv_count += 1  # 统计符合条件的日志个数
                                    for index, one in enumerate(new_content_list0):
                                        # 去除方法中变量加载指令中的 @_ 标识符
                                        if "@_" in one:
                                            # print("呵呵", one, one.split("@_"))
                                            one_list = one.split("@_")
                                            var_index = one_list[0]
                                            var_name = one_list[1]
                                            # print("呵呵one_list:",one_list)
                                            new_content_list0[index] = var_index + " " + var_name
                                            # print("niu:", new_content_list0[index])

                                    # 构建保存去除日志后的方法体的 train_csv 文件
                                    data = {'methodContent': new_content_list0}
                                    df1 = pd.DataFrame(data)
                                    name = file.split('.txt')
                                    print('csv_name:', name[0])
                                    csv_name = name[0]
                                    train_data_name = f"{csv_name}_Log{log_index}.csv"
                                    method_has_log_log_var_count.add(csv_name)
                                    file_path2 = os.path.join(csv_save_dir, train_data_name)
                                    df1.to_csv(file_path2, mode='w', index=False)

                                    # 保存 all_label 数据
                                    df2 = pd.DataFrame(local_var_list, columns=['index', 'var_name', 'label'])
                                    file_path3 = os.path.join(label_save_dir, train_data_name)
                                    df2.to_csv(file_path3, mode='w', index=False)

        print(f"一共处理了 {method_count} 个方法字节码指令txt文件")
        print(f"有 {method_has_log_count} 个方法有日志语句")
        print(f"其中 {method_has_log_count} 个含有日志语句的方法中, 有 {len(method_has_log_log_var_count)} 个方法的日志语句中记录了局部变量")
        print(f"项目中一共有 {project_log_count} 条日志语句")
        print(f"项目中 {project_log_count} 条日志中有 {log_has_var_count} 条日志记录了局部变量")
        print(f"所有日志语句中一共记录了 {log_logvarnum_count} 个局部变量")
        print(f"满足行号和局部变量个数条件后, 保存了 {save_csv_count} 条日志训练csv数据")

if __name__ == '__main__':
    # 读取添加了局部变量名称的 txt 文件夹, 提取里面的方法
    targetDir      = "/hive/class-txt2"
    csv_save_dir   = "./all_data/log4j_csv"
    label_save_dir = "./all_data/log4j_label"
    walkFile(targetDir, csv_save_dir, label_save_dir)

