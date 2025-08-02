from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client
import uuid, os

app = Flask(__name__)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr)

@app.route('/')
def index():
    search = request.args.get("search", "")
    query = supabase.table("listings").select("*")

    if search:
        query = query.ilike("name", f"%{search}%").ilike("description", f"%{search}%")

    result = query.order("likes", desc=True).execute()
    return render_template("index.html", listings=result.data, search=search)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        data = {
            "id": str(uuid.uuid4()),
            "name": request.form["name"],
            "description": request.form["description"],
            "file_link": request.form["file_link"],
            "likes": 0,
            "dislikes": 0
        }
        supabase.table("listings").insert(data).execute()
        return redirect(url_for("index"))
    return render_template("upload.html")

@app.route('/vote/<string:listing_id>/<string:action>')
def vote(listing_id, action):
    if action not in ['like', 'dislike']:
        return redirect(url_for("index"))

    ip = get_user_ip()
    vote_table = supabase.table("votes")
    listing_table = supabase.table("listings")

    # Step 1: Get current vote (if exists)
    vote_result = vote_table.select("*").eq("user_ip", ip).eq("listing_id", listing_id).execute()
    existing_votes = vote_result.data
    current_vote = existing_votes[0] if existing_votes else None

    # Step 2: Get listing
    listing_result = listing_table.select("*").eq("id", listing_id).execute()
    if not listing_result.data:
        return "<h2>Listing not found</h2>"

    listing = listing_result.data[0]

    if current_vote:
        # User already voted
        if current_vote["action"] == action:
            # Same vote again → do nothing
            return redirect(url_for("index"))

        # Switch vote
        vote_table.update({"action": action}).eq("id", current_vote["id"]).execute()

        if action == "like":
            listing_table.update({
                "likes": listing["likes"] + 1,
                "dislikes": max(listing["dislikes"] - 1, 0)
            }).eq("id", listing_id).execute()
        else:
            listing_table.update({
                "likes": max(listing["likes"] - 1, 0),
                "dislikes": listing["dislikes"] + 1
            }).eq("id", listing_id).execute()

    else:
        # First time voting
        vote_table.insert({
            "id": str(uuid.uuid4()),
            "user_ip": ip,
            "listing_id": listing_id,
            "action": action
        }).execute()

        if action == "like":
            listing_table.update({"likes": listing["likes"] + 1}).eq("id", listing_id).execute()
        else:
            listing_table.update({"dislikes": listing["dislikes"] + 1}).eq("id", listing_id).execute()

    return redirect(url_for("index"))

@app.route('/download/<string:listing_id>')
def download(listing_id):
    listing = supabase.table("listings").select("*").eq("id", listing_id).single().execute().data
    if listing["file_link"] and listing["file_link"].startswith("http"):
        return redirect(listing["file_link"])
    return "<script>alert('Does not have any downloadable files!'); window.location='/'</script>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
    
