from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client
import os, uuid

# Load from environment variables or hardcode (not recommended for production)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "your-anon-or-service-role-key")

# Supabase client setup
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Flask app
app = Flask(__name__)

@app.route('/')
def index():
    result = supabase.table("listings").select("*").execute()
    listings = result.data
    return render_template("index.html", listings=listings)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        name = request.form.get("name")
        description = request.form.get("description")
        file_link = request.form.get("file_link")

        supabase.table("listings").insert({
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "file_link": file_link,
            "likes": 0,
            "dislikes": 0
        }).execute()

        return redirect(url_for("index"))

    return render_template("upload.html")

@app.route('/like/<string:listing_id>')
def like(listing_id):
    listing = supabase.table("listings").select("*").eq("id", listing_id).single().execute().data
    new_likes = listing["likes"] + 1
    supabase.table("listings").update({"likes": new_likes}).eq("id", listing_id).execute()
    return redirect(url_for("index"))

@app.route('/dislike/<string:listing_id>')
def dislike(listing_id):
    listing = supabase.table("listings").select("*").eq("id", listing_id).single().execute().data
    new_dislikes = listing["dislikes"] + 1
    supabase.table("listings").update({"dislikes": new_dislikes}).eq("id", listing_id).execute()
    return redirect(url_for("index"))

@app.route('/download/<string:listing_id>')
def download(listing_id):
    listing = supabase.table("listings").select("*").eq("id", listing_id).single().execute().data
    link = listing["file_link"]
    if link and link.startswith("http"):
        return redirect(link)
    return "<script>alert('Does not have any downloadable files!'); window.location='/'</script>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
    
