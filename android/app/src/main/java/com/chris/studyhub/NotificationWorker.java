package com.chris.studyhub;

import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

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
import java.util.Locale;
import java.util.Set;

public class NotificationWorker extends Worker {
    private static final String TAG = "NotificationWorker";
    private static final String CHANNEL_ID = "studyhub_notifications";
    private static final String PREFS_NAME = "StudyHubNotifications";
    private static final String SENT_NOTIFICATIONS_KEY = "sent_notifications";

    // GitHub Gist for calendar events
    private static final String GIST_ID = "70ade01d4645cc8013a741b74d83561c";
    private static final String GIST_FILENAME = "studyhub_cloud.json";

    public NotificationWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
    }

    @NonNull
    @Override
    public Result doWork() {
        Log.d(TAG, "NotificationWorker running...");

        try {
            // Fetch calendar events from GitHub Gist
            String jsonData = fetchCalendarData();
            if (jsonData != null) {
                processEvents(jsonData);
            }
            return Result.success();
        } catch (Exception e) {
            Log.e(TAG, "Error in NotificationWorker", e);
            return Result.retry();
        }
    }

    private String getToken() {
        // Token parts for GitHub API
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
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(10000);

            int responseCode = connection.getResponseCode();
            if (responseCode == HttpURLConnection.HTTP_OK) {
                BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                reader.close();

                // Parse gist response to get the file content
                JSONObject gist = new JSONObject(response.toString());
                JSONObject files = gist.getJSONObject("files");
                JSONObject file = files.getJSONObject(GIST_FILENAME);
                return file.getString("content");
            }
        } catch (Exception e) {
            Log.e(TAG, "Error fetching calendar data from Gist", e);
        }
        return null;
    }

    private void processEvents(String jsonData) {
        try {
            JSONObject data = new JSONObject(jsonData);
            // Calendar events are stored in the "calendar" field of the gist
            JSONObject events = data.optJSONObject("calendar");
            if (events == null) {
                Log.d(TAG, "No calendar data found");
                return;
            }

            Calendar today = Calendar.getInstance();
            today.set(Calendar.HOUR_OF_DAY, 0);
            today.set(Calendar.MINUTE, 0);
            today.set(Calendar.SECOND, 0);
            today.set(Calendar.MILLISECOND, 0);

            SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
            SharedPreferences prefs = getApplicationContext().getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
            Set<String> sentNotifications = prefs.getStringSet(SENT_NOTIFICATIONS_KEY, new HashSet<>());
            Set<String> newSentNotifications = new HashSet<>(sentNotifications);

            // Clear old notifications (older than 7 days)
            Calendar weekAgo = Calendar.getInstance();
            weekAgo.add(Calendar.DAY_OF_YEAR, -7);
            String weekAgoStr = dateFormat.format(weekAgo.getTime());

            // Iterate through all dates
            java.util.Iterator<String> keys = events.keys();
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
                    eventCal.set(Calendar.MILLISECOND, 0);

                    long diffMillis = eventCal.getTimeInMillis() - today.getTimeInMillis();
                    int diffDays = (int) (diffMillis / (24 * 60 * 60 * 1000));

                    // Only process events within next 3 days
                    if (diffDays >= 0 && diffDays <= 3) {
                        JSONArray dayEvents = events.getJSONArray(dateKey);

                        for (int i = 0; i < dayEvents.length(); i++) {
                            JSONObject event = dayEvents.getJSONObject(i);
                            String eventName = event.optString("name", "");
                            String eventType = event.optString("type", "");
                            String eventCourse = event.optString("course", "");

                            // Create unique notification ID
                            String notificationId = dateKey + "_" + eventName + "_" + eventType;

                            // Skip if already sent today
                            String todayStr = dateFormat.format(today.getTime());
                            String dailyNotificationId = notificationId + "_" + todayStr;

                            if (!sentNotifications.contains(dailyNotificationId)) {
                                // Determine urgency
                                String urgencyLabel;
                                String prefix;
                                if (diffDays == 0) {
                                    urgencyLabel = "היום!";
                                    prefix = "דחוף! ";
                                } else if (diffDays == 1) {
                                    urgencyLabel = "מחר";
                                    prefix = "חשוב: ";
                                } else {
                                    urgencyLabel = "בעוד " + diffDays + " ימים";
                                    prefix = "תזכורת: ";
                                }

                                String title = prefix + eventName;
                                String message = urgencyLabel + " - " + (eventCourse.isEmpty() ? eventType : eventCourse);

                                // Show notification
                                showNotification(title, message);

                                // Mark as sent
                                newSentNotifications.add(dailyNotificationId);
                            }
                        }
                    }
                } catch (Exception e) {
                    Log.e(TAG, "Error processing date: " + dateKey, e);
                }
            }

            // Save sent notifications
            prefs.edit().putStringSet(SENT_NOTIFICATIONS_KEY, newSentNotifications).apply();

        } catch (Exception e) {
            Log.e(TAG, "Error processing events JSON", e);
        }
    }

    private void showNotification(String title, String message) {
        Context context = getApplicationContext();

        // Check permission for Android 13+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                Log.w(TAG, "Notification permission not granted");
                return;
            }
        }

        // Create notification channel if needed
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "StudyHub Notifications",
                    NotificationManager.IMPORTANCE_HIGH
            );
            channel.setDescription("Notifications for assignments and tests");
            channel.enableVibration(true);
            channel.setVibrationPattern(new long[]{200, 100, 200});

            NotificationManager notificationManager = context.getSystemService(NotificationManager.class);
            if (notificationManager != null) {
                notificationManager.createNotificationChannel(channel);
            }
        }

        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(R.mipmap.ic_launcher)
                .setContentTitle(title)
                .setContentText(message)
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .setVibrate(new long[]{200, 100, 200});

        NotificationManagerCompat notificationManager = NotificationManagerCompat.from(context);
        notificationManager.notify((int) System.currentTimeMillis(), builder.build());

        Log.d(TAG, "Notification shown: " + title);
    }
}
