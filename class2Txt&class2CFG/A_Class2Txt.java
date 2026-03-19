package class2txt3;
import lsieun.utils.FileUtils;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.tree.*;
import org.objectweb.asm.util.Textifier;
import org.objectweb.asm.util.TraceMethodVisitor;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class A_Class2Txt {
    public static int txtcount = 0;
    public static int method_count = 0;
    public static int classFile_count = 0;
    public static String classPath= "/Volumes/ExtremePro/varlogger分析项目/activemq/activemq-all-5.17.6";
    public static String savePath = "/Volumes/ExtremePro/varlogger分析项目/activemq/class-txt";
    public static void main(String[] args) throws FileNotFoundException {
        String filePath = classPath;
        File dir = new File(filePath);
        System.out.println("分析的项目的路径为:"+filePath);
        findClassFile(dir);
        System.out.println("处理的.class文件的数量(不包括接口类):" + classFile_count);
        System.out.println("生成的字节码方法的数量为:" + txtcount);
    }
    public static void findClassFile(File dir) throws FileNotFoundException {
        File[] files = dir.listFiles();
        if (files != null) {
            for (File file : files) {
                if (file.isFile()) {
                    String name = file.getName();
                    //判断是不是.class 文件
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

    public static void printInsn(String filePath) throws FileNotFoundException {
        File file = new File(filePath);
        System.out.println("================================================="+file.getName()+"文件信息"+"=================================================");

        //打印文件路径
        System.out.println("class文件路径 :"+file.getAbsoluteFile());
        String parentPath = file.getParent();
        System.out.println("parentPath   :"+parentPath);
        String name = file.getName();
        //打印class文件名字
        System.out.println("class name   :"+name);
        String[] split = name.split("\\.");//按照.符号分割出文件名
        String fileName = split[0];

        //读取文件的字节信息
        byte[] bytes = FileUtils.readBytes(filePath);
        //1.构建ClassReader
        ClassReader cr = new ClassReader(bytes);
        //2.生成classNode
        int api = Opcodes.ASM9;
        ClassNode classNode = new ClassNode(api);
        int parsingOptions =ClassReader.SKIP_FRAMES;
        cr.accept(classNode,parsingOptions);

        //当前读取的class文件的信息
        //类全路径名
        String className = classNode.name;
        System.out.println("cls类全路径名  :"+className);

        //类的访问标识
        int classAccess = classNode.access;
//        System.out.println("classAccess  :"+classAccess);

        //判断class文件是不是接口
        boolean isInterface = ((Opcodes.ACC_INTERFACE & classAccess)!= 0);
//        System.out.println("当前类文件是否是Interface:" + isInterface);
////
        //如果 class 文件不是接口就进行处理
        if (!isInterface){
            classFile_count += 1;
            //3.获取 class 文件中所有的方法
            List<MethodNode> methods = classNode.methods;
            // 存储方法名的字典
            Map<String, Integer> methodNameCountMap = new HashMap<>();

            //遍历 class 文件中的每个方法(每个方法表示为methodNode类)
            for (MethodNode methodNode : methods) {
                // 获取方法名
                String methodName = methodNode.name;
//                System.out.println("methodName:"+methodName);

                // 获取方法描述符
                String methodDesc = methodNode.desc;
//                System.out.println("methodDesc:"+methodDesc);
                System.out.println();
                System.out.println("   Method: " + methodName + methodDesc);

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

               //判断处理的方法是否是 抽象方法, native 方法, <init> 方法 和 <clinit> 方法
                boolean isAbstractMethod = ((methodAccess & Opcodes.ACC_ABSTRACT) == Opcodes.ACC_ABSTRACT);
                boolean isNativeMethod = ((methodAccess & Opcodes.ACC_NATIVE) == Opcodes.ACC_NATIVE);
                boolean isClinitMethod = (methodName.equals("<clinit>"));
                boolean isInitMethod = (methodName.equals("<init>"));

                //4.构建打印输出对象,打印输出 method 的 instruction
                Textifier printer = new Textifier();
                TraceMethodVisitor tmv = new TraceMethodVisitor(printer);

                //不处理 抽象方法 / Native 方法  / <clinit> 静态初始化方法 / <init> 构造方法
                if (!isAbstractMethod && !isNativeMethod && !isClinitMethod && !isInitMethod ) {
//                if (!isAbstractMethod && !isNativeMethod  && !isClinitMethod ) {
                    System.out.println("  符合方法筛选条件开始处理: " + methodNode.name + methodNode.desc);
                    InsnList instructions = methodNode.instructions;
                    for (AbstractInsnNode instruction : instructions) {
                        instruction.accept(tmv);
                    }

                    // 输出方法中局部变量信息
                    List<LocalVariableNode> localVariables = methodNode.localVariables;
                    System.out.println(localVariables);
                    for (LocalVariableNode localVariable : localVariables) {
//                        System.out.println("方法中局部变量信息:" +localVariable.name +" "+localVariable.desc+" "
//                                + localVariable.start.getLabel() +" "+localVariable.end.getLabel()+" "+localVariable.index);
                        localVariable.accept(tmv);
                    }
                }

                // 如果非抽象方法 / Native方法 / <clinit>方法/ 就保存该方法的 instruction 和 local variable 信息
                if (!isAbstractMethod && !isNativeMethod && !isClinitMethod && !isInitMethod) {
                        method_count += 1;
                        List<Object> list = printer.text;

                        //构建保存 txt 文件的地址
                        String className1 = className.replace("/",".");
                        String txtFileName = method_count+"@~"+className1+"^"+methodName+"^"+methodDesc+".txt";
                        System.out.println("   class_txt_FilePath:"+txtFileName);

                        // 保存符合条件的 method
                        File txtFile = new File(savePath, txtFileName);
                        printList(list ,txtFile, methodNode,
                                isAbstractMethod, isNativeMethod, isClinitMethod, isInitMethod,
                                className);
                }
            }
        }
    }

    private static void printList(List<?> list, File txtFilePath, MethodNode methodNode,
                                  boolean isAbstractMethod,boolean isNativeMethod,boolean isClinitMethod,boolean isInitMethod,
                                  String className)
            throws FileNotFoundException {
        if (!isAbstractMethod & !isNativeMethod & !isClinitMethod & !isInitMethod){
            try {
                txtcount++;
                PrintWriter writer = new PrintWriter(txtFilePath);
                printList(writer, list);
                writer.flush();
                writer.close();
            } catch (FileNotFoundException e) {
                System.out.println("无法创建文件，文件名可能太长或路径不正确: " + e.getMessage());
            }
        }
    }

    // 下面这段代码来自org.objectweb.asm.util.Printer.printList()方法
    private static void printList(final PrintWriter printWriter, final List<?> list) {
        for (Object o : list) {
            if (o instanceof List) {
                printList(printWriter, (List<?>) o);
            }
            else {
                printWriter.print(o);
            }
        }
    }
}