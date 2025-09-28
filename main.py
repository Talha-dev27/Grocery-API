from fastapi import FastAPI

app = FastAPI()

# ---------------- Products ----------------
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

# ---------------- Users ----------------
users = {}  # user_id: {"cart": [], "orders": [], "wishlist": [], "points": 0, "is_admin": False}


# ---------------- Home ----------------
@app.get("/")
def home():
    return {"message": "Welcome to Grocery Store API"}


# ---------------- Create User ----------------
@app.post("/users/{user_id}")
def create_user(user_id: str, admin: bool = False):
    if user_id in users:
        return {"error": "User already exists"}
    users[user_id] = {
        "cart": [],
        "orders": [],
        "wishlist": [],
        "points": 0,
        "is_admin": admin
    }
    role = "Admin" if admin else "Customer"
    return {"message": f"{role} {user_id} created successfully"}


# ---------------- User Profile ----------------
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
        "total_orders": len(user["orders"]),
        "is_admin": user["is_admin"]
    }


# ---------------- Products ----------------
@app.get("/products")
def get_products():
    product_list = []
    for name, (price, unit, stock) in products.items():
        product_list.append({
            "name": name.capitalize(),
            "price": price,
            "unit": unit,
            "stock": stock
        })
    return {"products": product_list}


# ---------------- Wishlist ----------------
@app.post("/wishlist/{user_id}/{product_name}")
def add_to_wishlist(user_id: str, product_name: str):
    if user_id not in users:
        return {"error": "User not found"}
    product_name = product_name.lower()
    if product_name not in products:
        return {"error": "Product not found"}
    users[user_id]["wishlist"].append(product_name)
    return {"message": f"{product_name} added to {user_id}'s wishlist"}


@app.get("/wishlist/{user_id}")
def view_wishlist(user_id: str):
    if user_id not in users:
        return {"error": "User not found"}
    return {"wishlist": users[user_id]["wishlist"]}


# ---------------- Cart ----------------
@app.get("/cart/{user_id}")
def view_cart(user_id: str):
    if user_id not in users:
        return {"error": "User not found"}
    cart = users[user_id]["cart"]
    if not cart:
        return {"cart": [], "total": 0}
    total = sum(item[2] for item in cart)
    return {"cart": cart, "total": total}


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


@app.delete("/cart/{user_id}/{product_name}")
def remove_from_cart(user_id: str, product_name: str):
    if user_id not in users:
        return {"error": "User not found"}
    cart = users[user_id]["cart"]
    product_name = product_name.lower()
    for item in cart:
        if item[0] == product_name:
            products[product_name][2] += item[1]
            cart.remove(item)
            return {"message": f"{product_name} removed from cart"}
    return {"error": "Item not in cart"}


# ---------------- Checkout ----------------
@app.post("/checkout/{user_id}")
def checkout(user_id: str):
    if user_id not in users:
        return {"error": "User not found"}
    cart = users[user_id]["cart"]
    if not cart:
        return {"error": "Cart is empty"}

    total = sum(item[2] for item in cart)
    discount = 0

    # Loyalty discount
    if users[user_id]["points"] >= 100:
        discount += 100
        users[user_id]["points"] -= 100

    # Purchase discount
    if total >= 3000:
        discount += total * 0.15
    elif total >= 1000:
        discount += total * 0.10

    total -= discount
    gst = total * 0.05
    final = total + gst

    # Add loyalty points
    earned_points = int(final // 100)
    users[user_id]["points"] += earned_points

    receipt = {
        "items": cart,
        "discount": int(discount),
        "gst": int(gst),
        "final_bill": int(final),
        "loyalty_points_earned": earned_points,
        "total_loyalty_points": users[user_id]["points"]
    }

    users[user_id]["orders"].append(receipt)
    users[user_id]["cart"].clear()

    return receipt



