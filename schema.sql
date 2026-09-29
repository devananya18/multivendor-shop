CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT,
  role TEXT CHECK(role IN('user','vendor','admin')) DEFAULT 'user', approved INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, vendor_id INTEGER REFERENCES users(id), name TEXT,
  description TEXT, price REAL, stock INTEGER, image TEXT, approved INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS cart(user_id INTEGER, product_id INTEGER, qty INTEGER DEFAULT 1, PRIMARY KEY(user_id,product_id));
CREATE TABLE IF NOT EXISTS wishlist(user_id INTEGER, product_id INTEGER, PRIMARY KEY(user_id,product_id));
CREATE TABLE IF NOT EXISTS coupons(code TEXT PRIMARY KEY, percent INTEGER, min_total REAL DEFAULT 0, active INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), total REAL, discount REAL,
  coupon TEXT, address TEXT, status TEXT DEFAULT 'Placed', created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders(id),
  product_id INTEGER, vendor_id INTEGER, name TEXT, price REAL, qty INTEGER);
