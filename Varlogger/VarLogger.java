package exe;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

public class VarLogger {

    private static final BlockingQueue<String> logQueue = new LinkedBlockingQueue<>(10000);
    private static BufferedWriter writer;
    private static volatile boolean running = true;
    private static final String LOG_FILE_PATH;
//    private static final SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS");

    static {
        String logPath;
        try {
            File jarFile = new File(VarLogger.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            File jarDir = jarFile.getParentFile();
            File logDir = new File(jarDir, "var_monitor");
            logPath = new File(logDir, "var_monitor.log").getAbsolutePath();
        } catch (URISyntaxException e) {
            logPath = "fallback-var_monitor/var_monitor.log";
            e.printStackTrace();
        }
        LOG_FILE_PATH = logPath;
        try {
            // 创建日志文件
            File logFile = new File(LOG_FILE_PATH);
            File parent = logFile.getParentFile();
            if (parent != null && !parent.exists()) parent.mkdirs();

            // 创建BufferedWriter来写入日志
            writer = new BufferedWriter(new FileWriter(logFile, true));

            // 创建日志写入线程
            Thread loggerThread = new Thread(() -> {
                List<String> buffer = new ArrayList<>(100); // 使用ArrayList缓冲日志
                long lastFlushTime = System.currentTimeMillis();

                try {
                    while (running || !logQueue.isEmpty()) {
                        // 批量取出队列中的日志
                        logQueue.drainTo(buffer, 100);

                        // 如果没有日志，可以使用较短的超时来阻塞等待
                        if (buffer.isEmpty()) {
                            String log = logQueue.poll(50, TimeUnit.MILLISECONDS);
                            if (log != null) buffer.add(log);
                        }

                        // 将批量日志写入文件
                        for (String log : buffer) {
                            writer.write(log);
                        }

                        // 控制flush的频率，避免过多的磁盘IO操作
                        long now = System.currentTimeMillis();
                        if (!buffer.isEmpty() || now - lastFlushTime > 200) {
                            writer.flush(); // 强制写入缓冲区
                            buffer.clear();
                            lastFlushTime = now;
                        }

                        // 休眠一段时间以减轻CPU占用
                        if (buffer.isEmpty()) {
                            Thread.sleep(100); // 适当的睡眠，避免高CPU占用
                        }
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt(); // 正确处理中断
                } catch (IOException e) {
                    e.printStackTrace();
                } finally {
                    // 确保在退出时写入所有剩余的日志并关闭
                    try {
                        writer.flush();
                        writer.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            });

            // 设置为守护线程，这样程序退出时可以自动退出该线程
            loggerThread.setDaemon(true);
            loggerThread.start();

            // 注册关闭钩子，确保在应用结束时能够优雅退出
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                running = false;  // 设置running标志为false
                try {
                    loggerThread.join(); // 等待日志写入线程结束
                } catch (InterruptedException ignored) {}
            }));

        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    private static void enqueue(String log) {
        logQueue.offer(log);
    }

//    private static String getTimestamp() {
//        return dateFormat.format(new Date());
//    }

    private static String formatLog(int index, Object value, String cls, String mth, String desc, String jarName) {
        StringBuilder logBuilder = new StringBuilder();  // 初始容量足够避免频繁扩容
        logBuilder.append('[').append(jarName)
                .append("] [jar=").append(jarName)
                .append("] [class=").append(cls)
                .append(", method=").append(mth)
                .append(desc)
                .append("] var[").append(index)
                .append("] = ").append(value)
                .append(System.lineSeparator());
        return logBuilder.toString();
    }

    public static void logInt(int index, int value, String cls, String mth, String desc, String jarName) {
        enqueue(formatLog(index, value, cls, mth, desc, jarName));
    }

    public static void logLong(int index, long value, String cls, String mth, String desc, String jarName) {
        enqueue(formatLog(index, value, cls, mth, desc, jarName));
    }

    public static void logFloat(int index, float value, String cls, String mth, String desc, String jarName) {
        enqueue(formatLog(index, value, cls, mth, desc, jarName));
    }

    public static void logDouble(int index, double value, String cls, String mth, String desc, String jarName) {
        enqueue(formatLog(index, value, cls, mth, desc, jarName));
    }

    public static void logObject(int index, Object value, String cls, String mth, String desc, String jarName) {
        enqueue(formatLog(index, value, cls, mth, desc, jarName));
    }
}