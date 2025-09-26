from fastapi import FastAPI

app = FastAPI()

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

cart = []


@app.get("/")
def home():
    return {"message": "Welcome to Grocery Store API"}


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


@app.get("/cart")
def view_cart():
    if not cart:
        return {"cart": [], "total": 0}
    total = sum(item[2] for item in cart)
    return {"cart": cart, "total": total}


@app.post("/cart/{product_name}/{quantity}")
def add_to_cart(product_name: str, quantity: int):
    product_name = product_name.lower()
    if product_name not in products:
        return {"error": "Product not found"}
    price, unit, stock = products[product_name]
    if quantity > stock:
        return {"error": f"Only {stock} {unit} available"}
    total = price * quantity
    cart.append((product_name, quantity, total, unit))
    products[product_name][2] -= quantity
    return {"message": f"{quantity} {unit} {product_name} added to cart"}


@app.delete("/cart/{product_name}")
def remove_from_cart(product_name: str):
    product_name = product_name.lower()
    for item in cart:
        if item[0] == product_name:
            products[product_name][2] += item[1]
            cart.remove(item)
            return {"message": f"{product_name} removed from cart"}
    return {"error": "Item not in cart"}


@app.post("/checkout")
def checkout():
    if not cart:
        return {"error": "Cart is empty"}
    total = sum(item[2] for item in cart)
    discount = 0
    if total >= 3000:
        discount = total * 0.15
        total -= discount
    elif total >= 1000:
        discount = total * 0.10
        total -= discount
    gst = total * 0.05
    final = total + gst
    receipt = {
        "items": cart,
        "discount": int(discount),
        "gst": int(gst),
        "final_bill": int(final)
    }
    cart.clear()
    return receipt
