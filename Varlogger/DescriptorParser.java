package class2txt3;

public class DescriptorParser {
    public static String parseMethodDescriptor(String descriptor) {
        StringBuilder result = new StringBuilder();  // 用于存储和返回解析结果
        // 提取括号内方法接收的形参
        String params = descriptor.substring(descriptor.indexOf('(') + 1, descriptor.indexOf(')'));

        // 检查是否没有参数,如果没有形参就返回none
        if (params.isEmpty()) {
            return "none";
        }

        // 如果有形参,就处理每个参数
        while (!params.isEmpty()) {
            if (params.charAt(0) == 'L') {
                // 类型引用
                String fullType = params.substring(1, params.indexOf(';')).replace('/', '.');
//                System.out.println("fullType: "+fullType);

                String simpleType = simplifyTypeName(fullType);
//                System.out.println("simpleType: "+simpleType);
                appendResult(result, simpleType);
                params = params.substring(params.indexOf(';') + 1);
            } else if (params.charAt(0) == '[') {
                // 数组类型
                int count = 1;
                while (params.charAt(count) == '[') {
                    count++;  // 计算维度
                }
                String type;
                if (params.charAt(count) == 'L') {
                    // 对象数组
                    int end = params.indexOf(';', count);
                    String fullType = params.substring(count + 1, end).replace('/', '.');
                    String simpleType = simplifyTypeName(fullType);
                    type = simpleType + getArrayBrackets(count);
                    params = params.substring(end + 1);
                } else {
                    // 基本类型数组
                    type = getPrimitiveType(params.charAt(count)) + getArrayBrackets(count);
                    params = params.substring(count + 1);
                }
                appendResult(result, type);
            } else {
                // 基本类型
                char typeChar = params.charAt(0);
                appendResult(result, getPrimitiveType(typeChar));
                params = params.substring(1);
            }
        }
        return result.toString();
    }

    private static void appendResult(StringBuilder result, String type) {
        if (result.length() > 0) {
            result.append('&');
        }
        result.append(type);
    }

    private static String simplifyTypeName(String fullTypeName) {
            // 找到最后一个.的位置
            int lastDotIndex = fullTypeName.lastIndexOf('.');
            if (lastDotIndex != -1) {
                String typeName =  fullTypeName.substring(lastDotIndex + 1);
                // 如果 typeName 中包含 $ 就表示是内部类,就分割内部类
                if (typeName.contains("$")){
                    String[] parts = fullTypeName.split("\\$");
                    typeName = parts[parts.length - 1];
                }
//                System.out.println("typeName: "+typeName);
                return typeName;
            } else {
                // 如果 typeName 中包含$就表示是内部类,就分割内部类
                if (fullTypeName.contains("$")){
                    String[] parts = fullTypeName.split("\\$");
                    fullTypeName = parts[parts.length - 1];
                }
                return fullTypeName;
            }
        }



    private static String getArrayBrackets(int dimensions) {
        StringBuilder brackets = new StringBuilder();
        for (int i = 0; i < dimensions; i++) {
            brackets.append("[]");
        }
        return brackets.toString();
    }

    private static String getPrimitiveType(char typeChar) {
        switch (typeChar) {
            case 'B': return "byte";
            case 'C': return "char";
            case 'D': return "double";
            case 'F': return "float";
            case 'I': return "int";
            case 'J': return "long";
            case 'S': return "short";
            case 'Z': return "boolean";
            case 'V': return "void";  // 通常用于返回类型
            default: return "?";
        }
    }

    public static void main(String[] args) {
        String result = parseMethodDescriptor("(Lorg/apache/accumulo/core/client/impl/ThriftTransportPool$CachedTTransport;)V");
        System.out.println(result); // 输出 "none"
    }
}
