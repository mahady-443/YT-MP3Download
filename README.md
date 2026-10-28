# YouTube to MP3 Web App

A small Flask web app with 128, 256, and 320 kbps MP3 options.

## Deploy on Render

1. Upload all files in this folder to your GitHub repository.
2. In Render, choose **New + → Web Service** and select this repository.
3. Select **Docker** as the runtime/environment if asked.
4. Choose a plan and click **Create Web Service**.
5. Open the public `onrender.com` URL when the build finishes.

The Dockerfile installs FFmpeg and starts the Flask app with Gunicorn.

## Important limitations

- Only use this app for content you own or are authorized to download.
- Free hosting is not reliable for very long conversions (including 8-hour videos); jobs may time out, memory/disk limits may be reached, and temporary files are not persistent.
- This basic demo is not designed for public high-traffic use. Do not share it widely without adding access controls and abuse protections.
