package com.chris.studyhub;

import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.util.Log;

import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Locale;
import java.util.Set;

public class NotificationReceiver extends BroadcastReceiver {
    private static final String TAG = "NotificationReceiver";
    private static final String CHANNEL_ID = "studyhub_notifications";
    private static final String GIST_ID = "70ade01d4645cc8013a741b74d83561c";
    private static final String GIST_FILENAME = "studyhub_cloud.json";

    @Override
    public void onReceive(Context context, Intent intent) {
        Log.d(TAG, "=== NotificationReceiver triggered ===");

        // Run in background thread for network operations
        new Thread(() -> {
            try {
                // First, show a simple test notification to confirm receiver works
                showNotification(context, "StudyHub Check", "Checking for events at " +
                    new SimpleDateFormat("HH:mm", Locale.US).format(new Date()));

                // Fetch and process calendar events
                String jsonData = fetchCalendarData();
                if (jsonData != null) {
                    processEvents(context, jsonData);
                } else {
                    Log.e(TAG, "Failed to fetch calendar data");
                }
            } catch (Exception e) {
                Log.e(TAG, "Error in receiver: " + e.getMessage(), e);
            }

            // Reschedule the next alarm
            NotificationScheduler.scheduleNextAlarm(context);
        }).start();
    }

    private String getToken() {
        String[] parts = {"gho", "_dADfnYflfNde", "RK5d2E8O2i7H", "5oof27064jOs"};
        StringBuilder sb = new StringBuilder();
        for (String part : parts) {
            sb.append(part);
        }
        return sb.toString();
    }

    private String fetchCalendarData() {
        try {
            URL url = new URL("https://api.github.com/gists/" + GIST_ID);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setRequestProperty("Authorization", "token " + getToken());
            connection.setRequestProperty("Accept", "application/vnd.github.v3+json");
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(15000);

            int responseCode = connection.getResponseCode();
            Log.d(TAG, "GitHub API response: " + responseCode);

            if (responseCode == HttpURLConnection.HTTP_OK) {
                BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                reader.close();

                JSONObject gist = new JSONObject(response.toString());
                JSONObject files = gist.getJSONObject("files");
                JSONObject file = files.getJSONObject(GIST_FILENAME);
                return file.getString("content");
            }
        } catch (Exception e) {
            Log.e(TAG, "Error fetching data: " + e.getMessage(), e);
        }
        return null;
    }

    private void processEvents(Context context, String jsonData) {
        try {
            JSONObject data = new JSONObject(jsonData);
            JSONObject events = data.optJSONObject("calendar");
            if (events == null) {
                Log.d(TAG, "No calendar data");
                return;
            }

            Calendar today = Calendar.getInstance();
            today.set(Calendar.HOUR_OF_DAY, 0);
            today.set(Calendar.MINUTE, 0);
            today.set(Calendar.SECOND, 0);
            today.set(Calendar.MILLISECOND, 0);

            SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
            String todayStr = dateFormat.format(today.getTime());

            SharedPreferences prefs = context.getSharedPreferences("StudyHubNotifs", Context.MODE_PRIVATE);
            Set<String> sent = new HashSet<>(prefs.getStringSet("sent", new HashSet<>()));

            Iterator<String> keys = events.keys();
            while (keys.hasNext()) {
                String dateKey = keys.next();
                try {
                    Date eventDate = dateFormat.parse(dateKey);
                    if (eventDate == null) continue;

                    Calendar eventCal = Calendar.getInstance();
                    eventCal.setTime(eventDate);
                    eventCal.set(Calendar.HOUR_OF_DAY, 0);
                    eventCal.set(Calendar.MINUTE, 0);
                    eventCal.set(Calendar.SECOND, 0);

                    long diffMillis = eventCal.getTimeInMillis() - today.getTimeInMillis();
                    int diffDays = (int) (diffMillis / (24 * 60 * 60 * 1000));

                    if (diffDays >= 0 && diffDays <= 3) {
                        JSONArray dayEvents = events.getJSONArray(dateKey);
                        for (int i = 0; i < dayEvents.length(); i++) {
                            JSONObject event = dayEvents.getJSONObject(i);
                            String name = event.optString("name", "Event");
                            String type = event.optString("type", "");

                            String notifId = dateKey + "_" + name + "_" + todayStr;
                            if (!sent.contains(notifId)) {
                                String urgency = diffDays == 0 ? "היום!" : (diffDays == 1 ? "מחר" : "בעוד " + diffDays + " ימים");
                                String prefix = diffDays == 0 ? "דחוף! " : (diffDays == 1 ? "חשוב: " : "תזכורת: ");

                                showNotification(context, prefix + name, urgency + " - " + type);
                                sent.add(notifId);
                            }
                        }
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error processing date " + dateKey, e);
                }
            }

            prefs.edit().putStringSet("sent", sent).apply();
        } catch (Exception e) {
            Log.e(TAG, "Error processing events", e);
        }
    }

    private void showNotification(Context context, String title, String message) {
        try {
            Log.d(TAG, "Showing notification: " + title);

            // Create channel
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                NotificationChannel channel = new NotificationChannel(
                        CHANNEL_ID, "StudyHub", NotificationManager.IMPORTANCE_HIGH);
                channel.enableVibration(true);
                NotificationManager nm = context.getSystemService(NotificationManager.class);
                if (nm != null) nm.createNotificationChannel(channel);
            }

            // Check permission
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS)
                        != PackageManager.PERMISSION_GRANTED) {
                    Log.w(TAG, "No notification permission");
                    return;
                }
            }

            // Create intent to open app
            Intent intent = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName());
            PendingIntent pendingIntent = PendingIntent.getActivity(context, 0, intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

            NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
                    .setSmallIcon(R.mipmap.ic_launcher)
                    .setContentTitle(title)
                    .setContentText(message)
                    .setPriority(NotificationCompat.PRIORITY_HIGH)
                    .setAutoCancel(true)
                    .setContentIntent(pendingIntent)
                    .setDefaults(NotificationCompat.DEFAULT_ALL);

            NotificationManagerCompat.from(context).notify((int) System.currentTimeMillis(), builder.build());
            Log.d(TAG, "Notification sent: " + title);
        } catch (Exception e) {
            Log.e(TAG, "Error showing notification", e);
        }
    }
}
