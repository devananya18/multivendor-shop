# MiniMart – a small multi-vendor shopping website

I built this project to understand how a real marketplace (like Amazon or Meesho) works behind the scenes. Many sellers can list their products, customers can buy from any of them, and an admin keeps everything under control.

It is made with **Python (Flask)** for the backend, **SQLite** for the database, and simple **HTML + CSS** for the pages.

## What can it do?

There are three types of people who use the site:

- **Customer** – search products, add to wishlist, add to cart, apply a coupon, place an order and see where the order has reached.
- **Vendor (seller)** – register as a seller, add products, and update the status of orders that contain their products.
- **Admin** – approve new sellers, approve new products, create coupons and see all orders.

Nothing a seller adds goes live directly. The admin has to approve the seller first, and then approve each product. This is how real marketplaces avoid fake listings.

## Try it on your computer

You need Python 3 installed. Open a terminal inside the project folder and run:

```
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 in your browser. (On Windows, if `python` does not work, use `py` instead.)

The database file is created by itself the first time, and a few demo products are added, so you do not have to write any SQL.

| Role     | Email           | Password  |
| -------- | --------------- | --------- |
| Admin    | admin@shop.com  | admin123  |
| Vendor   | vendor@shop.com | vendor123 |
| Customer | user@shop.com   | user123   |

You can also try the coupon **WELCOME10** (10% off on orders of Rs. 500 or more).

## How an order travels

1. A seller registers and waits. The admin approves the seller from the admin panel.
2. The seller adds a product. The admin approves it, and only then it shows up on the home page.
3. A customer adds it to the cart and checks out with an address (and a coupon if they have one). Stock goes down automatically.
4. The seller (or admin) changes the order status: Placed, Packed, Shipped, Delivered. The customer sees this as a progress bar on the Orders page.

Payment is a demo for now. The place where Razorpay or Stripe can be added is marked with a comment inside `checkout()` in `app.py`.

## Database tables

| Table       | What it stores                                                              |
| ----------- | --------------------------------------------------------------------------- |
| users       | name, email, hashed password, role (user / vendor / admin), approved or not |
| products    | which vendor owns it, price, stock, approved or not                         |
| cart        | which customer has which product and how many                               |
| wishlist    | products a customer has saved                                               |
| coupons     | code, discount percent, minimum order value                                 |
| orders      | who ordered, total, discount, address, status                               |
| order_items | each product inside an order, saved with its price at that time             |

`order_items` keeps its own copy of the price and the vendor, so old orders stay correct even if the seller changes the price later.

## Project structure

```
app.py            all the routes and logic
schema.sql        table definitions
templates/        the HTML pages (Jinja)
public/static/    CSS file
requirements.txt  Python packages needed
```

## Putting it online for free (Vercel)

1. Push this project to GitHub.
2. Go to vercel.com and log in with GitHub.
3. Click **Add New → Project** and pick this repository.
4. Vercel detects Flask on its own. Under Environment Variables add `SECRET_KEY` with any long random text.
5. Click **Deploy**.

One thing to know: Vercel does not keep files permanently, so on Vercel the SQLite database lives in a temporary folder and can reset. The demo accounts and products are re-created automatically, so the site always works for a demo. If you want data to stay forever, replace SQLite with a free hosted database like Neon or Supabase (PostgreSQL).

## Things I want to add later

- Real payments with Razorpay
- Product image upload
- Reviews and ratings
- A proper database like PostgreSQL
