from flask import Flask, request, redirect, session
import json, os, hashlib, random, datetime

app = Flask(__name__)
app.secret_key = "securekey"

DATA_FILE = "bank.json"

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load():
    if not os.path.exists(DATA_FILE):
        return {}
    return json.load(open(DATA_FILE))

def save(d):
    json.dump(d, open(DATA_FILE, "w"), indent=4)

def gen_acc():
    return str(random.randint(10000000, 99999999))

def user():
    return session.get("user")

def page(content):
    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont;
    background: #f7f8fa;
}}

.app {{
    max-width: 420px;
    margin: auto;
    background: white;
    min-height: 100vh;
    position: relative;
}}

.header {{
    background: #ff5f4a;
    color: white;
    padding: 30px 20px;
    border-bottom-left-radius: 25px;
    border-bottom-right-radius: 25px;
    text-align: center;
}}

.balance {{
    font-size: 40px;
    margin: 10px 0;
}}

.card {{
    background: white;
    margin: -30px 15px 15px;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.08);
}}

.btn {{
    width: 100%;
    padding: 14px;
    margin: 6px 0;
    border: none;
    border-radius: 12px;
    background: #ff5f4a;
    color: white;
    font-weight: bold;
    font-size: 16px;
}}

input {{
    width: 100%;
    padding: 12px;
    margin: 8px 0;
    border-radius: 10px;
    border: 1px solid #ddd;
}}

.tx {{
    padding: 12px;
    border-bottom: 1px solid #eee;
}}

.fab {{
    position: fixed;
    bottom: 70px;
    right: 20px;
    background: #ff5f4a;
    color: white;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    font-size: 30px;
    text-align: center;
    line-height: 60px;
    text-decoration: none;
}}

.nav {{
    position: fixed;
    bottom: 0;
    width: 100%;
    max-width: 420px;
    background: white;
    display: flex;
    justify-content: space-around;
    padding: 10px;
    border-top: 1px solid #eee;
}}

.nav a {{
    text-decoration: none;
    color: #444;
    font-size: 14px;
}}
</style>
</head>

<body>
<div class="app">
{content}

<a href="/deposit" class="fab">+</a>

<div class="nav">
    <a href="/">Home</a>
    <a href="/transfer">Send</a>
    <a href="/transactions">Activity</a>
</div>

</div>
</body>
</html>
"""

@app.route("/")
def home():
    if not user():
        return redirect("/login")

    d = load()
    u = user()

    return page(f"""
<div class="header">
    <h3>{u}</h3>
    <div class="balance">£{d[u]['balance']}</div>
</div>

<div class="card">
    <button class="btn" onclick="location.href='/transfer'">Send Money</button>
    <button class="btn" onclick="location.href='/withdraw'">Withdraw</button>
</div>
""")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        d = load()
        u = request.form["username"]
        p = request.form["password"]

        if u in d:
            return "User exists"

        d[u] = {
            "password": hash_password(p),
            "balance": 0,
            "account": gen_acc(),
            "transactions": []
        }
        save(d)
        return redirect("/login")

    return page("""
<div class="card">
<h2>Create Account</h2>
<form method='post'>
<input name='username' placeholder='Username'>
<input name='password' type='password' placeholder='Password'>
<button class='btn'>Create</button>
</form>
</div>
""")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        d = load()
        u = request.form["username"]
        p = request.form["password"]

        if u in d and d[u]["password"] == hash_password(p):
            session["user"] = u
            return redirect("/")
        return "Invalid login"

    return page("""
<div class="card">
<h2>Login</h2>
<form method='post'>
<input name='username' placeholder='Username'>
<input name='password' type='password' placeholder='Password'>
<button class='btn'>Login</button>
</form>
</div>
""")

@app.route("/deposit", methods=["GET","POST"])
def deposit():
    if not user(): return redirect("/login")
    if request.method == "POST":
        d = load()
        u = user()
        amt = float(request.form["amount"])
        d[u]["balance"] += amt
        d[u]["transactions"].insert(0, f"Deposit £{amt}")
        save(d)
        return redirect("/")
    return page("""
<div class="card">
<h2>Add Money</h2>
<form method='post'>
<input name='amount' placeholder='Amount'>
<button class='btn'>Add</button>
</form>
</div>
""")

@app.route("/withdraw", methods=["GET","POST"])
def withdraw():
    if not user(): return redirect("/login")
    if request.method == "POST":
        d = load()
        u = user()
        amt = float(request.form["amount"])
        if amt <= d[u]["balance"]:
            d[u]["balance"] -= amt
            d[u]["transactions"].insert(0, f"Withdraw £{amt}")
            save(d)
        return redirect("/")
    return page("""
<div class="card">
<h2>Withdraw</h2>
<form method='post'>
<input name='amount'>
<button class='btn'>Withdraw</button>
</form>
</div>
""")

@app.route("/transfer", methods=["GET","POST"])
def transfer():
    if not user(): return redirect("/login")
    if request.method == "POST":
        d = load()
        sender = user()
        acc = request.form["account"]
        amt = float(request.form["amount"])

        for u in d:
            if d[u]["account"] == acc and amt <= d[sender]["balance"]:
                d[sender]["balance"] -= amt
                d[u]["balance"] += amt
                d[sender]["transactions"].insert(0, f"Sent £{amt}")
                d[u]["transactions"].insert(0, f"Received £{amt}")
                save(d)
        return redirect("/")

    return page("""
<div class="card">
<h2>Send Money</h2>
<form method='post'>
<input name='account' placeholder='Account number'>
<input name='amount' placeholder='Amount'>
<button class='btn'>Send</button>
</form>
</div>
""")

@app.route("/transactions")
def transactions():
    if not user(): return redirect("/login")
    d = load()
    u = user()

    tx_html = ""
    for t in d[u]["transactions"]:
        tx_html += f"<div class='tx'>{t}</div>"

    return page(f"""
<div class="card">
<h2>Activity</h2>
{tx_html}
</div>
""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
