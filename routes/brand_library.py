import base64
from flask import Blueprint, abort, redirect, render_template, request, session, url_for, Response
from database.profiles import _connect, USE_POSTGRES
from routes.auth import login_required

brand_library_bp = Blueprint("brand_library", __name__)
ALLOWED = {"image/jpeg", "image/png", "image/webp"}

def _init():
    conn=_connect(); cur=conn.cursor(); ident="BIGSERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    cur.execute(f"""CREATE TABLE IF NOT EXISTS brand_media(id {ident},user_id INTEGER NOT NULL,name TEXT NOT NULL,mime TEXT NOT NULL,data TEXT NOT NULL,kind TEXT DEFAULT 'photo',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit(); conn.close()

def media_for_user(user_id):
    _init(); conn=_connect(); cur=conn.cursor(); cur.execute("SELECT id,name,mime,kind,created_at FROM brand_media WHERE user_id=? ORDER BY id DESC",(user_id,)); rows=cur.fetchall(); conn.close(); return rows

def save_files(user_id, files, kind="photo"):
    _init(); saved=[]; conn=_connect(); cur=conn.cursor()
    try:
        for file in list(files)[:20]:
            raw=file.read()
            if not raw or file.mimetype not in ALLOWED or len(raw)>6*1024*1024: continue
            sql="INSERT INTO brand_media(user_id,name,mime,data,kind) VALUES(?,?,?,?,?)"
            if USE_POSTGRES: sql += " RETURNING id"
            cur.execute(sql,(user_id,file.filename[:180],file.mimetype,base64.b64encode(raw).decode("ascii"),kind))
            saved.append((cur.fetchone()[0] if USE_POSTGRES else cur.lastrowid,file.filename[:180]))
        conn.commit(); return saved
    finally: conn.close()

@brand_library_bp.route("/brand-library", methods=["GET","POST"])
@login_required
def library():
    _init(); error=""
    if request.method=="POST":
        files=request.files.getlist("brand_media"); kind=request.form.get("kind","photo")
        save_files(session["user_id"],files,kind)
        return redirect(url_for("brand_library.library"))
    return render_template("brand_library.html", media=media_for_user(session["user_id"]), error=error)

@brand_library_bp.route("/brand-media/<int:media_id>")
@login_required
def media(media_id):
    _init(); conn=_connect(); cur=conn.cursor(); cur.execute("SELECT mime,data FROM brand_media WHERE id=? AND user_id=?",(media_id,session["user_id"])); row=cur.fetchone(); conn.close()
    if not row: abort(404)
    return Response(base64.b64decode(row[1]),mimetype=row[0],headers={"Cache-Control":"private, max-age=3600"})

@brand_library_bp.post("/brand-media/<int:media_id>/delete")
@login_required
def delete(media_id):
    conn=_connect(); cur=conn.cursor(); cur.execute("DELETE FROM brand_media WHERE id=? AND user_id=?",(media_id,session["user_id"])); conn.commit(); conn.close(); return redirect(url_for("brand_library.library"))
