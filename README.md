# 🛒 MiniMart — Multi-Vendor E-commerce (Flask + SQLite)

Three roles in one app: **User** (browse, wishlist, cart, coupon checkout, order tracking), **Vendor** (add products, update order status), **Admin** (approve vendors/products, manage coupons, all orders).

## Setup (2 minutes)
```bash
cd multivendor-shop
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                   # open http://127.0.0.1:5000
```
Tables are **created automatically** from `schema.sql` on first run (no manual SQL needed) and demo data is seeded.

| Role | Email | Password |
|---|---|---|
| Admin | admin@shop.com | admin123 |
| Vendor | vendor@shop.com | vendor123 |
| User | user@shop.com | user123 |

Demo coupon: `WELCOME10` (10% off orders ≥ ₹500).

## How it works
1. Vendor registers → stays **pending** → Admin approves in `/admin`.
2. Vendor adds a product → hidden until Admin approves it.
3. User adds to cart/wishlist → checkout (address + optional coupon). Stock is validated and reduced; prices are snapshotted into `order_items`.
4. Vendor/Admin moves status **Placed → Packed → Shipped → Delivered**; the user sees a live tracker on `/orders`.

## Database tables
`users`(role, approved) · `products`(vendor_id, approved, stock) · `cart` · `wishlist` · `coupons`(percent, min_total) · `orders`(status, coupon, discount) · `order_items`(vendor_id, price snapshot).
Relations: user 1─∞ orders 1─∞ order_items ∞─1 product ∞─1 vendor(user). Passwords are hashed (Werkzeug); routes are protected by a role decorator `@need("admin")`.

## Files
`app.py` all routes/logic · `schema.sql` tables · `templates/` Jinja pages · `static/style.css` styling.

## Deploy free
**Render:** push to GitHub → New *Web Service* → Build `pip install -r requirements.txt` → Start `gunicorn app:app` → env vars `SECRET_KEY=<random>`.
Free Render disks are ephemeral, so SQLite data resets on redeploy: add a Render disk and set `DB_PATH=/data/shop.db`, or use **PythonAnywhere** (free, keeps files; Flask setup guide on their site, point WSGI to `app`).

## Adding Razorpay/Stripe (optional)
In `checkout()` (marked with a comment): create a payment order with the SDK (`pip install razorpay`) using the cart total, show the checkout widget, verify the signature in a callback route, and only then insert the order. Keep keys in env vars.

## Interview talking points
Normalized schema & foreign keys · role-based access · approval workflow · price snapshotting · coupon validation · stock control · status state machine.
Ideas to extend: pagination, product reviews, CSRF (Flask-WTF), Postgres.
