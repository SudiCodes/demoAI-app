from langchain_openai import OpenAI
from flask import Flask , render_template , jsonify,request
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from datetime import datetime
from src.prompt import *
import os
import re

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

load_dotenv("env")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

db = SQLAlchemy(app)  # Initialize SQLAlchemy with the app context

# Ensure the database is created
with app.app_context():
    db.create_all()


bcrypt = Bcrypt(app)
jwt = JWTManager(app)



class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    mobile_number = db.Column(db.String(15), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    is_demo_active = db.Column(db.Boolean, default=False)
    is_subscribed = db.Column(db.Boolean, default=False)
    subscription_till = db.Column(db.DateTime, nullable=True)

    def __init__(self, email, password, first_name, last_name, mobile_number=None, state=None, 
                 is_demo_active=False, is_subscribed=False, subscription_till=None):
        self.email = email
        self.password = self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.mobile_number = mobile_number
        self.state = state
        self.is_demo_active = is_demo_active
        self.is_subscribed = is_subscribed
        self.subscription_till = subscription_till
        self.username = self.generate_username(first_name, last_name)

    def set_password(self, password):
        return bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    @staticmethod
    def generate_username(first_name, last_name):
        username = (first_name[:3] + last_name[-3:]).lower()
        count = 1
        while User.query.filter_by(username=username).first():
            username = f"{username}{count}"
            count += 1
        return username

# User Registration Route
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    mobile_number = data.get("mobile_number")
    state = data.get("state")

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 400

    user = User(email=email, password=password, first_name=first_name, last_name=last_name,
                mobile_number=mobile_number, state=state)
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "User registered successfully"}), 201

# User Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Bad email or password"}), 401

# Initialize the Flask-Admin extension
admin = Admin(app, name='Admin Portal', template_mode='bootstrap3')

# Create a custom view for the User model
class UserModelView(ModelView):
    # Optional: Customize which fields are displayed in the admin view
    column_list = ('id', 'email', 'first_name', 'last_name', 'mobile_number', 'state', 'is_demo_active', 'is_subscribed', 'subscription_till')
    form_columns = ('email', 'password', 'first_name', 'last_name', 'mobile_number', 'state', 'is_demo_active', 'is_subscribed', 'subscription_till')

    # You can also override methods to customize behavior (e.g., form validation)
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

# Add the User model to the admin interface
admin.add_view(UserModelView(User, db.session))

with app.app_context():
    db.create_all()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')  

os.environ['PINECONE_API_KEY'] = PINECONE_API_KEY
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY  


# Medbot logic
embeddings = download_hugging_face_embeddings()

index_name = "medicalbot"

docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k":3})


# Route for the homepage
@app.route('/')
def home():
    return "This site is under developement"

# API route for handling JSON requests
@app.route('/chat', methods=['POST'])
def api():
    data = request.json
    query = data.get("query")  # Extract query from the input JSON
    llm = OpenAI(api_key=OPENAI_API_KEY, temperature=0.4, max_tokens=500)
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
   
    response = rag_chain.invoke({"input": query})
    
    return jsonify({"answer": response["answer"]})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080,debug=True)
