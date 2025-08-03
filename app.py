from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client
import uuid, os, time

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Store last upload time per IP
last_upload_time = {}

COOLDOWN_SECONDS = 120  # 2 minutes

def get_client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

@app.route('/')
def index():
    search = request.args.get("search", "").strip()
    query = supabase.table("listings").select("*").order("inserted_at", desc=True)

    if search:
        query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")

    result = query.execute()
    return render_template("index.html", listings=result.data, search=search)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    ip = get_client_ip()

    if request.method == 'POST':
        now = time.time()
        last_time = last_upload_time.get(ip, 0)
        if now - last_time < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_time))
            return f"<script>alert('Please wait {remaining} seconds before uploading again.'); window.location='/upload'</script>"

        data = {
            "id": str(uuid.uuid4()),
            "name": request.form["name"],
            "description": request.form["description"],
            "file_link": request.form["file_link"]
        }
        supabase.table("listings").insert(data).execute()

        # Update last upload time
        last_upload_time[ip] = now

        return redirect(url_for("index"))

    return render_template("upload.html")

@app.route('/download/<string:listing_id>')
def download(listing_id):
    listing = supabase.table("listings").select("*").eq("id", listing_id).single().execute().data
    if listing["file_link"] and listing["file_link"].startswith("http"):
        return redirect(listing["file_link"])
    return "<script>alert('Does not have any downloadable files!'); window.location='/'</script>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
