from flask import Flask, render_template, request,redirect,flash,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import date,datetime
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin,current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Set up Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///grocery_app.sqlite3"

db = SQLAlchemy(app)
app.app_context().push()

app.config['SECRET_KEY'] = 'thisisasecretkey'

# # Initialize Bcrypt and SQLAlchemy
# bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "user_login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Manager(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    m_name = db.Column(db.String(100), unique=True, nullable=False)
    m_password_hash = db.Column(db.String(100), nullable=False)
    
    def initialize_manager():
        manager = Manager.query.filter_by(m_name='manager').first()
        if not manager:
            new_manager = Manager(m_name='manager')
            new_manager.set_password('manager@123')
            db.session.add(new_manager)
            db.session.commit()

    def set_password(self, password):
        self.m_password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.m_password_hash, password)

class Section(db.Model):
    section_id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(100), unique=True, nullable=False)
    section_description = db.Column(db.String(1000), nullable=False)
    products = db.relationship('Product', backref='section', lazy=True, cascade="all, delete-orphan")

class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    product_manufacture_date = db.Column(db.Date)
    product_expiry_date = db.Column(db.Date)
    product_rate_per_unit = db.Column(db.Float, nullable=False)
    product_unit = db.Column(db.String(20))  # For example, 'Rs/Kg', 'Rs/Litre'
    product_stock = db.Column(db.Integer, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.section_id'), nullable=False)  # Corrected the ForeignKey


    def __repr__(self):
        return f"Product('{self.product_name}', Manufactured: {self.product_manufacture_date}, Expires: {self.product_expiry_date}, Rate: {self.product_rate_per_unit} {self.product_unit})"

class UserCart(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    product_rate_per_unit = db.Column(db.Float, nullable=False)
    product_qty = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)

class UserTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ut_date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    product_rate_per_unit = db.Column(db.Float, nullable=False)
    product_qty = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)


@app.route('/')
def home_page():
    return render_template("home_page.html")


@app.route('/manager/sections')
def landing_page():
     return render_template('landing.html')


@app.route('/manager', methods=['GET', 'POST'])
def manager_login():
    if request.method == 'POST':
        m_name = request.form.get('m_name')
        m_password = request.form.get('m_password')
        manager = Manager.query.filter_by(m_name=m_name).first()

        if manager and manager.check_password(m_password):
            login_user(manager)
            flash('Logged in successfully as manager.')
            return redirect("/manager/sections") 
        else:
            flash('Invalid manager credentials. Please try again.', 'error')

    return render_template('manager_details.html')


@app.route('/section/create', methods=['GET', 'POST'])
def create_section():
    if request.method == 'POST':
        s_name = request.form['s_name']
        s_description = request.form['s_description']

        sec = Section(
             section_name = s_name,
             section_description = s_description
        )

        db.session.add(sec)
        db.session.commit()

        return redirect('/manager/sections')
    return render_template("create_section.html")

@app.route('/section/<int:section_id>/delete', methods=['POST'])
def delete_section(section_id):
    section_id = int(request.form.get('section_id'))
    s1 = Section.query.get(section_id)
    db.session.delete(s1)
    db.session.commit()
    return redirect("/manager/sections")
@app.route('/section/update', methods=['POST'])
def update_section():
    section_id = int(request.form.get('section_id'))
    new_name = request.form.get('s_name')
    new_description = request.form.get('s_description')

    # Fetch the section data from your data source (e.g., database)
    section = Section.query.get(section_id)

    if section:
        # Update the section data
        section.s_name = new_name
        section.s_description = new_description

        # Commit the changes to the database
        db.session.commit()

    # Redirect to a page showing the updated section or your desired destination
    return redirect(url_for('section_detail', section_id=section_id))

@app.route('/sections')
def view_sections():
     all = Section.query.all()
     return render_template("view_sections.html", all = all)


@app.route('/section/<int:section_id>/products', methods=['GET', 'POST'])
def products_list(section_id):
    s1 = Section.query.get(section_id)
    items = s1.products
    return render_template('products.html', items=items)


@app.route('/section/<int:section_id>/summary', methods=['GET', 'POST'])
def section_summary(section_id):
    section = Section.query.get(section_id)
    
    if section:
        product_names = []
        product_stocks = []

        for product in section.products:
            product_names.append(product.product_name)
            product_stocks.append(product.product_stock)

        plt.clf()
        plt.figure(figsize=(10, 6))
        plt.bar(product_names, product_stocks)
        plt.xlabel('Products')
        plt.ylabel('Stock')
        plt.xticks(rotation=45, ha='right')  # Rotate x-axis labels for better readability
        plt.tight_layout()

        # Save the plot image to a file
        plt.savefig('static/section_summary.png')  # Save the plot image

        return render_template("section_summary.html", section=section)

@app.route('/product/create', methods=['GET', 'POST'])
def create_product():
    if request.method == 'POST':
        # Process the form submission
        p_name = request.form['p_name']
        p_mnf_date = datetime.strptime(request.form['p_mnf_date'], '%Y-%m-%d')
        p_exp_date = datetime.strptime(request.form['p_exp_date'], '%Y-%m-%d')
        p_rate_unit = request.form['p_rate_unit']
        p_unit = request.form['p_unit']
        p_stock = request.form['p_stock']
        p_section_name = request.form['p_section_name']

        # Query the database to get the section object based on section_name
        section = Section.query.filter_by(section_name=p_section_name).first()

        if section:
            # Assuming that the 'Section' model has a 'section_id' attribute
            prod = Product(
                product_name=p_name,
                product_manufacture_date=p_mnf_date,
                product_expiry_date=p_exp_date,
                product_rate_per_unit=p_rate_unit,
                product_unit=p_unit,
                product_stock=p_stock,
                section_id=section.section_id  # Use the correct attribute here
            )

            db.session.add(prod)
            db.session.commit()

            return redirect('/manager/sections')
        else:
            flash('Section not found. Please enter a valid section name.', 'error')

    # Query the database to retrieve section names
    sections = Section.query.all()

    return render_template("create_product.html", sections=sections)


@app.route('/product/<int:product_id>/update', methods=['GET', 'POST'])
def update_product(product_id):
    product = Product.query.get(product_id)

    if request.method == 'POST':
        product.product_name = request.form['product_name']
        product.product_manufacture_date = datetime.strptime(request.form['product_manufacture_date'], '%Y-%m-%d')
        product.product_expiry_date = datetime.strptime(request.form['product_expiry_date'], '%Y-%m-%d')
        product.product_rate_per_unit = request.form['product_rate_per_unit']
        product.product_unit = request.form['product_unit']
        product.product_stock = request.form['product_stock']
        product.section_id = request.form['section_id']

        db.session.commit()

        return redirect('/manager/sections')  # Redirect to the desired page after updating

    return render_template("update_product.html", product=product)

@app.route('/product/<int:product_id>/delete' , methods = ['POST'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect('/manager/sections')

@app.route('/products')
def view_products():
     products = Product.query.all()
     return render_template("view_products.html", products = products)


@app.route('/product/<int:product_id>/summary', methods=['GET', 'POST'])
def summary(product_id):
    product = Product.query.get(product_id)
    
    if product:
        product_name = product.product_name
        product_stock = product.product_stock

        plt.clf()
        plt.xlabel('Product')
        plt.ylabel('Stock')
        plt.bar([product_name], [product_stock])
        plt.savefig('static/summary.png')  # Save the plot image
        

        return render_template("summary.html", product=product)
  
    
@app.route('/user', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully as user.')
            return redirect("/user/dashboard")
        else:
            flash('Invalid user credentials. Please try again.', 'error')

    return render_template('user_login.html')



@app.route('/user/dashboard')
def user_dashboard():
    uname = current_user.username  # Assuming you are using Flask-Login's current_user
    s1 = Section.query.all()  # Get sections from the database

    return render_template('user_dashboard.html', uname=uname, s1=s1)



@app.route('/user/orders')
def user_orders():
        uname = current_user.username
        transactions = UserTransaction.query.filter_by(username=uname).all()
        return render_template("user_orders.html", uname = uname, transactions = transactions)


@app.route('/user/logout')
def user_logout():
    return redirect('/user')


@app.route('/user/recommended', methods = ['GET','POST'])
def user_recommended():
    uname = current_user.username  # Assuming you are using Flask-Login's current_user

    # Get the user's recent purchases
    user_transactions = UserTransaction.query.filter_by(username=uname).order_by(UserTransaction.ut_date.desc()).limit(5).all()

    # Extract the unique product IDs from the purchases
    unique_product_ids = set(transaction.product_id for transaction in user_transactions)

    # Get the details of the unique products
    recommended_products = Product.query.filter(Product.product_id.in_(unique_product_ids)).all()

    # Get sections from the database
    sections = Section.query.all()

    return render_template("user_recommended.html", recommended_products=recommended_products, sections=sections,uname = uname)


@app.route('/user/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if the username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another.', 'error')
        else:
            new_user = User(username=username)
            new_user.set_password(password)  # Set the password using the set_password method
            db.session.add(new_user)
            db.session.commit()
            flash('Account registered successfully. You can now log in.')
            return redirect("/user")  # Redirect to the login page after successful registration

    return render_template('register_user.html')

@app.route('/sections/<string:uname>', methods=['GET'])
def categories_list(uname):
    s1 = Section.query.all()
        
    return render_template('user_section_list.html', uname=uname, s1=s1)



@app.route('/section/<int:section_id>/<string:username>/products', methods=['GET','POST'])
def user_products_list(section_id, username):
    s1 = Section.query.get(section_id)
    items = s1.products
    return render_template('user_products_list.html', s1=s1, items=items, uname=username)


@app.route('/products/search/<string:username>', methods=['POST'])
def products_search(username):
    search_term = request.form.get('item')
    
    # Assuming you want to search for products with a similar name
    filtered_products = Product.query.filter(Product.product_name.ilike(f'%{search_term}%')).all()
    
    return render_template('searched_products.html', products=filtered_products, uname=username)

@app.route('/sections/search/<string:username>', methods=['POST'])
def sections_search(username):
    s1 = Section.query.get('section_id')
    section_name = Section.query.get('section_name')
    search_term = request.form.get('item')
    
    # Assuming you want to search for sections with a similar name
    filtered_sections = Section.query.filter(Section.section_name.ilike(f'%{search_term}%')).all()
    uname = current_user.username
    return render_template('section_search.html', sections=filtered_sections, uname=username, s1 = s1,section_name =section_name)



@app.route('/products/<int:product_id>/<string:username>/add_to_cart', methods=['POST'])
@app.route('/user/cart', methods=['GET', 'POST'])
def user_cart(product_id=None, username=None):
    uname = current_user.username if username is None else username
    
    if request.method == 'POST':
        if product_id is not None:
            # Add product to cart
            tdate = date.today()
            product_qty = request.form.get('product_qty')
            product = Product.query.get(product_id)
            amt = product.product_rate_per_unit * int(product_qty)
            i1 = UserCart(username=uname, product_id=product_id, product_name=product.product_name, product_rate_per_unit=product.product_rate_per_unit, product_qty=product_qty, amount=amt)

            db.session.add(i1)
            db.session.commit()

    user_cart = UserCart.query.filter_by(username=uname).all()
    return render_template("user_cart.html", uname=uname, user_cart=user_cart)



@app.route('/products/<int:product_id>/<string:username>/delete_from_cart', methods=['POST'])
def delete_from_cart(product_id, username):
    cart_item = UserCart.query.filter_by(username=username, product_id=product_id).first()

    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()

    user_cart = UserCart.query.filter_by(username=username).all()
    return render_template('user_cart.html', user_cart=user_cart, uname = username)




@app.route('/add_to_cart/update/<string:username>/<int:item_id>', methods=['GET', 'POST'])
def cart_update(username, item_id):
    i1 = UserCart.query.get(item_id)
    
    if request.method == 'GET':
        return render_template('user_cart_update.html', i1=i1, uname=username)

    if request.method == 'POST':
        p_qty = request.form.get('product_qty')
        p_rpu = request.form.get('product_rate_per_unit')
        i1.product_qty = int(p_qty)
        i1.amount = i1.product_qty * i1.product_rate_per_unit
        db.session.commit()
        
        user_cart = UserCart.query.filter_by(username=username).all()
        return redirect("/user/cart")       


# Sample dictionary to store coupon codes and their corresponding discounts
coupon_codes = {
    "HARDIK10": 0.1,  # 10% discount
}

@app.route('/add_to_cart/coupon/<string:username>/<int:item_id>', methods=['GET', 'POST'])
def add_coupon(username, item_id):
    i1 = UserCart.query.get(item_id)  # Use the correct model class here

    if request.method == 'GET':
        return render_template('user_cart_with_coupon.html', i1=i1, uname=username)
    
    if request.method == 'POST':
        coupon_code = request.form.get('coupon_code')
        discount = coupon_codes.get(coupon_code, 0.0)

        i1.amount = i1.product_qty * i1.product_rate_per_unit * (1.0 - discount)  # Apply discount

        db.session.commit()

        user_cart_items = UserCart.query.filter_by(username=username).all()
        return redirect("/user/cart")


@app.route('/search/<string:uname>', methods=['GET', 'POST'])
def search(uname):
    if request.method == 'POST':
        data = request.form.get('item')
        s1 = Section.query.filter(Section.section_name.ilike(f"%{data}%")).all()
        p1 = Product.query.filter(Product.product_name.ilike(f"%{data}%")).all()

        if len(s1) != 0:
            return render_template('section_search.html', s1=s1, uname=uname)
        if len(p1) != 0:
            return render_template('product_search.html', p1=p1, uname=uname)

        return render_template('search_error.html', uname=uname)
    
    return redirect("/user/dashboard")


@app.route('/checkout/<string:username>', methods=['GET', 'POST'])
def checkout(username):
    tdate = datetime.utcnow().date()
    total_amount = 0
    i1s = UserCart.query.filter_by(username=username).all()

    for i1 in i1s:
        product = Product.query.get(i1.product_id)

        # Check if there are enough items in stock to complete the transaction
        if i1.product_qty <= product.product_stock:
            utransaction = UserTransaction(
                ut_date=tdate,
                username=username,
                product_id=i1.product_id,
                product_name=i1.product_name,
                product_rate_per_unit=i1.product_rate_per_unit,
                product_qty=i1.product_qty,
                amount=i1.amount
            )

            db.session.add(utransaction)
            product.product_stock -= i1.product_qty
            total_amount += i1.amount
        else:
            # Not enough items in stock for this product, handle it as needed
            flash(f'Not enough {i1.product_name} in stock to complete the transaction.', 'error')
            return redirect(url_for('user_dashboard', username=username))  # Change to your user dashboard route

    if request.method == 'POST':
        # Clear the user's cart after successful checkout
        UserCart.query.filter_by(username=username).delete()
        db.session.commit()

        flash('Checkout successful! Your order has been placed.', 'success')
        return redirect(url_for('user_dashboard', username=username))  # Change to your user dashboard route

    if request.method == 'GET':
        return render_template('checkout.html', i1s=i1s, username=username, total_amount=total_amount)



# run code in debug mode
if __name__ == "__main__":
    with app.app_context():
        Manager.initialize_manager()
    app.run(debug=True)