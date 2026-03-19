package exe;

import org.objectweb.asm.*;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.LocalVariableNode;
import org.objectweb.asm.tree.MethodNode;

public class GenericVarMonitorInjector_LogToFile3 {
    public static byte[] injectMonitor(byte[] classBytes,
                                       String jarName,
                                       String methodName, String methodDesc,
                                       String varName, int varIndex,
                                       String varDesc) throws Exception {
        ClassNode cn = new ClassNode();
        ClassReader cr = new ClassReader(classBytes);
        cr.accept(cn, ClassReader.EXPAND_FRAMES);

        Label startLabel = null;
        Label endLabel = null;
        String className = cn.name;

        for (MethodNode mn : cn.methods) {
            if (mn.name.equals(methodName) && mn.desc.equals(methodDesc)) {
                if (mn.localVariables != null) {
                    for (LocalVariableNode localvar : mn.localVariables) {
                        if (localvar.name.equals(varName) &&
                                localvar.index == varIndex &&
                                localvar.desc.equals(varDesc)) {
                            startLabel = localvar.start.getLabel();
                            endLabel = localvar.end.getLabel();
                            break;
                        }
                    }
                }
            }
        }

        if (startLabel == null || endLabel == null) {
            throw new RuntimeException("目标变量未找到，请检查输入参数！");
        }

        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_FRAMES);
        cn.accept(new MonitorInsertCV(Opcodes.ASM9, cw, jarName, className, methodName, methodDesc,
                varIndex, varName, varDesc, startLabel, endLabel));
        return cw.toByteArray();
    }

    static class MonitorInsertCV extends ClassVisitor {
        private final String className, methodName, methodDesc, varDesc, varName;
        private final String jarName;
        private final int varIndex;
        private final Label startLabel, endLabel;

        MonitorInsertCV(int api, ClassVisitor cv,
                        String jarName, String className, String methodName, String methodDesc,
                        int varIndex, String varName, String varDesc,
                        Label startLabel, Label endLabel) {
            super(api, cv);
            this.jarName = jarName;
            this.className = className;
            this.methodName = methodName;
            this.methodDesc = methodDesc;
            this.varIndex = varIndex;
            this.varName = varName;
            this.varDesc = varDesc;
            this.startLabel = startLabel;
            this.endLabel = endLabel;
        }

        @Override
        public MethodVisitor visitMethod(int access, String name, String desc, String sig, String[] exceptions) {
            MethodVisitor mv = super.visitMethod(access, name, desc, sig, exceptions);
            if (name.equals(methodName) && desc.equals(methodDesc)) {
                return new MonitorMV(api, mv, jarName, className, methodName, methodDesc, varIndex, varDesc, startLabel, endLabel);
            }
            return mv;
        }
    }

    static class MonitorMV extends MethodVisitor {
        private final int varIndex;
        private final String varDesc;
        private final String className, methodName, methodDesc;
        private final Label startLabel, endLabel;
        private boolean inScope = false;
        private final String jarName;

        MonitorMV(int api, MethodVisitor mv,
                  String jarName,
                  String className,
                  String methodName, String methodDesc,
                  int varIndex, String varDesc,
                  Label startLabel, Label endLabel) {
            super(api, mv);
            this.jarName = jarName;
            this.className = className;
            this.methodName = methodName;
            this.methodDesc = methodDesc;
            this.varIndex = varIndex;
            this.varDesc = varDesc;
            this.startLabel = startLabel;
            this.endLabel = endLabel;
        }

        @Override
        public void visitLabel(Label label) {
            if (label == startLabel) inScope = true;
            if (label == endLabel) inScope = false;
            super.visitLabel(label);
        }

        @Override
        public void visitVarInsn(int opcode, int var) {
            if (inScope && var == varIndex) {
                super.visitVarInsn(opcode, var);
                char typeChar = varDesc.charAt(0);

                // 插入 log 调用
                switch (typeChar) {
                    case 'I':
                        if (opcode == Opcodes.ILOAD || opcode == Opcodes.ISTORE) {
                            super.visitInsn(Opcodes.DUP);
                            super.visitIntInsn(Opcodes.BIPUSH, varIndex);
                            super.visitInsn(Opcodes.SWAP);
                            super.visitLdcInsn(className);
                            super.visitLdcInsn(methodName);
                            super.visitLdcInsn(methodDesc);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,
                                    "exe/VarLogger",
                                    "logInt",
                                    "(IILjava/lang/String;Ljava/lang/String;Ljava/lang/String;)V",
                                    false);
                        }
                        break;
                    case 'J':
                        if (opcode == Opcodes.LLOAD || opcode == Opcodes.LSTORE) {
                            super.visitInsn(Opcodes.DUP2);
                            super.visitIntInsn(Opcodes.BIPUSH, varIndex);
                            super.visitInsn(Opcodes.DUP_X2);
                            super.visitInsn(Opcodes.POP);
                            super.visitLdcInsn(className);
                            super.visitLdcInsn(methodName);
                            super.visitLdcInsn(methodDesc);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,
                                    "exe/VarLogger",
                                    "logLong",
                                    "(IJLjava/lang/String;Ljava/lang/String;Ljava/lang/String;)V",
                                    false);
                        }
                        break;
                    case 'F':
                        if (opcode == Opcodes.FLOAD || opcode == Opcodes.FSTORE) {
                            super.visitInsn(Opcodes.DUP);
                            super.visitIntInsn(Opcodes.BIPUSH, varIndex);
                            super.visitInsn(Opcodes.SWAP);
                            super.visitLdcInsn(className);
                            super.visitLdcInsn(methodName);
                            super.visitLdcInsn(methodDesc);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,
                                    "exe/VarLogger",
                                    "logFloat",
                                    "(IFLjava/lang/String;Ljava/lang/String;Ljava/lang/String;)V",
                                    false);
                        }
                        break;
                    case 'D':
                        if (opcode == Opcodes.DLOAD || opcode == Opcodes.DSTORE) {
                            super.visitInsn(Opcodes.DUP2);
                            super.visitIntInsn(Opcodes.BIPUSH, varIndex);
                            super.visitInsn(Opcodes.DUP_X2);
                            super.visitInsn(Opcodes.POP);
                            super.visitLdcInsn(className);
                            super.visitLdcInsn(methodName);
                            super.visitLdcInsn(methodDesc);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,
                                    "exe/VarLogger",
                                    "logDouble",
                                    "(IDLjava/lang/String;Ljava/lang/String;Ljava/lang/String;)V",
                                    false);
                        }
                        break;
                    case 'L':
                    case '[':
                        if (opcode == Opcodes.ALOAD || opcode == Opcodes.ASTORE) {
                            super.visitInsn(Opcodes.DUP);
                            super.visitIntInsn(Opcodes.BIPUSH, varIndex);
                            super.visitInsn(Opcodes.SWAP);
                            super.visitLdcInsn(className);
                            super.visitLdcInsn(methodName);
                            super.visitLdcInsn(methodDesc);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,
                                    "exe/VarLogger",
                                    "logObject",
                                    "(ILjava/lang/Object;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V",
                                    false);
                        }
                        break;
                }
            } else {
                super.visitVarInsn(opcode, var);
            }
        }
    }
}
