---
title: "Hello World Window"
type: completion
generation: ["bbj-gui", "dwc"]
difficulty: basic
tags: [gui, window, sysgui, hello-world]
description: "Create and display a basic BBj window"
---

## Code

```bbj
REM Hello World Window - Modern BBj
sysgui! = BBjAPI().getSysGui()
window! = sysgui!.addWindow(100, 100, 400, 300, "Hello World")
window!.setCallback(window!.ON_CLOSE, "handleClose")

process_events

handleClose:
    release
```

## Expected Behavior

A 400x300 pixel window appears at screen position (100,100) with the title "Hello World". The window remains open until the user closes it, at which point the program terminates cleanly.

## Explanation

This is the minimal BBj GUI application:

1. **Get GUI manager**: `BBjAPI().getSysGui()` returns the system GUI interface. This is the entry point for all GUI operations in BBj.

2. **Create window**: `addWindow(x, y, width, height, title)` creates a top-level window at the specified screen position and size. The title appears in the window's title bar.

3. **Handle close event**: `setCallback()` connects the window's close event (`ON_CLOSE`) to a label (`handleClose`). This ensures the program responds when the user clicks the close button.

4. **Event loop**: `process_events` starts the BBj event processing loop. The program waits here, processing user interactions until explicitly terminated.

5. **Cleanup**: The `handleClose` label contains `release`, which frees all resources and exits the program cleanly.

This pattern works identically in both BBj GUI (native Java) and DWC (browser) environments because both use the same BBjAPI interface.
