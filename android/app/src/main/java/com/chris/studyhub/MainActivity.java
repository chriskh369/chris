package com.chris.studyhub;

import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import com.getcapacitor.BridgeActivity;
import java.util.concurrent.TimeUnit;

public class MainActivity extends BridgeActivity {
    private static final String CHANNEL_ID = "studyhub_notifications";
    private static final int NOTIFICATION_PERMISSION_CODE = 1001;
    private static final String NOTIFICATION_WORK_TAG = "studyhub_notification_check";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Create notification channel
        createNotificationChannel();

        // Request notification permission for Android 13+
        requestNotificationPermission();

        // Schedule background notification checks
        scheduleNotificationWorker();

        // Disable cache to always get fresh content
        WebView webView = getBridge().getWebView();
        webView.getSettings().setCacheMode(android.webkit.WebSettings.LOAD_NO_CACHE);

        // Add JavaScript interface for notifications
        webView.addJavascriptInterface(new NotificationInterface(), "AndroidNotification");
    }

    private void scheduleNotificationWorker() {
        // Schedule periodic work to check for notifications every 15 minutes (minimum allowed)
        PeriodicWorkRequest notificationWork = new PeriodicWorkRequest.Builder(
                NotificationWorker.class,
                15, TimeUnit.MINUTES
        ).build();

        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
                NOTIFICATION_WORK_TAG,
                ExistingPeriodicWorkPolicy.KEEP,
                notificationWork
        );
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            CharSequence name = "StudyHub Notifications";
            String description = "Notifications for assignments and tests";
            int importance = NotificationManager.IMPORTANCE_HIGH;
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, name, importance);
            channel.setDescription(description);
            channel.enableVibration(true);
            channel.setVibrationPattern(new long[]{200, 100, 200});

            NotificationManager notificationManager = getSystemService(NotificationManager.class);
            notificationManager.createNotificationChannel(channel);
        }
    }

    private void requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.POST_NOTIFICATIONS},
                        NOTIFICATION_PERMISSION_CODE);
            }
        }
    }

    // JavaScript interface to show notifications from web
    public class NotificationInterface {
        @JavascriptInterface
        public void showNotification(String title, String message) {
            runOnUiThread(() -> {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    if (ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.POST_NOTIFICATIONS)
                            != PackageManager.PERMISSION_GRANTED) {
                        return;
                    }
                }

                NotificationCompat.Builder builder = new NotificationCompat.Builder(MainActivity.this, CHANNEL_ID)
                        .setSmallIcon(R.mipmap.ic_launcher)
                        .setContentTitle(title)
                        .setContentText(message)
                        .setPriority(NotificationCompat.PRIORITY_HIGH)
                        .setAutoCancel(true)
                        .setVibrate(new long[]{200, 100, 200});

                NotificationManagerCompat notificationManager = NotificationManagerCompat.from(MainActivity.this);
                notificationManager.notify((int) System.currentTimeMillis(), builder.build());
            });
        }
    }
}
