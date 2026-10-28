import os
import re
import tempfile
from flask import Flask, request, render_template_string, send_file, flash, redirect, url_for
import yt_dlp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>YouTube to MP3</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f6fb;color:#172033;font-family:Arial,sans-serif}
main{max-width:680px;margin:8vh auto;padding:28px}
.panel{background:white;border:1px solid #e4e8f0;border-radius:18px;padding:28px;box-shadow:0 12px 40px #18254412}
h1{margin:0 0 8px;font-size:30px}p{line-height:1.55;color:#5a6475}
label{display:block;font-weight:700;margin:18px 0 8px}
input,select{width:100%;padding:13px 14px;border:1px solid #ccd3df;border-radius:10px;font-size:16px;background:white}
button{width:100%;margin-top:20px;padding:14px;border:0;border-radius:10px;background:#2457d6;color:white;font-size:16px;font-weight:700;cursor:pointer}
button:hover{background:#1746bc}.note{font-size:13px;color:#697386;margin-top:16px}
.alert{background:#fff0f0;border:1px solid #ffd0d0;color:#8b2020;padding:12px;border-radius:9px;margin:14px 0}
</style>
</head>
<body><main><section class="panel">
<h1>YouTube to MP3</h1>
<p>Paste a YouTube link, choose an MP3 bitrate, and create an audio file.</p>
{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="alert">{{ message }}</div>{% endfor %}{% endwith %}
<form method="post" action="/download">
<label for="url">YouTube URL</label>
<input id="url" name="url" type="url" placeholder="https://www.youtube.com/watch?v=..." required>
<label for="bitrate">MP3 quality</label>
<select id="bitrate" name="bitrate">
<option value="128">128 kbps — smaller file</option>
<option value="256" selected>256 kbps — balanced</option>
<option value="320">320 kbps — highest MP3 bitrate</option>
</select>
<button type="submit">Convert and download MP3</button>
</form>
<p class="note">Use only for videos you own or have permission to download. Long conversions may exceed the limits of free hosting. Do not submit private or sensitive links.</p>
</section></main></body></html>
"""

def valid_youtube_url(url):
    # Allow standard YouTube watch, short, and youtu.be URLs only.
    return bool(re.match(r"^https?://(www\\.)?(youtube\\.com|m\\.youtube\\.com|youtu\\.be)/", url.strip(), re.I))

@app.get("/")
def index():
    return render_template_string(PAGE)

@app.post("/download")
def download():
    url = request.form.get("url", "").strip()
    bitrate = request.form.get("bitrate", "256")
    if not valid_youtube_url(url):
        flash("Please enter a valid YouTube URL.")
        return redirect(url_for("index"))
    if bitrate not in {"128", "256", "320"}:
        bitrate = "256"

    tempdir = tempfile.mkdtemp(prefix="ytmp3_")
    output_template = os.path.join(tempdir, "%(title).120s.%(ext)s")
    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "max_filesize": 1024 * 1024 * 1024,  # 1 GB safety ceiling
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": bitrate,
        }],
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        candidates = [os.path.join(tempdir, f) for f in os.listdir(tempdir) if f.lower().endswith(".mp3")]
        if not candidates:
            flash("Conversion did not produce an MP3. Try another video.")
            return redirect(url_for("index"))
        path = candidates[0]
        return send_file(path, as_attachment=True, download_name=os.path.basename(path), mimetype="audio/mpeg")
    except Exception:
        flash("Download or conversion failed. The video may be unavailable, restricted, too large, or the host may have timed out.")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
