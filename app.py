from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client
import uuid
import os

# Get Supabase config from environment
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB limit

@app.route('/')
def index():
    resp = supabase.table("files").select("*").order("created_at", desc=True).execute()
    files = resp.data
    return render_template("index.html", files=files)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files.get('file')
        has_file = file and file.filename != ""
        filename = ""
        filepath = ""

        if has_file:
            filename = str(uuid.uuid4()) + "_" + file.filename
            supabase.storage().from_("uploads").upload(filename, file.stream.read())
            filepath = filename

        supabase.table("files").insert({
            "title": title,
            "description": description,
            "filename": file.filename if has_file else None,
            "filepath": filepath or None,
            "has_file": has_file,
            "likes": 0,
            "dislikes": 0
        }).execute()

        return redirect(url_for('index'))
    return render_template("upload.html")

@app.route('/like/<file_id>')
def like(file_id):
    supabase.rpc("increment_like", { "file_id_input": file_id }).execute()
    return redirect(url_for('index'))

@app.route('/dislike/<file_id>')
def dislike(file_id):
    supabase.rpc("increment_dislike", { "file_id_input": file_id }).execute()
    return redirect(url_for('index'))

@app.route('/download/<path:filepath>')
def download(filepath):
    public = supabase.storage().from_("uploads").get_public_url(filepath)
    return redirect(public['publicUrl'])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
