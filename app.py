import os
from datetime import datetime
import re

try:
    import requests
except ImportError:
    requests = None

from flask import (
    Flask,
    request,
    render_template_string,
    redirect,
    url_for,
    flash,
    jsonify,
)
from dotenv import load_dotenv
from openai import OpenAI
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# ============================================
# Setup
# ============================================

load_dotenv()

client = OpenAI()
db = SQLAlchemy()

COMMON_VECTOR_STORE_ID = os.getenv("WINK_VECTOR_STORE_ID")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///wink.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

UPLOAD_DIR = os.path.join(app.root_path, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================
# Database models
# ============================================

class Instructor(db.Model):
    __tablename__ = "instructors"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    slug = db.Column(db.String(64), unique=True, nullable=True)
    personal_vector_store_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InstructorFile(db.Model):
    __tablename__ = "instructors_files"

    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey("instructors.id"), nullable=False)
    file_id = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    instructor = db.relationship("Instructor", backref="files")


with app.app_context():
    db.create_all()

# ============================================
# Vector store helpers
# ============================================

def _require_requests():
    if requests is None:
        raise RuntimeError("requests library required")

def create_vector_store_http(name: str) -> str:
    _require_requests()
    resp = requests.post(
        f"{OPENAI_BASE_URL}/v1/vector_stores",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2",
        },
        json={"name": name},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]

# ============================================
# Templates
# ============================================

TEMPLATE_LOGIN_PAGE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>WINK Instructor Access</title>
<style>
body{
  margin:0;
  font-family:system-ui;
  background:radial-gradient(circle at top left,#0b1120,#020617);
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
}
.card{
  width:100%;
  max-width:520px;
  background:#fff;
  border-radius:26px;
  box-shadow:0 28px 70px rgba(15,23,42,0.45);
}
.header{
  padding:20px;
  background:linear-gradient(135deg,#041e42,#1d4ed8,#f97316);
  color:#fff;
  text-align:center;
}
.body{padding:22px;text-align:center;}
.avatar{
  width:140px;height:140px;margin:0 auto 14px;border-radius:50%;overflow:hidden;
}
input{
  width:100%;
  padding:14px;
  border-radius:16px;
  border:1px solid #cbd5e1;
  font-size:15px;
}
button{
  margin-top:18px;
  padding:14px 20px;
  border:none;
  border-radius:16px;
  font-size:15px;
  font-weight:700;
  color:#fff;
  background:linear-gradient(135deg,#f97316,#1d4ed8);
  cursor:pointer;
}
.hint{margin-top:10px;font-size:13px;color:#475569;}
.flash{
  margin:14px 0 0;
  font-size:13px;
  color:#b91c1c;
}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>WINK Instructor Access</h1>
    <p>Manage your course materials</p>
  </div>
  <div class="body">
    <div class="avatar">
      <img src="/static/wink.jpeg" style="width:100%;height:100%;object-fit:cover;">
    </div>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="flash">{{ messages[0] }}</div>
      {% endif %}
    {% endwith %}

    <form method="post">
      <input type="email" name="email" required placeholder="you@utep.edu">
      <div class="hint">
        Existing instructors go to file management.
        New instructors are guided to create their WINK page.
      </div>
      <button type="submit">Continue</button>
    </form>
  </div>
</div>
</body>
</html>
"""

TEMPLATE_NEW_INSTRUCTOR = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>New Instructor Setup</title>
<style>
body{
  margin:0;
  font-family:system-ui;
  background:radial-gradient(circle at top left,#0b1120,#020617);
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
}
.card{
  width:100%;
  max-width:640px;
  background:#fff;
  border-radius:26px;
  box-shadow:0 28px 70px rgba(15,23,42,0.45);
}
.header{
  padding:20px;
  background:linear-gradient(135deg,#041e42,#1d4ed8,#f97316);
  color:#fff;
}
.body{padding:22px;}
label{
  display:block;
  margin:14px 0 8px;
  font-size:13px;
  color:#334155;
  font-weight:700;
}
input{
  width:100%;
  padding:14px;
  border-radius:16px;
  border:1px solid #cbd5e1;
  font-size:15px;
}
.help{
  margin-top:8px;
  font-size:13px;
  color:#475569;
}
.actions{
  margin-top:18px;
}
button{
  padding:14px 18px;
  border-radius:16px;
  border:none;
  font-weight:700;
  color:#fff;
  background:linear-gradient(135deg,#f97316,#1d4ed8);
}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h2>New Instructor Setup</h2>
    <div>Create your WINK page</div>
  </div>
  <div class="body">
    <form method="post">
      <input type="hidden" name="email" value="{{ email }}">
      <label>Name students will see</label>
      <input name="name" required placeholder="Dr. Trevino">
      <div class="actions">
        <button type="submit">Create my WINK page</button>
      </div>
    </form>
  </div>
</div>
</body>
</html>
"""

TEMPLATE_MANAGE_FILES = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Manage Files</title>
<style>
body{
  margin:0;
  font-family:system-ui;
  background:radial-gradient(circle at top left,#0b1120,#020617);
  min-height:100vh;
  display:flex;
  justify-content:center;
  padding:20px;
}
.card{
  width:100%;
  max-width:980px;
  background:#fff;
  border-radius:26px;
  box-shadow:0 28px 70px rgba(15,23,42,0.45);
}
.header{
  padding:20px;
  background:linear-gradient(135deg,#041e42,#1d4ed8,#f97316);
  color:#fff;
}
.header a{
  color:#fff;
  text-decoration:none;
  font-weight:800;
}
.body{padding:22px;}
.upload-box{
  border:2px dashed #cbd5e1;
  border-radius:18px;
  padding:18px;
  text-align:center;
  background:#fff;
}
table{
  width:100%;
  border-collapse:collapse;
  margin-top:20px;
}
th,td{
  padding:12px;
  border-bottom:1px solid #e2e8f0;
  text-align:left;
}
button{
  padding:12px 16px;
  border-radius:14px;
  border:none;
  background:linear-gradient(135deg,#f97316,#1d4ed8);
  color:#fff;
  font-weight:800;
}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-size:18px;font-weight:900;">{{ instructor.name or instructor.email }}</div>
        <div>Manage your WINK files</div>
      </div>
      <div>
        <a href="/wink/{{ instructor.slug }}">Open WINK Chat</a>
      </div>
    </div>
  </div>
  <div class="body">
    <div style="margin-bottom:12px;font-size:13px;">
      Vector Store ID: {{ instructor.personal_vector_store_id }}
    </div>
    <form method="post" enctype="multipart/form-data" class="upload-box">
      <input type="file" name="files" multiple required>
      <div style="margin-top:12px;">
        <button type="submit" name="action" value="upload">Upload to WINK</button>
      </div>
    </form>
  </div>
</div>
</body>
</html>
"""

TEMPLATE_WINK_CHAT = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>WINK</title>
<style>
body{margin:0;font-family:system-ui;background:#020617;}
.wrapper{display:grid;grid-template-columns:420px 1fr;min-height:100vh;}
.left{background:linear-gradient(180deg,#041e42,#020617);color:#fff;padding:26px;}
.right{background:#f8fafc;padding:24px;}
.chat-body{height:500px;overflow-y:auto;background:#f1f5f9;padding:20px;}
.chat-input{display:flex;gap:10px;}
.chat-input input{flex:1;padding:14px;border-radius:16px;border:1px solid #cbd5e1;}
.chat-input button{padding:14px 18px;border-radius:16px;border:none;font-weight:700;color:#fff;background:linear-gradient(135deg,#f97316,#1d4ed8);}
.msg{margin-bottom:12px;}
.msg.user{text-align:right;}
.bubble{display:inline-block;padding:12px 14px;border-radius:16px;background:#e2e8f0;}
.msg.user .bubble{background:#c7d2fe;}
</style>
</head>
<body>
<div class="wrapper">
  <div class="left">
    <h2>ENTERING STUDENT EXPERIENCES</h2>
    <img src="/static/wink.jpeg" style="width:100%;border-radius:26px;margin-top:20px;">
  </div>
  <div class="right">
    <div id="chatBody" class="chat-body"></div>
    <div class="chat-input">
      <input id="chatInput" placeholder="Type your question here...">
      <button onclick="sendMsg()">Send</button>
    </div>
  </div>
</div>
<script>
function addMsg(t,r){
  const b=document.getElementById("chatBody");
  const d=document.createElement("div");
  d.className="msg "+r;
  const s=document.createElement("div");
  s.className="bubble";
  s.textContent=t;
  d.appendChild(s);
  b.appendChild(d);
  b.scrollTop=b.scrollHeight;
}
function sendMsg(){
  const i=document.getElementById("chatInput");
  const t=i.value.trim();
  if(!t)return;
  addMsg(t,"user");
  i.value="";
  fetch("",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:t})})
    .then(r=>r.json()).then(d=>addMsg(d.reply,"assistant"));
}
</script>
</body>
</html>
"""

# ============================================
# Routes
# ============================================

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        instructor = Instructor.query.filter_by(email=email).first()
        if instructor:
            return redirect(url_for("manage_files", instructor_id=instructor.id))
        return redirect(url_for("new_instructor", email=email))
    return render_template_string(TEMPLATE_LOGIN_PAGE)


@app.route("/admin/new_instructor", methods=["GET","POST"])
def new_instructor():
    if request.method == "GET":
        return render_template_string(TEMPLATE_NEW_INSTRUCTOR, email=request.args.get("email",""))

    email = request.form.get("email")
    name = request.form.get("name")
    slug = re.sub(r"[^a-z0-9]+","",email.split("@")[0])

    vector_store_id = create_vector_store_http(f"WINK - {name}")

    instructor = Instructor(
        email=email,
        name=name,
        slug=slug,
        personal_vector_store_id=vector_store_id,
    )
    db.session.add(instructor)
    db.session.commit()

    return redirect(url_for("manage_files", instructor_id=instructor.id))


@app.route("/admin/manage_files/<int:instructor_id>", methods=["GET","POST"])
def manage_files(instructor_id):
    instructor = Instructor.query.get_or_404(instructor_id)
    return render_template_string(
        TEMPLATE_MANAGE_FILES,
        instructor=instructor,
        files=InstructorFile.query.filter_by(instructor_id=instructor.id).all(),
    )


@app.route("/wink/<slug>", methods=["GET","POST"])
def wink_chat(slug):
    instructor = Instructor.query.filter_by(slug=slug).first_or_404()
    if request.method == "POST":
        msg = request.get_json().get("message","")
        resp = client.responses.create(model="gpt-4.1-mini", input=msg)
        return jsonify({"reply": resp.output_text})
    return render_template_string(TEMPLATE_WINK_CHAT, instructor=instructor)


@app.errorhandler(404)
def catch_all(e):
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
