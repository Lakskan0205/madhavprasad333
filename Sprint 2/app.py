import os ,pathlib ,requests ,google.auth.transport.requests ,ibm_db ,tweepy
from flask import Flask, render_template, request, session, abort, redirect
from flask_mail import Mail, Message
from random import randint
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol

connectionstring = "DATABASE=bludb;HOSTNAME=3883e7e4-18f5-4afe-be8c-fa31c41761d2.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31498;PROTOCOL=TCPIP;UID=kmy46098;PWD=PN0aG7meNBbB7HH1;SECURITY=SSL;"
connection = ibm_db.connect(connectionstring, '', '')

app = Flask(__name__)
mail = Mail(app)
app.secret_key = "HireMe.com"

app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = '2k19cse052@kiot.ac.in'
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

consumer_key = ''
consumer_secret = ''
tcallback = ''

GOOGLE_CLIENT_ID = ""
client_secrets_file = os.path.join(
    pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)


@app.route("/")
def signup():
    return render_template("signup.html")


@app.route('/verification', methods=["POST", "GET"])
def verify():

    if request.method == 'POST':
        global first_name
        global last_name
        global useremail
        global password
        global email
        global otp
        global newuser

        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        useremail = request.form.get('email')
        password = request.form.get('password')
        newuser = 1

        sql = "SELECT * FROM User WHERE email =?"
        stmt = ibm_db.prepare(connection, sql)
        ibm_db.bind_param(stmt, 1, useremail)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)

        if (account):
            return render_template('signup.html', msg="You are already a member, please login using your details")

        else:
            otp = randint(000000, 999999)
            email = request.form['email']
            msg = Message(subject='OTP', sender='hackjacks@gmail.com',
                          recipients=[email])
            msg.body = "You have succesfully registered on Hire Me!\nUse the OTP given below to verify your email ID.\n\t\t" + \
                str(otp)
            mail.send(msg)
            return render_template('verification.html')

    if request.method == 'GET':
        otp = randint(000000, 999999)
        msg = Message(subject='OTP', sender='hackjacks@gmail.com',
                      recipients=[email])
        msg.body = "You have succesfully registered for Hire Me!\nUse the OTP given below to verify your email ID.\n\t\t" + \
            str(otp)
        mail.send(msg)
        return render_template('verification.html', resendmsg="OTP has been resent")


@app.route('/validate', methods=['POST'])
def validate():
    user_otp = request.form['otp']
    if otp == int(user_otp):
        insert_sql = "INSERT INTO User VALUES (?,?,?,?,?)"
        prep_stmt = ibm_db.prepare(connection, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, first_name)
        ibm_db.bind_param(prep_stmt, 2, last_name)
        ibm_db.bind_param(prep_stmt, 3, useremail)
        ibm_db.bind_param(prep_stmt, 4, password)
        ibm_db.bind_param(prep_stmt, 5, newuser)
        ibm_db.execute(prep_stmt)
        return render_template('signin.html')

    else:
        return render_template('verification.html', msg="OTP is invalid. Please enter a valid OTP")


@app.route("/googlelogin")
def googlelogin():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(
        session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["email_id"] = id_info.get("email")
    session["first_name"] = id_info.get("given_name")
    session["last_name"] = id_info.get("family_name")

    global first_name
    global last_name
    global useremail
    global password
    global newuser

    first_name = session['first_name']
    last_name = session['last_name']
    useremail = session['email_id']
    password = ""
    newuser = 1

    sql = "SELECT * FROM User WHERE email =?"
    stmt = ibm_db.prepare(connection, sql)
    ibm_db.bind_param(stmt, 1, useremail)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)

    if account:
        if (account['NEWUSER'] == 1):
            return redirect('/profile')
        return redirect('/home')

    else:
        insert_sql = "INSERT INTO User VALUES (?,?,?,?,?)"
        prep_stmt = ibm_db.prepare(connection, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, first_name)
        ibm_db.bind_param(prep_stmt, 2, last_name)
        ibm_db.bind_param(prep_stmt, 3, useremail)
        ibm_db.bind_param(prep_stmt, 4, password)
        ibm_db.bind_param(prep_stmt, 5, newuser)
        ibm_db.execute(prep_stmt)
        return redirect("/profile")


@app.route('/tlogin')
def auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, tcallback)
    url = auth.get_authorization_url()
    session['request_token'] = auth.request_token
    return redirect(url)

@app.route('/tcallback')
def twitter_callback():

    global first_name
    request_token = session['request_token']
    print(request_token)
    del session['request_token']

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret, tcallback)
    auth.request_token = request_token
    verifier = request.args.get('oauth_verifier')
    auth.get_access_token(verifier)
    session['token'] = (auth.access_token, auth.access_token_secret)
    first_name = session['token']
    return redirect('/profile')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/signin")


@app.route("/signup")
def signup1():
    return render_template("signup.html")


@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/signin")
@app.route("/login", methods=['GET', 'POST'])
def login():
    global useremail
    if request.method == 'POST':
        useremail = request.form.get('email')
        password = request.form.get('password')
        sql = "SELECT * FROM user WHERE email =?"
        stmt = ibm_db.prepare(connection, sql)
        ibm_db.bind_param(stmt, 1, useremail)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)

        if account:
            if (password == str(account['PASS']).strip()):
                if (account['NEWUSER'] == 1):
                    return redirect('/profile')
                return redirect('/home')
            else:
                return render_template('signin.html', msg="Password is invalid")
        else:
            return render_template('signin.html', msg="Email is invalid")
    else:
        return render_template('signin.html')


@app.route("/profile", methods=["POST", "GET"])
def profile():
    if (request.method == "POST"):
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        mobile_no = request.form.get('mobile_no')
        address_line_1 = request.form.get('address_line_1')
        address_line_2 = request.form.get('address_line_2')
        zipcode = request.form.get('zipcode')
        city = request.form.get('city')
        pemail = request.form.get('pemail')
        education = request.form.get('education')
        country = request.form.get('countries')
        state = request.form.get('states')
        experience = request.form.get('experience')
        job_title = request.form.get('job_title')

        insert_sql = "INSERT INTO profile VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
        prep_stmt = ibm_db.prepare(connection, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, first_name)
        ibm_db.bind_param(prep_stmt, 2, last_name)
        ibm_db.bind_param(prep_stmt, 3, mobile_no)
        ibm_db.bind_param(prep_stmt, 4, address_line_1)
        ibm_db.bind_param(prep_stmt, 5, address_line_2)
        ibm_db.bind_param(prep_stmt, 6, zipcode)
        ibm_db.bind_param(prep_stmt, 7, city)
        ibm_db.bind_param(prep_stmt, 8, pemail)
        ibm_db.bind_param(prep_stmt, 9, education)
        ibm_db.bind_param(prep_stmt, 10, country)
        ibm_db.bind_param(prep_stmt, 11, state)
        ibm_db.bind_param(prep_stmt, 12, experience)
        ibm_db.bind_param(prep_stmt, 13, job_title)
        ibm_db.execute(prep_stmt)

        insert_sql = "UPDATE USER SET newuser = false WHERE email = ?"
        prep_stmt = ibm_db.prepare(connection, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, useremail)
        ibm_db.execute(prep_stmt)
        return render_template('index.html')
    else:
        return render_template('profile.html')
