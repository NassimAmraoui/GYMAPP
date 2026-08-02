import mysql.connector as sql
from mysql.connector import errorcode 
import uuid
import smtplib
import bcrypt
from email.mime.text import MIMEText
import random
import os
ssl_certificate = "/etc/secrets/ca.pem"
DB_PASSWORD = os.getenv("DB_PASSWORD")
EMAIL_SERVICE = os.getenv("EMAIL_SERVICE")
PASSWORD_EMAIL_SERVICE = os.getenv("PASSWORD_EMAIL_SERVICE")
from fastapi import FastAPI
data = {"email":"","password":"","code":""}
app = FastAPI()

def hashingPassword(password):
    selt = password.encode('utf-8')#convert the str to bytes
    hashing_password = bcrypt.hashpw(selt,bcrypt.gensalt())#the function bcrypt.gensalt() he is make password hash by calculted on low level memory 
    story_password = hashing_password.decode('utf-8')#convert the file bytes to str 
    print(story_password)
    return(story_password)


def codeConfirm():
    code = ""
    arr = ["0","1","2","3","4","5","6","7","8","9"]
    for i in range(8):
        t = random.randint(1,8)
        code += arr[t]
    return code

def sendEmailConfirm(to_email,subject,body):
    senderEmail = EMAIL_SERVICE
    app_password = PASSWORD_EMAIL_SERVICE
    smtp_host = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
    smtp_port = int(os.getenv("SMTP_PORT", 2525))
    sender_email = os.getenv("SMTP_USER")
    app_password = os.getenv("SMTP_PASS")
    
    msg = MIMEText(body,"html")
    msg["Subject"] = subject
    msg["From"] = senderEmail
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
        server.login(senderEmail,app_password)
        server.sendmail(senderEmail,to_email,msg.as_string())
@app.get("/sendCode")
def sendCode():
    subject = "Verify your email address for GYM APP"
    data["code"] = codeConfirm()
    body = (f"""
                <div style ="display: flex;justify-content: center;align-items: center;flex-direction: column;row-gap: 20px;">
                   
                Hi,<br>Welcome to GYM APP! To complete your registration and secure your account, please confirm that you own this email address
                        <div style="box-sizing: border-box;border-radius: 8%;width: 200px; height: 150px;padding: 20px;background-color: bisque;">
                                <div style = "font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;font-size: 30px;text-align: center;width: 100%;background-color: rgb(135, 152, 222);">Code</div>
                                <div style = "height: 50%;border-radius: 5px;font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;font-size: 30px;text-align: center;width: 100%;background-color:rgb(0, 208, 255);">{data['code']}</div>
                        </div> 
                </div>
        """)
    try:
        sendEmailConfirm(data["email"], subject, body)
        return {"status": "200", "message": f"the message sent {data['email']}"}
    except Exception as e:
        print(f"SMTP Error on Render: {e}")
        # Return a graceful message so your desktop app doesn't crash on .json() parsing
        return {
            "status": "error", 
            "message": "Email server restricted on cloud host, but code generated successfully."
        }

@app.post("/saveData")
def saveData(dataSv : dict):
    data["email"] = dataSv.get("email","")
    data["password"] = dataSv.get("password","")
    return {"code":200,"message":"data it save"}

@app.post("/CreateAccount")
def CreateAccount(dataRV : dict):
    confirm = dataRV.get("confirm",False)
    Code = dataRV.get("code","")
    res = False
    if(confirm and data["code"] == Code ): 
        try:
            connexion = sql.connect(
                host ="mysql-24a70c3f-amraoui-7d80.a.aivencloud.com",
                port =22229 ,
                user = "avnadmin",
                password=DB_PASSWORD,
                database="gestion_salle_sport",     
                ssl_ca = ssl_certificate,
                ssl_verify_cert = True)
            cr = connexion.cursor()
            inst = "INSERT INTO accounts(id_account,email,password_account)VALUES(%s,%s,%s)"
            id = str(uuid.uuid4())
            password_is_hashing = hashingPassword(data['password'])
            cr.execute(inst,(id,data["email"],password_is_hashing))
            connexion.commit()
            inst2 = "SELECT * FROM accounts"
            resultat = cr.fetchall()

            for r in resultat:
                print(r)
            
            cr.close()
            connexion.close()
            res = True
            return {"resultat":res}
        except sql.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("the somthing worren in your name or password")
            elif err.errno ==  errorcode.ER_BAD_DB_ERROR:
                print(f"there not data base with name {"gestion_salle_sport"}")
            else:
                print(err)
    return {"resultat":res}
@app.get("/checkAccount")
def check_exist_account():
    exist = False
    db="gestion_salle_sport"
    try:
        connexion = sql.connect(
                host ="mysql-24a70c3f-amraoui-7d80.a.aivencloud.com",
                port =22229 ,
                user = "avnadmin",
                password=DB_PASSWORD,
                database="gestion_salle_sport",     
                ssl_ca =ssl_certificate,
                ssl_verify_cert = True)
        cr = connexion.cursor()
        inst2 = "SELECT * FROM accounts"
        cr.execute(inst2)
        resultat = cr.fetchall()
        for row in resultat:
            password_in_database = str(row[1])
            correct_password = bcrypt.checkpw(data['password'].encode('utf-8'),password_in_database.encode('utf-8'))
            
            if(data['email'] == str(row[0]) and correct_password):
                exist = True
        
        
        cr.close()
        connexion.close()
    except sql.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("the somthing worren in your name or password")
        elif err.errno ==  errorcode.ER_BAD_DB_ERROR:
            print(f"there not data base with name {db}")
        else:
            print(err)
    return exist

