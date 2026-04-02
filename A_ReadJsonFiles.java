package exe;

import com.fasterxml.jackson.databind.ObjectMapper;
import lsieun.utils.FileUtils;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
public class A_ReadJsonFiles {
    public static int json_file_count = 0;
    public static int fault_file_count = 0;
    public static String class_file_dir   = "/Users/wangtaizheng/分析项目jar/activemq/activemq-client-5.16.7训练数据/activemq-client-5.16.7";
    public static String moniter_info_dir = "/Users/wangtaizheng/分析项目jar/activemq/activemq-client-5.16.7训练数据/activemq-client_moniter_info";
    public static String method_desc2_dir = "/Users/wangtaizheng/分析项目jar/activemq/activemq-client-5.16.7训练数据/method_desc2";

    public static void main(String[] args) throws IOException {
        System.out.println("class_file_dir  :" + class_file_dir);
        System.out.println("method_desc2_dir:" + method_desc2_dir);
        System.out.println("moniter_info_dir:" + moniter_info_dir);

        File jar_file = new File(class_file_dir);
        String jarName = jar_file.getName();
        System.out.println("最后一个文件夹名称是: " + jarName);


      // 遍历 moniter_info_dir 找到方法里面需要监控的变量
        File folder = new File(moniter_info_dir);
        listJsonFiles(folder, jarName);
        System.out.println("有 " + json_file_count + " 个 需要监控的 log json 文件");
    }
    // 遍历 jsonfile找到需要修改的方法
    public static void listJsonFiles(File folder, String jarName) throws IOException {
        File[] files = folder.listFiles();
        // 遍历 json 文件
        for (File moniter_info_file : files) {
            try {
                if (moniter_info_file.getName().endsWith(".json")) {
                    System.out.println();
                    json_file_count++;
                    System.out.println(json_file_count);
                    System.out.println("Found JSON file : " + moniter_info_file.getName());
                    System.out.println("JSON file path  : " + moniter_info_file.getAbsoluteFile());

                    // 构造监控的日志变量其对应方法 method_desc 文件名
                    // 按照 "_Log" 进行分割
                    String[] parts = moniter_info_file.getName().split("_Log");
//                 // 输出分割结果
//                 for (String part : parts) {
//                     System.out.println(part);
//                 }
                    String method_desc_name = parts[0] + ".json";
//                 System.out.println("method_desc_name: "+ method_desc_name);

                    // 找到对应的 method_desc 文件
                    Path method_desc2_path = Paths.get(method_desc2_dir, method_desc_name);
//                 System.out.println("method_desc 路径：" + path.toString());

                    // 读取 method_desc 内容
                    // 读取为 Map
                    ObjectMapper mapper = new ObjectMapper();
                    Map<String, Object> method_desc_data = mapper.readValue(method_desc2_path.toFile(), Map.class);
                    System.out.println("method_desc_data:" + method_desc_data);

                    // 1.获取 class_path
                    String classPath = (String) method_desc_data.get("class_path");
                    System.out.println("class_path: " + classPath);

                    // 2.获取 method_name
                    String methodName = (String) method_desc_data.get("method_name");
                    System.out.println("method_name: " + methodName);

                    // 3.获取 method_desc
                    String methodDesc = (String) method_desc_data.get("method_desc");
                    System.out.println("method_desc: " + methodDesc);


                    // 4. 获取 localtable
                    Object localtableObj = method_desc_data.get("localtable");
                    System.out.println("localtable:" + localtableObj);
                    if (localtableObj instanceof List) {
                        List<?> localtableList = (List<?>) localtableObj;
                        for (Object item : localtableList) {
                            if (item instanceof Map) {
                                Map<String, Object> varInfo = (Map<String, Object>) item;
                            }
                        }
                    }

                    // 读取 method_moniter_info 监控 var 的信息
                    ObjectMapper mapper2 = new ObjectMapper();
                    try {
                        // 读取 JSON 文件为 Map（也可以定义类替换 Map）
                        Map<String, Object> method_moniter_info_data = mapper2.readValue(moniter_info_file, Map.class);
//                     System.out.println("method_moniter_info_data:" + method_moniter_info_data);
                        List<Object> logVarInfo = (List<Object>) method_moniter_info_data.get("monitoring_var_info");
                        System.out.println("log_var_info:" + logVarInfo);

                        // 获取 var 的各种信息
                        int var_index = (Integer) logVarInfo.get(0);
                        String varName = (String) logVarInfo.get(1);
                        String varDesc = (String) logVarInfo.get(2);
                        String startLabel = "";
                        String endLabel = "";

                        System.out.println("var_index:" + var_index);
                        System.out.println("varName:" + varName);
                        System.out.println("varDesc:" + varDesc);

                        // 遍历 localtable 列表获取 moniter_var 的作用范围
                        List<?> localtableList2 = (List<?>) localtableObj;
                        for (Object item : localtableList2) {
                            if (item instanceof Map) {
                                Map<String, Object> local_varInfo = (Map<String, Object>) item;
//                             System.out.println("var_name: " + local_varInfo.get("name"));
//                             System.out.println("var_index: " + local_varInfo.get("index"));
                                int local_var_index = (Integer) local_varInfo.get("index");
//                             System.out.println("var_desc: " + local_varInfo.get("desc"));
//                             System.out.println("var_start: " + local_varInfo.get("start"));
//                             System.out.println("var_end: " + local_varInfo.get("end"));
//                             System.out.println();
                                if (local_varInfo.get("name").equals(varName) && local_var_index == var_index && local_varInfo.get("desc").equals(varDesc)) {
                                    startLabel = (String) local_varInfo.get("start");
                                    endLabel = (String) local_varInfo.get("end");
                                }

                            }
                        }
                        System.out.println("var_start:" + startLabel);
                        System.out.println("var_end:" + endLabel);


                        // 根据 class_path 读取具体的 class 文件
                        Path full_class_path = Paths.get(class_file_dir, classPath);
                        System.out.println("full_class_path: " + full_class_path);

                        // 读取具体的class文件内容保存为字节数组,并进行转换
                        byte[] bytes    = FileUtils.readBytes(String.valueOf(full_class_path));
                        byte[] newBytes = GenericVarMonitorInjector_LogToFile.injectMonitor(bytes, jarName, methodName, methodDesc, varName, var_index, varDesc);
                        // 写回 class 文件
                        Path outputPath = Paths.get(String.valueOf(full_class_path)); // 替换为原始 .class 文件路径
                        Files.write(outputPath, newBytes);
                        System.out.println("已写入修改后的 class 文件: " + outputPath.toAbsolutePath());
                    } catch (IOException e) {
                        System.out.println("读取 moniter_info 文件失败: " + moniter_info_file.getName());
                        e.printStackTrace();
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                }
            } catch (Throwable e) {
                System.err.println("跳过: " + moniter_info_file.getName() + "，原因：" + e);
                // 可以继续，也可以统计失败文件
                fault_file_count+=1;
            }
        }
        System.out.println("插装失败的文件数量为: "+ fault_file_count);
    }
}

