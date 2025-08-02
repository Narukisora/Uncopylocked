from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client
import uuid, os

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    search = request.args.get("search", "").strip()
    query = supabase.table("listings").select("*").order("inserted_at", desc=True)

    if search:
        # Use OR condition between name and description
        query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")

    result = query.execute()
    return render_template("index.html", listings=result.data, search=search)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        data = {
            "id": str(uuid.uuid4()),
            "name": request.form["name"],
            "description": request.form["description"],
            "file_link": request.form["file_link"]
        }
        supabase.table("listings").insert(data).execute()
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
    
