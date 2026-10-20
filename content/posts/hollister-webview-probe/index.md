---
date: "2026-10-20T00:00:00+02:00"
draft: false
title: "Hollister WebView probe"
---

[Open the Hollister WebView probe](/bug-bounty/hollister-webview-probe.html).

This test page shows the page origin, user agent, and whether an Android bridge is present. It requests location only when you press the button, and displays the result on the page.

Use an emulator with a synthetic location. Record whether the page opens inside Hollister or in a separate browser, the app's Android permissions, and any website permission prompt.
