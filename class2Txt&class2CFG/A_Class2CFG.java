import soot.*;
import soot.jimple.JimpleBody;
import soot.options.Options;
import soot.toolkits.graph.*;
import java.io.*;
import java.util.*;

import static soot.SootClass.HIERARCHY;

public class A_Class2CFG_2 {
    public static final String jar_path = "/Users/varlogger-jar-data/hive-jar2";
    public static final String cfgPath  = "/Users/varlogger分析项目/hive2/class-cfg";
    public static final String output   = "/Users/varlogger分析项目/hive2/class-jimple";
    public static int class_count = 0;
    public static int method_count = 0;
    public static void sootSetup(String jar_path) {
        G.reset();
        // 输出格式
        Options.v().set_output_format(Options.output_format_jimple);
        Scene.v().addBasicClass("org.apache.amoro.shade.guava32.com.google.common.base.Predicate",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction0$mcZ$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction0$mcV$sp", HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction1$mcZI$sp", HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction1$mcII$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction0$mcC$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction0$mcI$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction1$mcVI$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction0$mcJ$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction0$mcB$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction1$mcVJ$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction2$mcIII$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction2$mcJJJ$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction1$mcZD$sp",HIERARCHY);
        Scene.v().addBasicClass("scala.runtime.java8.JFunction1$mcJJ$sp",HIERARCHY);
        Scene.v().addBasicClass("io.netty.channel.ChannelFutureListener",HIERARCHY);
        Scene.v().addBasicClass("org.springframework.cglib.proxy.MethodInterceptor",HIERARCHY);
        Options.v().set_whole_program(true);

        // 输入路径
//      Options.v().set_output_dir(output); // 设置 IR Jimple 的输出目录
        Options.v().set_process_dir(Collections.singletonList(jar_path));
        Options.v().set_prepend_classpath(true);
        Options.v().set_src_prec(Options.src_prec_class);
        Options.v().set_keep_line_number(true);

        Options.v().set_whole_program(true); //全程序分析
        Options.v().set_verbose(true); //显示详细信息
//        Options.v().set_no_bodies_for_excluded(true); //不加载被排除的类 / callgraph 边会减少很多
        Options.v().set_allow_phantom_refs(true); // 找不到对应的源代码就被称作是虚类（phantom class),允许虚类存在不报错
        Options.v().set_no_writeout_body_releasing(true);//不释放Body

        Scene.v().loadNecessaryClasses();   // 加载 Soot 依赖的类和命令行指定的类
        try {
            PackManager.v().writeOutput();  // 关键：启动输出。（不运行此语句不会进行输出）
        } catch (CompilationDeathException e) {
            if (e.getCause() instanceof FileNotFoundException) {
                System.out.println("文件名过长或路径不正确，跳过该文件");
            }
        }catch (ClassCastException e){
            System.out.println("ClassCastException，跳过该文件");
        }catch (RuntimeException e){
            System.out.println("RuntimeException，跳过该文件");
        }
    }

    public static String UnitsgraphToDot(ClassicCompleteUnitGraph graph) {
        StringBuilder dot = new StringBuilder();
        dot.append("digraph G {\n");

        // 遍历图中的每个节点
        for (Unit unit : graph) {
            String unitStr = unit.toString().replace('"', '\'').replace("\n", "\\l");
            dot.append("\"").append(unitStr).append("\";\n");
            // 遍历当前节点的后继节点，并为它们创建边
            for (Unit successor : graph.getSuccsOf(unit)) {
                String succStr = successor.toString().replace('"', '\'').replace("\n", "\\l");
                dot.append("\"").append(unitStr).append("\" -> \"").append(succStr).append("\";\n");
            }
        }
        dot.append("}\n");
        return dot.toString();
    }

    public static void main(String[] args) throws IOException {
        File jar_dir = new File(jar_path);
        System.out.println("jar_dir:"+jar_dir);
        File[] jar_files = jar_dir.listFiles();
        int jar_count = 0;
        for (File jar_file : jar_files) {
            System.out.println("jar_file:"+jar_file);
            if (jar_file.isFile()){
                String name = jar_file.getName();
                if (name.endsWith(".jar")&& !name.startsWith("._")) {
                    System.out.println("jar_name:"+name);
                    jar_count++;
                    // 分析每个jar包文件
                    sootSetup(jar_file.getAbsolutePath());

                    // 遍历jar包文件获取每个class文件
                    for (SootClass sc : Scene.v().getClasses()) {
                        System.out.println(sc);
                        String packName = "org.apache.activemq";
                        String javaPackageName = sc.getJavaPackageName();
                        boolean is_activemq_package = javaPackageName.contains(packName);
                        // 不对接口进行处理
                        if (!sc.isInterface()) {
                            // 创建一个 HashMap 来存储该class文件中方法名及其出现的次数
                            Map<String, Integer> methodNameCountMap = new HashMap<>();
                            SootClass cls = Scene.v().loadClassAndSupport(sc.getName());
//                            System.out.println("--------------------------------------------------------");
//                            System.out.println("包名:" + cls.getJavaPackageName());
//                            System.out.println("类名:" + cls.getName());
                            String package_name = cls.getJavaPackageName();
                            // 统计处理的class文件的数量
                            // 遍历class文件中的每个方法
                            for (SootMethod sootMethod : cls.getMethods()) {
                                // 如果方法有方法体
                                if (sootMethod.hasActiveBody() && !sootMethod.isAbstract() && !sootMethod.isNative() &&
                                        !sootMethod.isStaticInitializer() && !sootMethod.isConstructor()) {
                                    // 获取每个方法的信息
//                                    System.out.println();
                                    System.out.println("   方法名:" + sootMethod.getName());
                                    System.out.println("   方法所属类:" + sootMethod.getDeclaringClass().getName());
//                                    System.out.println("   方法签名:" + sootMethod.getSignature());     // 签名
//                                    System.out.println("   方法子签名" + sootMethod.getSubSignature()); // 子签名

                                    // 获得对应方法的 Jimple 格式 body
                                    JimpleBody body = (JimpleBody) sootMethod.retrieveActiveBody();
//                                    System.out.println("Jimple Units:");
                                    int c = 1;
                                    // 获取方法的Jimple代码的每行语句
                                    for (Unit u : body.getUnits()) {
                                        System.out.println("   (" + c + ") " + u.toString());
                                        c++;
                                    }

                                    // 根据 Jimple body 获得 基于 Block 的控制流图
                                    ZonedBlockGraph blocks = new ZonedBlockGraph(body);
//                                    System.out.println("ZonedBlockGraph:");
//                                    System.out.println(blocks.toString());

                                    // 如果方法名字典中不包含该方法名
                                    if (!methodNameCountMap.containsKey(sootMethod.getName())){
                                        methodNameCountMap.put(sootMethod.getName(),1);
                                        String method_name = cls.getName()+"_"+sootMethod.getName()+"_"+1+".txt";
                                        String method_path = cfgPath+'/'+method_name;
//                            System.out.println(method_path);
                                        try {
                                            // 创建一个FileWriter对象，指定要写入的文件名
                                            FileWriter fileWriter = new FileWriter(method_path);
                                            // 创建一个PrintWriter对象，它可以更方便地写入字符串到文件
                                            PrintWriter printWriter = new PrintWriter(fileWriter);

                                            // 将units的字符串表示形式写入文件
                                            printWriter.print(blocks.toString());
                                            // 关闭PrintWriter和FileWriter
                                            printWriter.close();
                                            fileWriter.close();
                                        } catch (FileNotFoundException  e) {
                                            System.out.println("无法创建文件，文件名可能太长或路径不正确");
                                        } catch (RuntimeException | IOException e) {
                                            System.out.println("无法创建文件");;
                                        }
                                    }
                                    else{
                                        // 如果方法名字典中已经存在该方法名
                                        methodNameCountMap.put(sootMethod.getName(), methodNameCountMap.get(sootMethod.getName()) + 1);
                                        String method_name = cls.getName()+"_"+sootMethod.getName()+"_"+methodNameCountMap.get(sootMethod.getName())+".txt";
                                        String method_path = cfgPath+"/"+method_name;
//                            System.out.println(method_path);
                                        try {
                                            // 创建一个FileWriter对象，指定要写入的文件名
                                            FileWriter fileWriter = new FileWriter(method_path);
                                            // 创建一个PrintWriter对象，它可以更方便地写入字符串到文件
                                            PrintWriter printWriter = new PrintWriter(fileWriter);

                                            // 将units的字符串表示形式写入文件
                                            printWriter.print(blocks.toString());
                                            // 关闭PrintWriter和FileWriter
                                            printWriter.close();
                                            fileWriter.close();
                                        } catch (FileNotFoundException  e) {
                                            System.out.println("无法创建文件，文件名可能太长或路径不正确");
                                        } catch (RuntimeException | IOException e) {
                                            System.out.println("无法创建文件");;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        System.out.println("处理了"+jar_count+"个jar文件");
    }
}



