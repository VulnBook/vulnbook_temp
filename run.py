from app.db import create_app

#from app import db
app = create_app()

#reset the database
#with app.app_context():
   #db.drop_all()
   #db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)