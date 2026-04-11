from database import db


class Product(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False)
    price = db.Column(db.Float, nullable = False)
    description = db.Column(db.Text, nullable = True)
    image_url = db.Column(db.Text, nullable = True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(120), nullable = False)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable = False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')


class Order(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    total = db.Column(db.Float, nullable = False)
    user = db.relationship('User')
    items = db.relationship('OrderItem', backref = 'order', lazy=True)



# from dataclasses import dataclass

# @dataclass
# class Product:
#     id: int 
#     name: str 
#     price: float 
#     description: str

# @dataclass
# class CartItem:
#     product_id: int 
#     quantity: int 

# @dataclass
# class Order:
#     id: int
#     total: float 
#     itens: list