package com.chris.studyhub;

import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private static final String TAG = "StudyHub";
    private static final String CHANNEL_ID = "studyhub_notifications";
    private static final int NOTIFICATION_PERMISSION_CODE = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Log.d(TAG, "=== MainActivity onCreate ===");

        // Create notification channel FIRST
        createNotificationChannel();

        // Request notification permission for Android 13+
        requestNotificationPermission();

        // Schedule background notifications using AlarmManager
        NotificationScheduler.scheduleImmediate(this); // Test immediately
        NotificationScheduler.scheduleNextAlarm(this); // Then every 15 min

        // Disable cache
        WebView webView = getBridge().getWebView();
        webView.getSettings().setCacheMode(android.webkit.WebSettings.LOAD_NO_CACHE);

        // Add JavaScript interface
        webView.addJavascriptInterface(new NotificationInterface(), "AndroidNotification");

        Log.d(TAG, "=== MainActivity setup complete ===");
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == NOTIFICATION_PERMISSION_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Log.d(TAG, "Notification permission GRANTED");
                // Permission granted, schedule immediate test
                NotificationScheduler.scheduleImmediate(this);
            } else {
                Log.w(TAG, "Notification permission DENIED");
            }
        }
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "StudyHub Notifications",
                    NotificationManager.IMPORTANCE_HIGH
            );
            channel.setDescription("Notifications for assignments and tests");
            channel.enableVibration(true);
            channel.setVibrationPattern(new long[]{200, 100, 200});

            NotificationManager notificationManager = getSystemService(NotificationManager.class);
            if (notificationManager != null) {
                notificationManager.createNotificationChannel(channel);
                Log.d(TAG, "Notification channel created");
            }
        }
    }

    private void requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                Log.d(TAG, "Requesting notification permission...");
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.POST_NOTIFICATIONS},
                        NOTIFICATION_PERMISSION_CODE);
            } else {
                Log.d(TAG, "Notification permission already granted");
            }
        }
    }

    // JavaScript interface to show notifications from web
    public class NotificationInterface {
        @JavascriptInterface
        public void showNotification(String title, String message) {
            Log.d(TAG, "JS called showNotification: " + title);
            runOnUiThread(() -> {
                try {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        if (ContextCompat.checkSelfPermission(MainActivity.this, Manifest.permission.POST_NOTIFICATIONS)
                                != PackageManager.PERMISSION_GRANTED) {
                            Log.w(TAG, "No permission for JS notification");
                            return;
                        }
                    }

                    NotificationCompat.Builder builder = new NotificationCompat.Builder(MainActivity.this, CHANNEL_ID)
                            .setSmallIcon(R.mipmap.ic_launcher)
                            .setContentTitle(title)
                            .setContentText(message)
                            .setPriority(NotificationCompat.PRIORITY_HIGH)
                            .setAutoCancel(true)
                            .setDefaults(NotificationCompat.DEFAULT_ALL);

                    NotificationManagerCompat notificationManager = NotificationManagerCompat.from(MainActivity.this);
                    notificationManager.notify((int) System.currentTimeMillis(), builder.build());
                    Log.d(TAG, "JS notification sent");
                } catch (Exception e) {
                    Log.e(TAG, "Error in JS notification: " + e.getMessage());
                }
            });
        }
    }
}
