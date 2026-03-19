from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Transaction(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    date = db.Column(db.Date , nullable=False)
    payee = db.Column(db.String(300) , nullable=False)
    type = db.Column(db.String(100) , nullable=False)
    amount = db.Column(db.Float,nullable=False)
    category = db.Column(db.String(100),default='Uncategorized')
    
    def __repr__(self):
        return f"transaction:{self.id} , date:{self.date}"