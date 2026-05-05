**NOVASPHERE – Development Notes (Monitoring System – Version 1)**

In version 1, I focused on building the basic file monitoring system. My main goal was to make the system detect file activities in real time. I implemented functionality to monitor events such as file creation, deletion, modification, and renaming within a selected directory.

Initially, I tested the system by printing the detected events to the console to confirm that the monitoring was working correctly. During testing, I noticed that the system was capturing a large number of file changes, especially from background processes and development tools. This helped me understand that real-time monitoring can generate a lot of noise.

At this stage, the system successfully detects file activity, but it does not yet differentiate between normal and suspicious behavior. Version 1 mainly serves as the foundation for the system, where the focus is on accurate event detection rather than analysis.

This version will be further improved in the next stage by adding filtering, structured logging, and behavior-based detection.
