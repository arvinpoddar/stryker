# Stryker
Stryker is an advanced foosball system that brings analytics real-time monitoring to any foosball table. It uses OpenCV for the ball tracking and Vue/Quasar for the game control web app.

To run the web app (built with Vue and Quasar) locally:

```bash
npm install
quasar dev
```

To run the computer vision Python script (afer installing all dependencies): 
```bash
python3 stryker.py
```

**Note:** The Python script requires a secondary webcam to be plugged into the computer.
