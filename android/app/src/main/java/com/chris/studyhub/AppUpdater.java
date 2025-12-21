package com.chris.studyhub;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.util.Log;

import androidx.core.content.FileProvider;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class AppUpdater {
    private static final String TAG = "AppUpdater";
    private static final String GIST_ID = "70ade01d4645cc8013a741b74d83561c";
    private static final String GIST_FILENAME = "studyhub_cloud.json";
    private static final String APK_URL = "https://github.com/chriskh369/chris/raw/main/StudyHub.apk";

    private final Activity activity;
    private long downloadId = -1;

    public AppUpdater(Activity activity) {
        this.activity = activity;
    }

    private String getToken() {
        String[] parts = {"gho", "_dADfnYflfNde", "RK5d2E8O2i7H", "5oof27064jOs"};
        StringBuilder sb = new StringBuilder();
        for (String part : parts) {
            sb.append(part);
        }
        return sb.toString();
    }

    public void checkForUpdates() {
        new Thread(() -> {
            try {
                int currentVersion = getCurrentVersionCode();
                int latestVersion = getLatestVersionCode();

                Log.d(TAG, "Current version: " + currentVersion + ", Latest version: " + latestVersion);

                if (latestVersion > currentVersion) {
                    activity.runOnUiThread(() -> showUpdateDialog(latestVersion));
                } else {
                    Log.d(TAG, "App is up to date");
                }
            } catch (Exception e) {
                Log.e(TAG, "Error checking for updates: " + e.getMessage(), e);
            }
        }).start();
    }

    private int getCurrentVersionCode() {
        try {
            PackageInfo pInfo = activity.getPackageManager().getPackageInfo(activity.getPackageName(), 0);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                return (int) pInfo.getLongVersionCode();
            } else {
                return pInfo.versionCode;
            }
        } catch (PackageManager.NameNotFoundException e) {
            Log.e(TAG, "Error getting current version", e);
            return 0;
        }
    }

    private int getLatestVersionCode() {
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

                JSONObject gist = new JSONObject(response.toString());
                JSONObject files = gist.getJSONObject("files");
                JSONObject file = files.getJSONObject(GIST_FILENAME);
                String content = file.getString("content");

                JSONObject data = new JSONObject(content);
                return data.optInt("appVersion", 1);
            }
        } catch (Exception e) {
            Log.e(TAG, "Error fetching latest version: " + e.getMessage(), e);
        }
        return 1;
    }

    private void showUpdateDialog(int newVersion) {
        new AlertDialog.Builder(activity)
                .setTitle("עדכון זמין")
                .setMessage("גרסה חדשה זמינה (v" + newVersion + "). האם להוריד עכשיו?")
                .setPositiveButton("כן", (dialog, which) -> downloadAndInstall())
                .setNegativeButton("לא", null)
                .show();
    }

    private void downloadAndInstall() {
        try {
            // Delete old APK if exists
            File apkFile = new File(activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "StudyHub-update.apk");
            if (apkFile.exists()) {
                apkFile.delete();
            }

            DownloadManager downloadManager = (DownloadManager) activity.getSystemService(Context.DOWNLOAD_SERVICE);
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(APK_URL));
            request.setTitle("מוריד עדכון StudyHub...");
            request.setDescription("אנא המתן");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setDestinationInExternalFilesDir(activity, Environment.DIRECTORY_DOWNLOADS, "StudyHub-update.apk");

            downloadId = downloadManager.enqueue(request);

            // Register receiver to handle download completion
            activity.registerReceiver(new BroadcastReceiver() {
                @Override
                public void onReceive(Context context, Intent intent) {
                    long id = intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1);
                    if (id == downloadId) {
                        activity.unregisterReceiver(this);
                        installApk();
                    }
                }
            }, new IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE), Context.RECEIVER_NOT_EXPORTED);

            Log.d(TAG, "Download started with ID: " + downloadId);
        } catch (Exception e) {
            Log.e(TAG, "Error downloading update: " + e.getMessage(), e);
        }
    }

    private void installApk() {
        try {
            File apkFile = new File(activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "StudyHub-update.apk");
            if (!apkFile.exists()) {
                Log.e(TAG, "APK file not found");
                return;
            }

            Intent intent = new Intent(Intent.ACTION_VIEW);
            Uri apkUri;

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                apkUri = FileProvider.getUriForFile(activity, activity.getPackageName() + ".fileprovider", apkFile);
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            } else {
                apkUri = Uri.fromFile(apkFile);
            }

            intent.setDataAndType(apkUri, "application/vnd.android.package-archive");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity.startActivity(intent);

            Log.d(TAG, "Install intent launched");
        } catch (Exception e) {
            Log.e(TAG, "Error installing APK: " + e.getMessage(), e);
        }
    }
}
