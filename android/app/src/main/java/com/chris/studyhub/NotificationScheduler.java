package com.chris.studyhub;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;

public class NotificationScheduler {
    private static final String TAG = "NotificationScheduler";
    private static final int ALARM_REQUEST_CODE = 12345;
    private static final long INTERVAL_MS = 15 * 60 * 1000; // 15 minutes

    public static void scheduleNextAlarm(Context context) {
        try {
            AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
            if (alarmManager == null) {
                Log.e(TAG, "AlarmManager is null");
                return;
            }

            Intent intent = new Intent(context, NotificationReceiver.class);
            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                    context,
                    ALARM_REQUEST_CODE,
                    intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            );

            long triggerTime = System.currentTimeMillis() + INTERVAL_MS;

            // Use setExactAndAllowWhileIdle for reliable delivery even in Doze mode
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent);
            } else {
                alarmManager.setExact(AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent);
            }

            Log.d(TAG, "Next alarm scheduled for " + new java.util.Date(triggerTime));
        } catch (Exception e) {
            Log.e(TAG, "Error scheduling alarm: " + e.getMessage(), e);
        }
    }

    public static void scheduleImmediate(Context context) {
        try {
            AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
            if (alarmManager == null) return;

            Intent intent = new Intent(context, NotificationReceiver.class);
            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                    context,
                    ALARM_REQUEST_CODE + 1, // Different request code for immediate
                    intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            );

            // Trigger in 5 seconds
            long triggerTime = System.currentTimeMillis() + 5000;

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent);
            } else {
                alarmManager.setExact(AlarmManager.RTC_WAKEUP, triggerTime, pendingIntent);
            }

            Log.d(TAG, "Immediate alarm scheduled for 5 seconds from now");
        } catch (Exception e) {
            Log.e(TAG, "Error scheduling immediate alarm: " + e.getMessage(), e);
        }
    }

    public static void cancelAlarms(Context context) {
        try {
            AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
            if (alarmManager == null) return;

            Intent intent = new Intent(context, NotificationReceiver.class);
            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                    context,
                    ALARM_REQUEST_CODE,
                    intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            );

            alarmManager.cancel(pendingIntent);
            Log.d(TAG, "Alarms cancelled");
        } catch (Exception e) {
            Log.e(TAG, "Error cancelling alarms: " + e.getMessage(), e);
        }
    }
}
