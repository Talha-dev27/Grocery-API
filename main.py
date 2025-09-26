from fastapi import FastAPI
from typing import Optional

app = FastAPI()

# ---------------- Data ----------------
products = {
    "apple": [200, "per kg", 50],
    "banana": [100, "per dozen", 30],
    "milk": [220, "per liter", 20],
    "bread": [250, "per loaf", 15],
    "eggs": [350, "per dozen", 40],
    "rice": [270, "per kg", 100],
    "sugar": [165, "per kg", 70],
    "chicken": [660, "per kg", 25],
    "beef": [2200, "per kg", 10],
    "oil": [450, "per liter", 40],
    "tea": [800, "per kg", 20],
    "salt": [50, "per kg", 60]
}

users = {}  # user_id: {"cart": [], "orders": [], "wishlist": [], "points": 0}
coupons = {"SAVE10": 0.10, "SAVE20": 0.20}


# ---------------- Home ----------------
@app.get("/")
def home():
    return {"message": "Welcome to Grocery Store API"}


# ---------------- Product Endpoints ----------------
@app.get("/products")
def get_products(
    search: Optional[str] = None,
    max_price: Optional[int] = None,
    sort: Optional[str] = None,
    order: str = "asc"
):
    product_list = []
    for name, (price, unit, stock) in products.items():
        if search and search.lower() not in name.lower():
            continue
        if max_price and price > max_price:
            continue
        product_list.append({
            "name": name.capitalize(),
            "price": price,
            "unit": unit,
            "stock": stock,
            "low_stock": stock < 5
        })

    if sort:
        reverse = (order == "desc")
        product_list.sort(key=lambda x: x[sort], reverse=reverse)

    return {"products": product_list}


@app.put("/products/{product_name}")
def update_product(product_name: str, price: Optional[int] = None, stock: Optional[int] = None):
    product_name = product_name.lower()
    if product_name not in products:
        return {"error": "Product not found"}
    if price:
        products[product_name][0] = price
    if stock:
        products[product_name][2] = stock
    return {"message": f"{product_name} updated", "product": products[product_name]}


# ---------------- User Management ----------------
@app.post("/users/{user_id}")
def create_user(user_id: str):
    if user_id in users:
        return {"error": "User already exists"}
    users[user_id] = {"cart": [], "orders": [], "wishlist": [], "points": 0}
    return {"message": f"User {user_id} created"}


@app.get("/users/{user_id}")
def user_profile(user_id: str):
    if user_id not in users:
        return {"error": "User not found"}
    user = users[user_id]
    return {
        "user_id": user_id,
        "loyalty_points": user["points"],
        "cart_items": len(user["cart"]),
        "wishlist_items": len(user["wishlist"]),
        "total_orders": len(user["orders"])
    }


# ---------------- Cart ----------------
@app.post("/cart/{user_id}/{product_name}/{quantity}")
def add_to_cart(user_id: str, product_name: str, quantity: int):
    if user_id not in users:
        return {"error": "User not found"}
    product_name = product_name.lower()
    if product_name not in products:
        return {"error": "Product not found"}
    price, unit, stock = products[product_name]
    if quantity > stock:
        return {"error": f"Only {stock} {unit} available"}
    total = price * quantity
    users[user_id]["cart"].append((product_name, quantity, total, unit))
    products[product_name][2] -= quantity
    return {"message": f"{quantity} {unit} {product_name} added to cart"}


@app.get("/cart/{user_id}")
def view_cart(user_id: str):
    if user_id not in users:
        return {"error": "User not found"}
    cart = users[user_id]["cart"]
    total = sum(item[2] for item in cart)
    return {"cart": cart, "total": total}


@app.delete("/cart/{user_id}/{product_name}")
def remove_from_cart(user_id: str, product_name: str):
    if user_id not in users:
        return {"error": "User not found"}
    product_name = product_name.lower()
    cart = users[user_id]["cart"]
    for item in cart:
        if item[0] == product_name:
            products[product_name][2] += item[1]
            cart.remove(item)
            return {"message": f"{product_name} removed from cart"}
    return {"error": "Item not in cart"}


# ---------------- Checkout ----------------
@app.post("/checkout/{user_id}")
def checkout(user_id: str, coupon: Optional[str] = None, use_points: bool = False):
    if user_id not in users:
        return {"error": "User not found"}
    cart = users[user_id]["cart"]
    if not cart:
        return {"error": "Cart is empty"}

    total = sum(item[2] for item in cart)
    discount = 0

    # Auto-discount
    if total >= 3000:
        discount = total * 0.15
    elif total >= 1000:
        discount = total * 0.10

    # Coupon discount
    if coupon and coupon in coupons:
        discount += total * coupons[coupon]

    total -= discount

    # Loyalty points discount
    points_used = 0
    if use_points and users[user_id]["points"] > 0:
        points_used = min(users[user_id]["points"], int(total))  # 1 point = 1 Rs
        total -= points_used
        users[user_id]["points"] -= points_used

    gst = total * 0.05
    final = total + gst

    # Earn new points (1 per 100 spent, after discounts but before GST)
    earned_points = int(total // 100)
    users[user_id]["points"] += earned_points

    receipt = {
        "items": cart,
        "discount": int(discount),
        "coupon_used": coupon if coupon else None,
        "points_used": points_used,
        "points_earned": earned_points,
        "remaining_points": users[user_id]["points"],
        "gst": int(gst),
        "final_bill": int(final)
    }

    users[user_id]["orders"].append(receipt)
    users[user_id]["cart"].clear()
    return receipt


# ---------------- Orders ----------------
@app.get("/orders/{user_id}")
def order_history(user_id: str):
    if user_id not in users:
        return {"error": "User not found"}
    return {"orders": users[user_id]["orders"]}


# ---------------- Wishlist ----------------
@app.post("/wishlist/{user_id}/{product_name}")
def add_to_wishlist(user_id: str, product_name: str):
    if user_id not in users:
        return {"error": "User not found"}
    product_name = product_name.lower()
    if product_name not in products:
        return {"error": "Product not found"}
    users[user_id]["wishlist"].append(product_name)
    return {"message": f"{product_name} added to wishlist"}


@app.get("/wishlist/{user_id}")
def view_wishlist(user_id: str):
    if user_id not in users:
        return {"error": "User not found"}
    return {"wishlist": users[user_id]["wishlist"]}

