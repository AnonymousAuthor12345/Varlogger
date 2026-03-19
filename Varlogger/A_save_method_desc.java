package class2txt3;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lsieun.utils.FileUtils;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.LocalVariableNode;
import org.objectweb.asm.tree.MethodNode;
import org.objectweb.asm.tree.ParameterNode;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

// 保存方法描述符()
public class A_save_method_desc {
    public static int txtcount = 0;
    public static int method_count = 0;
    public static int classFile_count = 0; //统计处理的class文件个数(不包括接口)
    public static String classPath = "/Volumes/ExtremePro/300-10案例分析/hdfs/2.8.0/hadoop-hdfs-2.8.0";
    public static String savePath  = "/Volumes/ExtremePro/300-10案例分析/hdfs/2.8.0/method_desc";
    public static void main(String[] args) throws FileNotFoundException, JsonProcessingException {
        String filePath = classPath;
        File dir = new File(filePath);
        System.out.println("分析的项目的路径为:"+filePath);
        findClassFile(dir);
        System.out.println("处理的 class 文件的数量(不包括接口类):" + classFile_count);
        System.out.println("生成的方法描述符文件的数量为:" + txtcount);

    }
    public static void findClassFile(File dir) throws FileNotFoundException, JsonProcessingException {
        File[] files = dir.listFiles();
        if (files != null) {
            for (File file : files) {
                if (file.isFile()) {
                    String name = file.getName();
                    //判断是不是 class 文件
                    if (name.endsWith(".class")&& !name.startsWith("._")) {
                        // 对 class 文件进行分析
                        printInsn(file.getAbsolutePath());
                    }
                } else {
                    findClassFile(file);
                }
            }
        }
    }
    public static void printInsn(String filePath) throws FileNotFoundException, JsonProcessingException {
        File clsfile = new File(filePath);
        System.out.println("================================================="+clsfile.getName()+"文件信息"+"=================================================");

        //打印文件路径
        System.out.println("classfilePath:"+clsfile.getAbsoluteFile());
        String parentPath = clsfile.getParent(); // 获得父类路径
        System.out.println("parentPath   :"+parentPath);

        //打印class文件名字
        String name = clsfile.getName();
        System.out.println("clsfile_name :"+name);
        String[] split = name.split("\\.class");//按照.符号分割出不包含后缀.class的文件名
        String fileName = split[0];
        System.out.println("fileName     :"+fileName);

        //读取class文件的二进制字节码的信息
        byte[] bytes = FileUtils.readBytes(filePath);
        //1.构建ClassReader
        ClassReader cr = new ClassReader(bytes);
        //2.生成classNode
        int api = Opcodes.ASM9;
        ClassNode classNode = new ClassNode(api);
        int parsingOptions =ClassReader.SKIP_FRAMES;
        cr.accept(classNode,parsingOptions);

        //当前读取的 class 文件的信息
        //类全路径名 javax/jms/InvalidDestinationException
        String className = classNode.name;
        System.out.println("cls类全路径名  :"+className);

        //类的访问标识
        int classAccess = classNode.access;

        //判断 class 文件是不是接口
        boolean isInterface = ((Opcodes.ACC_INTERFACE & classAccess)!= 0);

        //如果 class 文件不是接口就进行处理
        if (!isInterface){
            classFile_count += 1;
            //3.获取 class 文件中所有的方法
            List<MethodNode> methods = classNode.methods;

            // 存储方法名的字典
            Map<String, Integer> methodNameCountMap = new HashMap<>();

            //遍历 class 文件中的每个方法 (每个方法表示为 methodNode 类)
            for (MethodNode methodNode : methods) {
                // 获取方法名
                String methodName = methodNode.name;
                // 获取方法描述符
                String methodDesc = methodNode.desc;
                System.out.println();
                System.out.println("   Method    :" + methodName + methodDesc);

                // 获取方法的访问标识
                int methodAccess = methodNode.access;

                // 获取方法接收的参数的变量名(如果 -parameters 参数有的话)
                if (methodNode.parameters != null) {
                    for (ParameterNode param : methodNode.parameters) {
                        System.out.println("   Parameter name: " + param.name);
                    }
                }

                // 解析方法的描述符转换成 Java 代码类型
                methodDesc = DescriptorParser.parseMethodDescriptor(methodDesc);
                System.out.println("   Java methodDesc: "+methodDesc);

                //判断处理的方法是否是抽象方法, native 方法, <init> 方法 和 <clinit> 方法
                boolean isAbstractMethod = ((methodAccess & Opcodes.ACC_ABSTRACT) == Opcodes.ACC_ABSTRACT);
                boolean isNativeMethod = ((methodAccess & Opcodes.ACC_NATIVE) == Opcodes.ACC_NATIVE);
                boolean isClinitMethod = (methodName.equals("<clinit>"));
                boolean isInitMethod = (methodName.equals("<init>"));

                // 如果非抽象方法 / Native方法 / <clinit>方法/ 就保存该方法的 instruction 和 local variable 信息
                if (!isAbstractMethod && !isNativeMethod && !isClinitMethod && !isInitMethod) {
                    System.out.println("methodName_desc :" + methodNode.name + methodNode.desc);
                    System.out.println("cls类全路径名    :"+className+".class");
                    method_count += 1;

                    // 输出方法中局部变量信息

                    List<Map<String, Object>> result = new ArrayList<>();
                    List<LocalVariableNode> localVariables = methodNode.localVariables;
                    for (LocalVariableNode var : localVariables) {
                        Map<String, Object> varInfo = new HashMap<>();
                        varInfo.put("name", var.name);
                        varInfo.put("desc", var.desc);
                        varInfo.put("index", var.index);
                        varInfo.put("start", var.start.getLabel().toString());
                        varInfo.put("end", var.end.getLabel().toString());
                        result.add(varInfo);
                    }


                    // 创建一个Map存储你要保存的数据
                    Map<String, Object> data = new HashMap<>();
                    data.put("class_path" , className+".class");
                    data.put("method_name", methodNode.name);
                    data.put("method_desc", methodNode.desc);
                    data.put("localtable" , result);

                    // 构建保存 txt 文件的地址
                    String className1 = className.replace("/", ".");
                    String jsonFileName = method_count + "@~" + className1 + "^" + methodName + "^" + methodDesc + ".json";
                    System.out.println("jsonFileName:" + jsonFileName);

                    // 定义json文件输出路径
                    Path json_save_path = Paths.get(savePath, jsonFileName);
                    System.out.println("json_save_path:"+json_save_path);

                    // 使用 Jackson 将 Map 写入 JSON 文件
                    ObjectMapper mapper = new ObjectMapper();
                    try {
                        mapper.writerWithDefaultPrettyPrinter().writeValue(json_save_path.toFile(), data);
                        System.out.println("保存成功，路径：" + json_save_path);
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }
        }
    }
}