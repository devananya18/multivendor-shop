import os, sqlite3
from functools import wraps
from flask import Flask, g, session, request, redirect, render_template, flash, abort
from werkzeug.security import generate_password_hash as gph, check_password_hash as cph

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("DB_PATH", os.path.join(BASE, "shop.db"))
STEPS = ["Placed", "Packed", "Shipped", "Delivered"]
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-change-me")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
    return g.db
@app.teardown_appcontext
def close(_):
    d = g.pop("db", None)
    if d: d.close()
def q(sql, a=(), one=False):
    c = db().execute(sql, a); r = c.fetchall(); db().commit()
    return (r[0] if r else None) if one else r

def init():
    c = sqlite3.connect(DB); c.executescript(open(os.path.join(BASE, "schema.sql")).read())
    if not c.execute("select 1 from users").fetchone():
        for n, e, p, r, a in [("Admin", "admin@shop.com", "admin123", "admin", 1),
                              ("Demo Vendor", "vendor@shop.com", "vendor123", "vendor", 1),
                              ("Demo User", "user@shop.com", "user123", "user", 1)]:
            c.execute("insert into users(name,email,password,role,approved) values(?,?,?,?,?)", (n, e, gph(p), r, a))
        for i, (n, p) in enumerate([("Wireless Earbuds", 1499), ("Cotton T-Shirt", 499), ("Steel Water Bottle", 699)]):
            c.execute("insert into products(vendor_id,name,description,price,stock,image,approved) values(2,?,?,?,25,?,1)",
                      (n, "Demo product", p, f"https://picsum.photos/seed/{i+7}/400/300"))
        c.execute("insert into coupons values('WELCOME10',10,500,1)")
    c.commit(); c.close()
init()

def me():
    return q("select * from users where id=?", (session["uid"],), True) if "uid" in session else None
def need(*roles):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            u = me()
            if not u: return redirect("/login")
            if roles and u["role"] not in roles: abort(403)
            return f(*a, **k)
        return w
    return deco
@app.context_processor
def inject():
    u = me()
    n = q("select coalesce(sum(qty),0) n from cart where user_id=?", (u["id"],), True)["n"] if u else 0
    return dict(user=u, cart_n=n)

# ---------- auth ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form; role = "vendor" if f.get("role") == "vendor" else "user"
        try:
            q("insert into users(name,email,password,role,approved) values(?,?,?,?,?)",
              (f["name"], f["email"].lower(), gph(f["password"]), role, 0 if role == "vendor" else 1))
        except sqlite3.IntegrityError:
            flash("Email already registered"); return redirect("/register")
        flash("Registered! " + ("Wait for admin approval to sell." if role == "vendor" else "Please log in.")); return redirect("/login")
    return render_template("auth.html", mode="register")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = q("select * from users where email=?", (request.form["email"].lower(),), True)
        if u and cph(u["password"], request.form["password"]):
            session["uid"] = u["id"]
            return redirect({"admin": "/admin", "vendor": "/vendor"}.get(u["role"], "/"))
        flash("Wrong email or password")
    return render_template("auth.html", mode="login")
@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

# ---------- shop ----------
@app.route("/")
def index():
    s = request.args.get("s", "")
    ps = q("select p.*,u.name vendor from products p join users u on u.id=p.vendor_id "
           "where p.approved=1 and u.approved=1 and p.name like ? order by p.id desc", ("%" + s + "%",))
    wl = {r["product_id"] for r in q("select product_id from wishlist where user_id=?", (session.get("uid", 0),))}
    return render_template("index.html", ps=ps, wl=wl, title="All products")
@app.route("/wishlist")
@need()
def wishlist():
    ps = q("select p.*,u.name vendor from wishlist w join products p on p.id=w.product_id "
           "join users u on u.id=p.vendor_id where w.user_id=?", (session["uid"],))
    return render_template("index.html", ps=ps, wl={p["id"] for p in ps}, title="My wishlist")
@app.post("/wish/<int:pid>")
@need()
def wish(pid):
    a = (session["uid"], pid)
    if q("select 1 from wishlist where user_id=? and product_id=?", a, True):
        q("delete from wishlist where user_id=? and product_id=?", a)
    else: q("insert into wishlist values(?,?)", a)
    return redirect(request.referrer or "/")
@app.post("/add/<int:pid>")
@need()
def add(pid):
    a = (session["uid"], pid)
    if q("select 1 from cart where user_id=? and product_id=?", a, True):
        q("update cart set qty=qty+1 where user_id=? and product_id=?", a)
    else: q("insert into cart(user_id,product_id) values(?,?)", a)
    flash("Added to cart"); return redirect(request.referrer or "/")
@app.post("/remove/<int:pid>")
@need()
def remove(pid):
    q("delete from cart where user_id=? and product_id=?", (session["uid"], pid)); return redirect("/cart")

def cart_items():
    return q("select c.qty,p.* from cart c join products p on p.id=c.product_id where c.user_id=?", (session["uid"],))
@app.route("/cart")
@need()
def cart():
    items = cart_items()
    return render_template("cart.html", items=items, sub=sum(i["qty"] * i["price"] for i in items))
@app.post("/checkout")
@need()
def checkout():
    items = cart_items()
    if not items: return redirect("/cart")
    for i in items:
        if i["qty"] > i["stock"]:
            flash(f"Only {i['stock']} left of {i['name']}"); return redirect("/cart")
    sub = sum(i["qty"] * i["price"] for i in items)
    code = request.form.get("coupon", "").strip().upper(); disc = 0; used = None
    if code:
        c = q("select * from coupons where code=? and active=1", (code,), True)
        if not c or sub < c["min_total"]:
            flash("Invalid coupon or minimum order value not met"); return redirect("/cart")
        used, disc = code, round(sub * c["percent"] / 100, 2)
    # (Razorpay/Stripe: create the payment here, place the order only after payment succeeds. See README.)
    oid = db().execute("insert into orders(user_id,total,discount,coupon,address) values(?,?,?,?,?)",
                       (session["uid"], sub - disc, disc, used, request.form["address"])).lastrowid
    for i in items:
        db().execute("insert into order_items(order_id,product_id,vendor_id,name,price,qty) values(?,?,?,?,?,?)",
                     (oid, i["id"], i["vendor_id"], i["name"], i["price"], i["qty"]))
        db().execute("update products set stock=stock-? where id=?", (i["qty"], i["id"]))
    db().execute("delete from cart where user_id=?", (session["uid"],)); db().commit()
    flash(f"Order #{oid} placed!"); return redirect("/orders")
@app.route("/orders")
@need()
def orders():
    os_ = q("select * from orders where user_id=? order by id desc", (session["uid"],))
    its = {o["id"]: q("select * from order_items where order_id=?", (o["id"],)) for o in os_}
    return render_template("orders.html", os=os_, its=its, steps=STEPS)

# ---------- vendor ----------
@app.route("/vendor", methods=["GET", "POST"])
@need("vendor")
def vendor():
    u = me()
    if request.method == "POST" and u["approved"]:
        f = request.form
        q("insert into products(vendor_id,name,description,price,stock,image) values(?,?,?,?,?,?)",
          (u["id"], f["name"], f["description"], float(f["price"]), int(f["stock"]),
           f["image"] or f"https://picsum.photos/seed/{f['name']}/400/300"))
        flash("Product submitted for admin approval"); return redirect("/vendor")
    ps = q("select * from products where vendor_id=?", (u["id"],))
    os_ = q("select distinct o.* from orders o join order_items i on i.order_id=o.id where i.vendor_id=? order by o.id desc", (u["id"],))
    return render_template("vendor.html", ps=ps, os=os_, steps=STEPS)
@app.post("/order/<int:oid>/status")
@need("vendor", "admin")
def status(oid):
    u = me(); s = request.form["status"]
    mine = q("select 1 from order_items where order_id=? and vendor_id=?", (oid, u["id"]), True)
    if s in STEPS and (u["role"] == "admin" or mine):
        q("update orders set status=? where id=?", (s, oid))
    return redirect(request.referrer or "/")

# ---------- admin ----------
@app.route("/admin")
@need("admin")
def admin():
    return render_template("admin.html", steps=STEPS,
        vs=q("select * from users where role='vendor' order by approved"),
        ps=q("select p.*,u.name vendor from products p join users u on u.id=p.vendor_id order by p.approved"),
        cs=q("select * from coupons"), os=q("select * from orders order by id desc"))
@app.post("/admin/approve/<kind>/<int:i>")
@need("admin")
def approve(kind, i):
    t = {"vendor": "users", "product": "products"}.get(kind) or abort(404)
    q(f"update {t} set approved=? where id=?", (int(request.form["v"]), i)); return redirect("/admin")
@app.post("/admin/coupon")
@need("admin")
def add_coupon():
    f = request.form
    q("insert or replace into coupons values(?,?,?,1)", (f["code"].upper(), int(f["percent"]), float(f["min_total"] or 0)))
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
