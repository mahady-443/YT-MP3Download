
import os
import tempfile
from urllib.parse import urlparse

from flask import (
    Flask,
    request,
    render_template_string,
    send_file,
    flash,
    redirect,
    url_for,
)
import yt_dlp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")


PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>YouTube to MP3 Converter</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    padding: 20px;
    background: #f4f6fb;
    color: #172033;
    font-family: Arial, sans-serif;
}

main {
    max-width: 680px;
    margin: 8vh auto;
}

.panel {
    background: white;
    border: 1px solid #e4e8f0;
    border-radius: 18px;
    padding: 28px;
    box-shadow: 0 12px 40px #18254412;
}

h1 {
    margin: 0 0 8px;
    font-size: 30px;
}

p {
    line-height: 1.55;
    color: #5a6475;
}

label {
    display: block;
    font-weight: 700;
    margin: 18px 0 8px;
}

input, select {
    width: 100%;
    padding: 13px 14px;
    border: 1px solid #ccd3df;
    border-radius: 10px;
    font-size: 16px;
    background: white;
}

button {
    width: 100%;
    margin-top: 20px;
    padding: 14px;
    border: 0;
    border-radius: 10px;
    background: #2457d6;
    color: white;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
}

button:hover {
    background: #1746bc;
}

.note {
    font-size: 13px;
    color: #697386;
    margin-top: 16px;
}

.alert {
    background: #fff0f0;
    border: 1px solid #ffd0d0;
    color: #8b2020;
    padding: 12px;
    border-radius: 9px;
    margin: 14px 0;
}
</style>
</head>

<body>
<main>
<section class="panel">

<h1>YouTube to MP3</h1>

<p>
Paste a YouTube link, choose your MP3 quality,
and create an audio file.
</p>

{% with messages = get_flashed_messages() %}
    {% for message in messages %}
        <div class="alert">{{ message }}</div>
    {% endfor %}
{% endwith %}

<form method="post" action="/download">

<label for="url">YouTube URL</label>

<input
    id="url"
    name="url"
    type="text"
    placeholder="https://youtu.be/VIDEO_ID"
    autocomplete="url"
    required
>

<label for="bitrate">MP3 quality</label>

<select id="bitrate" name="bitrate">
    <option value="128">128 kbps — smaller file</option>
    <option value="256" selected>256 kbps — balanced</option>
    <option value="320">320 kbps — highest MP3 bitrate</option>
</select>

<button type="submit">Convert and download MP3</button>

</form>

<p class="note">
Use only for content you own or are authorized to download.
Long conversions may exceed free hosting limits.
</p>

</section>
</main>
</body>
</html>
"""


def valid_youtube_url(url):
    try:
        parsed = urlparse(url.strip())

        allowed_hosts = {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
            "www.youtu.be",
        }

        return (
            parsed.scheme in ("http", "https")
            and parsed.hostname is not None
            and parsed.hostname.lower() in allowed_hosts
            and bool(parsed.path)
        )

    except (ValueError, AttributeError):
        return False


@app.get("/")
def index():
    return render_template_string(PAGE)


@app.post("/download")
def download():
    url = request.form.get("url", "").strip()
    bitrate = request.form.get("bitrate", "256")

    if not valid_youtube_url(url):
        flash(
            "Invalid YouTube URL. Paste a complete link such as "
            "https://youtu.be/VIDEO_ID"
        )
        return redirect(url_for("index"))

    if bitrate not in {"128", "256", "320"}:
        bitrate = "256"

    tempdir = tempfile.mkdtemp(prefix="ytmp3_")
    output_template = os.path.join(
        tempdir, "%(title).120s.%(ext)s"
    )

    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "max_filesize": 1024 * 1024 * 1024,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        candidates = [
            os.path.join(tempdir, filename)
            for filename in os.listdir(tempdir)
            if filename.lower().endswith(".mp3")
        ]

        if not candidates:
            flash(
                "No MP3 file was created. The video may be "
                "unavailable or conversion may have failed."
            )
            return redirect(url_for("index"))

        path = candidates[0]

        return send_file(
            path,
            as_attachment=True,
            download_name=os.path.basename(path),
            mimetype="audio/mpeg",
        )

    except Exception:
        app.logger.exception("YouTube audio conversion failed")

        flash(
            "Conversion failed. Check the Render logs for details. "
            "The video may be restricted, or the server may have "
            "reached its processing limits."
        )

        return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000")),
    )
