from flask import Flask,render_template,request,redirect,url_for
from models import db,Transaction
from df_manager import parse_dataframe,save_in_db,detect_format
from sqlalchemy import func,case
import os
from collections import Counter

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spending.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
upload_folder = 'uploads/'
app.config['UPLOAD_FOLDER'] = upload_folder
os.makedirs(upload_folder , exist_ok = True)

db.init_app(app)

with app.app_context():
    # db.drop_all()
    db.create_all()

@app.route('/',methods=['POST','GET'])
def content():
    if request.method == "POST":
        try:
            if 'statement' in request.files:
                file = request.files['statement']
                if file.filename != "" :
                    path = os.path.join(app.config['UPLOAD_FOLDER'],file.filename)
                    file.save(path)
                    df = detect_format(file.filename)
                    save_in_db(df)
                    os.remove(path)
                    return redirect(url_for('results'))
        except Exception as e:
                print(e)
                return render_template('index.html')

    
    return render_template('index.html')

@app.route('/dashboard',methods=['POST','GET'])
def results():
    all_transactions = Transaction.query
    
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    category = request.args.get('category')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    some_entity = request.args.get('some_entity')
    
    print(some_entity)
    
    total_credit = db.session.query(db.func.sum( Transaction.amount)).filter(Transaction.type == 'debit') 
    total_debit = db.session.query(db.func.sum( Transaction.amount)).filter(  Transaction.type == 'credit')
    
    total_Person_Credit = db.session.query(db.func.sum( Transaction.amount)).filter(Transaction.type=='credit',Transaction.category == 'Person') 
    total_Person_Debit = db.session.query(db.func.sum( Transaction.amount)).filter(  Transaction.type == 'debit' , Transaction.category == 'Person')
    
    total_Merchant_Credit = db.session.query(db.func.sum( Transaction.amount)).filter(Transaction.type=='credit',Transaction.category == 'Merchant') 
    total_Merchant_Debit = db.session.query(db.func.sum( Transaction.amount)).filter(  Transaction.type == 'debit' , Transaction.category == 'Merchant')
    
    # daily_spending = db.session.query(
    #                      Transaction.date,
    #                     func.sum( Transaction.amount)
    #                 ).filter( Transaction.type == 'debit').group_by( Transaction.date).order_by( Transaction.date)
    
    daily_credit = db.session.query(
                         Transaction.date,
                        func.sum( Transaction.amount)
                    ).filter( Transaction.type == 'credit').group_by( Transaction.date).order_by( Transaction.date)
    daily_spending = db.session.query(
                         Transaction.date,
                        func.sum( Transaction.amount)
                    ).filter( Transaction.type == 'debit').group_by( Transaction.date).order_by( Transaction.date)
    if start_date and end_date:
        total_credit = total_credit.filter(Transaction.date >= start_date)
        total_debit = total_debit.filter(Transaction.date >= start_date)
        daily_spending = daily_spending.filter(Transaction.date >= start_date)
        daily_credit = daily_credit.filter(Transaction.date >= start_date)
        all_transactions = all_transactions.filter(Transaction.date >= start_date)
        total_Person_Credit = total_Person_Credit.filter(Transaction.date >= start_date)
        total_Person_Debit =  total_Person_Debit.filter(Transaction.date >= start_date)
        total_Merchant_Credit = total_Merchant_Credit.filter(Transaction.date >= start_date)
        total_Merchant_Debit = total_Merchant_Debit.filter(Transaction.date >= start_date)
    
    
    if end_date:
        total_credit = total_credit.filter( Transaction.date <= end_date)
        total_debit = total_debit.filter( Transaction.date <= end_date)
        daily_spending = daily_spending.filter( Transaction.date <= end_date)
        daily_credit = daily_credit.filter( Transaction.date <= end_date)
        all_transactions = all_transactions.filter( Transaction.date <= end_date)
        total_Person_Credit = total_Person_Credit.filter( Transaction.date <= end_date)
        total_Person_Debit =  total_Person_Debit.filter( Transaction.date <= end_date)
        total_Merchant_Credit = total_Merchant_Credit.filter( Transaction.date <= end_date)
        total_Merchant_Debit = total_Merchant_Debit.filter( Transaction.date <= end_date)       
    
    
    if category:
        total_credit = total_credit.filter(Transaction.category == category)
        total_debit = total_debit.filter(Transaction.category == category)
        daily_spending = daily_spending.filter(Transaction.category == category)
        daily_credit = daily_credit.filter(Transaction.category == category)
        all_transactions = all_transactions.filter(Transaction.category == category)
        total_Person_Credit = total_Person_Credit.filter(Transaction.category == category)
        total_Person_Debit =  total_Person_Debit.filter(Transaction.category == category )
        total_Merchant_Credit = total_Merchant_Credit.filter(Transaction.category == category)
        total_Merchant_Debit = total_Merchant_Debit.filter(Transaction.category == category)
    
    
    if min_amount:
        total_credit = total_credit.filter(Transaction.amount >= min_amount)
        total_debit = total_debit.filter(Transaction.amount >= min_amount)
        daily_spending = daily_spending.filter(Transaction.amount >= min_amount)
        daily_credit = daily_credit.filter(Transaction.amount >= min_amount)
        all_transactions = all_transactions.filter(Transaction.amount >= min_amount)
        total_Person_Credit = total_Person_Credit.filter(Transaction.amount >= min_amount)
        total_Person_Debit =  total_Person_Debit.filter(Transaction.amount >= min_amount )
        total_Merchant_Credit = total_Merchant_Credit.filter(Transaction.amount >= min_amount)
        total_Merchant_Debit = total_Merchant_Debit.filter(Transaction.amount>= min_amount)
        
    if max_amount:
        total_credit = total_credit.filter(Transaction.amount <=  max_amount)
        total_debit = total_debit.filter(Transaction.amount <=  max_amount)
        daily_spending = daily_spending.filter(Transaction.amount <=  max_amount)
        daily_credit = daily_credit.filter(Transaction.amount <=  max_amount)
        all_transactions = all_transactions.filter(Transaction.amount <=  max_amount)
        total_Person_Credit = total_Person_Credit.filter(Transaction.amount <=  max_amount)
        total_Person_Debit =  total_Person_Debit.filter(Transaction.amount <=  max_amount )
        total_Merchant_Credit = total_Merchant_Credit.filter(Transaction.amount <=  max_amount)
        total_Merchant_Debit = total_Merchant_Debit.filter(Transaction.amount<=  max_amount)
        
    if some_entity:
        entity_transactions = db.session.query(
                                Transaction.date,
                                Transaction.type,
                                Transaction.amount
                            ).filter(Transaction.payee == some_entity).order_by(Transaction.date).all()
        
        entity_dict = {}
        for row in entity_transactions:
            date, type_, amount = row[0], row[1], row[2]
            if date not in entity_dict:
                entity_dict[date] = 0
            if type_ == 'credit':
                entity_dict[date] += amount
            else:
                entity_dict[date] -= amount
        entity_labels = [str(d) for d in entity_dict.keys()]
        entity_data = list(entity_dict.values())
    else:
        entity_labels = []
        entity_data = []
    daily_credit = daily_credit.all()
    biggest_transaction = all_transactions.order_by(db.desc(Transaction.amount)).first()
    daily_spending = daily_spending.all()
    total_credit = total_credit.scalar() or 0.0
    total_debit = total_debit.scalar() or 0.0
    total_Merchant_Credit = total_Merchant_Credit.scalar() or 0.0
    total_Merchant_Debit = total_Merchant_Debit.scalar() or 0.0
    total_Person_Credit  = total_Person_Credit.scalar() or 0.0
    total_Person_Debit   = total_Person_Debit.scalar() or 0.0
    
    
    pie_category_lables = ["Mercant","Person"]
    pie_category_values_credit = [total_Merchant_Credit,total_Person_Credit]
    pie_category_values_debit = [total_Merchant_Debit,total_Person_Debit]
    
    x_labels_debit = [row[0] for row in daily_spending]
    x_labels_credit = [row[0] for row in daily_credit]
    spending_data = [row[1] for row in daily_spending] 
    credit_data = [row[1] for row in daily_credit]
   
        
    
    payee_name = all_transactions.with_entities(Transaction.payee).distinct().all()
    payee_name = [name[0] for name in payee_name]
    all_transactions =  all_transactions.all()
    
    name_list = [t.payee for t in all_transactions]
    top_categories = []
    top_iterations = []
    if name_list:
        name_tallies = Counter(name_list)
        if len(name_tallies) >= 10:
            for i in name_tallies.most_common(10):
                top_categories.append(i[0])
                top_iterations.append(i[1])
    # print(top_categories,top_iterations)
                
        
    
    return render_template('dashboard.html',transactions = all_transactions , credit_sum = total_credit,debit_sum = total_debit , X_AXIS =   x_labels_debit,Y_AXIS = spending_data
                           ,PIE_CREDIT_LABLES = pie_category_lables , PIE_CREDIT_VALUES_CREDIT = pie_category_values_credit ,PIE_CREDIT_VALUES_DEBIT = pie_category_values_debit,TOP_PAYEE_CATEGORIES = top_categories,
                           TOP_PAYEE_NUMBERS = top_iterations , Big_transaction_amount = biggest_transaction.amount , Big_transaction_type = biggest_transaction.type
                           ,Big_transaction_Payee =biggest_transaction.payee, X_AXIS_CREDIT =x_labels_credit,Y_AXIS_CREDIT = credit_data, Payee_names = payee_name,
                           ENTITY_DATA = entity_data ,  ENTITY_LABELS = entity_labels 
                           )


@app.route('/update_category/<int:id>', methods=['POST'])
def update_category(id):
    transaction = Transaction.query.get_or_404(id)
    new_category = request.form.get('category')
    
    if new_category in ['Merchant', 'Person']:
    
        Transaction.query.filter_by(payee=transaction.payee)\
            .update({'category': new_category})
    else:
        transaction.category = new_category
    
    db.session.commit()
    return '', 204


if __name__ == "__main__":
    
    app.run(debug = True)