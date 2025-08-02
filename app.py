from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not found in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

@app.route('/')
def index():
    resp = supabase.table("files").select("*").order("created_at", desc=True).execute()
    files = resp.data
    return render_template("index.html", files=files)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            download_link = request.form.get('download_link', '').strip()

            if not title or not description:
                return "Title and description are required.", 400

            has_download = bool(download_link)

            data = {
                "title": title,
                "description": description,
                "download_link": download_link if has_download else None,
                "has_download": has_download,
                "likes": 0,
                "dislikes": 0
            }

            response = supabase.table("files").insert(data).execute()

            if response.error:
                return f"Error uploading: {response.error.message}", 500

            return redirect(url_for('index'))

        except Exception as e:
            return f"An error occurred: {str(e)}", 500

    return render_template("upload.html")

@app.route('/download/<int:file_id>')
def download(file_id):
    result = supabase.table("files").select("*").eq("id", file_id).single().execute()
    file = result.data

    if file and file.get("has_download") and file.get("download_link"):
        return redirect(file["download_link"])
    else:
        return """
        <script>
            alert("This listing does not have any downloadable files!");
            window.location.href = "/";
        </script>
        """

@app.route('/like/<file_id>')
def like(file_id):
    supabase.rpc("increment_like", { "file_id_input": file_id }).execute()
    return redirect(url_for('index'))

@app.route('/dislike/<file_id>')
def dislike(file_id):
    supabase.rpc("increment_dislike", { "file_id_input": file_id }).execute()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
    
