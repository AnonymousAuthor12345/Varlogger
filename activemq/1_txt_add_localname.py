import os
import re

# 分析txt文件把局部变量表中的的对应变量名记录下来,
# 对应方法体中如果有该变量的加载指令就在指令的后面加上变量的名字
def change_load_index_to_name(dir_path,save_path):
    txt_count = 0
    save_txt_count = 0
    for root, dirs, files in os.walk(dir_path):
        # root 表示当前正在访问的文件夹路径
        # dirs 表示当前路径下子目录名的list
        # files 表示当前路径下文件名的list
        # 遍历文件
        for file in files:
            # 如果是txt文件
            if file.endswith('.txt'):
                print('==================================', file, '==================================')
                # txt_count 为读取的方法字节码指令 txt 文件个数
                txt_count += 1
                # 拼接 txt 文件的绝对路径
                file_path1 = os.path.join(root, file)
                f1 = open(file_path1, "r")
                # 读取 txt 方法字节码文件, 返回代码行列表
                content_list = f1.readlines()
                # print(content_list)
                f1.close()
                # print("content_list1:",content_list)
                print("原始方法为:")
                # 遍历方法字节码指令 content_list 把每条语句前后的空格删除
                for line_num, statement in enumerate(content_list):
                    content_list[line_num] = statement.strip()
                    print(line_num, statement.strip())

                # 遍历 content_list 方法查找每个局部变量
                for line_num, statement in enumerate(content_list):
                    # 判断是否是局部变量
                    if 'LOCALVARIABLE' in statement:
                        print()
                        print("局部变量语句:", statement)
                        # 按空格切分局部变量语句
                        statement_list = statement.split()
                        print("statement_list:", statement_list)
                        localvariable_name = statement_list[1]
                        print("localvariable_name:", localvariable_name)
                        localvariable_sort = statement_list[2]
                        print('localvariable_sort:', localvariable_sort)
                        localvariable_start = statement_list[3]
                        print('localvariable_start:', localvariable_start)
                        localvariable_end = statement_list[4]
                        print('localvariable_end:', localvariable_end)
                        localvariable_index = statement_list[5]
                        print('localvariable_index:', localvariable_index)

                        # 根据局部变量的类型, 判断该变量需要哪种加载(LOAD)指令与存储(STORE)指令
                        localvariable_load = None
                        localvariable_store = None
                        if localvariable_sort == 'Z':
                            localvariable_load = 'ILOAD'
                            localvariable_store = 'ISTORE'
                        elif localvariable_sort == 'B':
                            localvariable_load = 'ILOAD'
                            localvariable_store = 'ISTORE'
                        elif localvariable_sort == 'C':
                            localvariable_load = 'ILOAD'
                            localvariable_store = 'ISTORE'
                        elif localvariable_sort == 'S':
                            localvariable_load = 'ILOAD'
                            localvariable_store = 'ISTORE'
                        elif localvariable_sort == 'I':
                            localvariable_load = 'ILOAD'
                            localvariable_store = 'ISTORE'
                        elif localvariable_sort == 'D':
                            localvariable_load = 'DLOAD'
                            localvariable_store = 'DSTORE'
                        elif localvariable_sort == 'F':
                            localvariable_load = 'FLOAD'
                            localvariable_store = 'FSTORE'
                        elif localvariable_sort == 'J':
                            localvariable_load = 'LLOAD'
                            localvariable_store = 'LSTORE'
                        else:
                            localvariable_load = 'ALOAD'
                            localvariable_store = 'ASTORE'

                        # 获取对应局部变量类型的加载指令和存储指令
                        print("load_insn:", localvariable_load, localvariable_index)
                        print("store_insn:", localvariable_store, localvariable_index)

                        # 遍历方法, 确定该变量的作用域的起始行号和结束行号
                        index_list = []
                        for index, statement2 in enumerate(content_list):
                            # 如果当前语句是变量的作用域的开始, 就把该行的行号记录
                            if statement2 == localvariable_start:
                                index_list.append(index)
                            # 如果当前语句是变量的作用域的结束, 就把该行的行号记录
                            if statement2 == localvariable_end:
                                index_list.append(index)
                        print(f'该变量作用域范围: {localvariable_start}-{localvariable_end},'f'代码行:{index_list} ')  # 变量的作用域的起始行号和结束行号
                        print(" ")
                        print(f"作用域内 load {localvariable_index} 替换为变量名:")

                        # 遍历该变量作用域内的字节码, 把与该变量相关的 LOAD 加载指令, 替换为该变量的名字
                        for i in range(index_list[0], index_list[1]+1):
                            print(i, content_list[i])
                            # 加载指令 xLoad index
                            load_insn = f"{localvariable_load} {localvariable_index}"
                            # 如果当前遍历的指令是该局部变量的加载指令
                            if load_insn == content_list[i]:
                                # print("加载指令为:", statement_insn)
                                # new_load_insn = localvariable_load + " " + f"{localvariable_name}_"
                                new_load_insn = f"{load_insn}@_{localvariable_name}"
                                print("加载指令替换为:")
                                print(i, new_load_insn)
                                content_list[i] = new_load_insn

                        print(f"作用域内 store {localvariable_index} 替换为变量名:")

                        # 遍历该变量作用域内的字节码, 把与该变量相关的存储指令 STORE 去掉,并替换为该变量的名字
                        for i in range(index_list[0]-1, index_list[1] + 1):
                            print(i, content_list[i])
                            store_insn = f"{localvariable_store} {localvariable_index}"
                            # 如果遍历的指令是当前变量的加载指令
                            if store_insn == content_list[i]:
                                # print("存储指令为:", statement_insn)
                                # new_store_insn = localvariable_store + " " +f"{localvariable_name}_"
                                new_store_insn = f"{store_insn}@_{localvariable_name}"
                                print("存储指令替换为:")
                                print(i, new_store_insn)
                                content_list[i] = new_store_insn

                        print(f"======{localvariable_index}_{localvariable_name}替换后的方法======")
                        for index, content in enumerate(content_list):
                            print(index, content)

                # 保存文件
                new_txt_name = f"{file.split('.txt')[0]}.txt"
                print('new_txt_name:', new_txt_name)
                new_txt_path = os.path.join(save_path, new_txt_name)
                print("new_txt_path:", new_txt_path)
                with open(new_txt_path, mode='w') as f:
                    for one in content_list:
                        # 不写入含有注释的语句
                        if '// signature' in one or "// declaration:" in one or "LINENUMBER" in one:
                            continue
                        else:
                            f.write(one + '\n')
                save_txt_count += 1
    print(f"处理了 {txt_count} 个方法字节码文件")
    print(f"保存了 {save_txt_count} 个方法字节码文件")

if __name__ == '__main__':
    load_path = "./activemq/class-txt"
    save_path = "./activemq/class-txt2"
    change_load_index_to_name(load_path, save_path)

