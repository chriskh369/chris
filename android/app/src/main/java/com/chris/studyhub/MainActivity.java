package com.chris.studyhub;

import android.os.Bundle;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Disable cache to always get fresh content
        WebView webView = getBridge().getWebView();
        webView.getSettings().setCacheMode(android.webkit.WebSettings.LOAD_NO_CACHE);
    }
}
