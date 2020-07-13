from flask import (
    Flask, 
    render_template,
    request,
    flash,
    json,
    send_file,
    session,
    jsonify
)

from model import (
    insert_user, 
    login_users,
    update_verified_user,
    select_email,
    insert_code,
    validation_code,
    change_password_user,
    select_roles,
    select_city,
    select_country,
    select_docs,
    users_organizations,
    insert_users_organizations,
    insert_roles_users_organizations,
    selec_users_roles,
    list_user_data_edit,
    update_data_user,
    update_user_organizations,
    disable_roles_users_organizations,
    admin_list_user_data_edit,
    select_organizations,
    list_remaining_users_organizations,
    selec_roles_users_organizations,
    admin_users_organizations,
    insert_roles_organization_demo,
    login_user_organization
)

from model_organization import(
    admin_create_organizations,
    list_data_organization,
    list_data_all_organizations,
    update_organization_data,
    list_model_crop_organization,
    select_remaining_crops,
    organization_all_model_crops,
    insert_update_organization_crop,
    insert_organization_model_train,
    disable_crop_organization,
    enable_crop_organization,
    disable_organization_model_train,
    crops_organization,
    crops_model_organization,
)

from model_stage import(
    organization_crops,
    organization_model_crops,
    list_model_weight,
    calculate_stage,
    insert_stage_attachments,
    list_calculate_stage ,
    insert_humidity_attachments,
    list_calculate_humidity,
    calculate_plant,
    insert_plant_attachments,
    list_calculate_plant
)

from werkzeug.utils import secure_filename
from functools import wraps
import jwt
import datetime
import os
import glob
import shutil

from flask_wtf import CsrfProtect
from config import DevelopmentConfig

from other_functions import (
    predict_image,
    generate_uuid,
    humidity_calculation,
    plant_health
)

from flask_mail import (
    Mail, 
    Message
)

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CsrfProtect()
mail = Mail()



@app.route('/')
def index():
    return render_template('pages/index.html')


# Insertar imagenes dinámicamente 

def save_image(image,directory):
    
    app.config['UPLOAD_FOLDER'] = './static/images/'+directory

    name_image = str(generate_uuid(2))

    image_path = os.path.join(app.config['UPLOAD_FOLDER'], name_image + '.png')

    filename = secure_filename(image.filename)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    os.rename(os.path.join(app.config['UPLOAD_FOLDER'], filename), os.path.join(image_path))

    return name_image

#Traer la cuidad de acuerdo al país     
@app.route('/get_city/<country>')
def get_city(country):

    citys=select_city(country)
    city = citys[0][0]
    json_city = json.loads(city)

    return jsonify(json_city)  

#Traer el modelo de aprendisaje de acuerdo al cultivo
@app.route('/get_model_all_crop/<crop>')
def get_model_all_crop(crop):

    model_crops=organization_all_model_crops(crop)
    model_crop = model_crops[0][0]
    json_model_crop = json.loads(model_crop)

    return jsonify(json_model_crop) 

@app.route('/get_model_crop/<crop>')
def get_model_crop(crop):

    model_crops=organization_model_crops(session['organization_id'],crop)
    model_crop = model_crops[0][0]
    json_crop= json.loads(model_crop)

    return jsonify(json_crop) 

@app.route('/crops_org')
def crops_org():

    list_crops_org =crops_organization(session['organization_id'])
    return render_template('pages/crops_organization.html', list_crops_org=list_crops_org)   

@app.route('/crops_model_org/<crop_id>/<crop_name>')
def crops_model_org(crop_id,crop_name):

    list_model_crop =crops_model_organization(crop_id,session['organization_id'])
    return render_template('pages/crops_model_organization.html', list_model_crop=list_model_crop, crop_name=crop_name)   


@app.route('/login')
def login():
    return render_template('pages/login.html')   

@app.route('/login_validation',methods=['POST'])
def login_validation():

    email = request.form['email']
    password = request.form['password']

    validation_login = login_users(email,password)

    if (validation_login == 'error_usu'):  
        msg_login ='El correo no registra en sistema'
        return render_template('pages/login.html', msg_login= msg_login) 
   
    elif (validation_login == 'error_pass'):  
        msg_login ='La contraseña ingresada es incorrecta'
        return render_template('pages/login.html', msg_login= msg_login)   
   
    elif (validation_login == 'no_verified'):  
        msg_login ='El correo del usuario no ha sido validado'
        return render_template('pages/login.html', msg_login= msg_login)   
   
    else:
        session['data'] = validation_login

        return render_template('pages/select_organization.html')


@app.route('/forgot_password')
def forgot_password():
    return render_template('pages/forgot_password.html')  

@app.route('/request_password_code', methods=['GET'])    
def request_password_code():

    email= request.args.get('email')

    validation = select_email(email)

    code = generate_uuid(1)


    if len(validation) > 0:
        
        subject = str(code)+' es el código de recuperación de tu cuenta ' 

        msg = Message ( subject = subject, 
                        sender = app.config['MAIL_USERNAME'],
                        recipients = [email] )

        msg.html = render_template('pages/forgot_password_email.html', user_id = validation[0][0], user = validation[0][1], email= validation[0][2],code = code)
        mail.send(msg)

        insert_code(validation[0][0],str(code))

        return render_template('pages/forgot_password_validation_code.html',user_id = validation[0][0], code=code, email= email) 

    else:
        return render_template('pages/forgot_password.html', validation_email ="error") 


@app.route('/password_validation_code', methods=['GET'])
def password_validation_code():

    code= request.args.get('code')
    user_id = request.args.get('user_id')

    validation=validation_code(code,user_id)

    if len(validation) > 0:
        return render_template('pages/forgot_password_code.html', user_id = validation[0][0]) 
    else:
        return render_template('pages/forgot_password_validation_code.html', user_id= user_id, validation_code ="error")    

@app.route('/forgot_password_code')     
def forgot_password_code():
    return render_template('pages/forgot_password_code.html') 

@app.route('/change_password', methods=['POST'])
def change_password():

    user_id = request.form['user_id']
    change_password= request.form['change_password']

    change_password_user(user_id,change_password)

    msg_user= 'Contraseña actualizada con exito'
    msg_content = 'Ingresa con tu usuario y contraseña actualizada y tendrás acceso a nuestra plataforma '
    
    return render_template('pages/login.html', msg_user= msg_user, msg_content=msg_content )   

@app.route('/enter_user/<user_id>/<organization>')
def enter_user(user_id,organization):   

    user_data = login_user_organization(user_id,organization)

    session['user_id'] = user_data[0][0]
    session['user'] = user_data[0][1]

    if user_data[0][2] is None:
        if session['data'][0][5] == 1:
            session['profile_photo'] ='/static/images/male.png'
        else :
            session['profile_photo'] ='/static/images/female.png'
    else:
        session['profile_photo'] = user_data[0][2]

    session['organization_id'] = user_data[0][3]
    session['organization_name'] = user_data[0][4]
    session['roles'] = user_data[0][5]
    session['type'] = user_data[0][6]

    list_stage= list_calculate_stage(session['organization_id'])
    return render_template('pages/stage_attachments.html',list_stage = list_stage)   

@app.route('/logout')
def logout():

    session.clear()
    
    return render_template('pages/login.html') 

@app.before_request
def before_request():

    pages=[ 'admin_create_users','admin_create_organization',
            'admin_users','create_users','health_attachments',
            'health_calculation','humidity_attachments','humidity_ground',
            'organization','users','stage_attachments','stages_crop'
            ]

    if 'user' not in session and request.endpoint in pages:
        return render_template('pages/login.html') 
    
    elif 'user' in session  and request.endpoint in ['login']:
        return render_template('stage_attachments.html')                                                                              
        

# Listar usuario de la organización
   
@app.route('/users')
def users():
    us_org = users_organizations(session['organization_id'])
    
    return render_template('pages/users.html',us_org=us_org)    

# Crear usuario en la organización

@app.route('/create_users')
def create_users():
    roles = select_roles()
    country = select_country()
    docs = select_docs()
    citys = select_city(1)
    city = citys[0][0]
    json_city = json.loads(city)

    return render_template('pages/create_users.html',roles = roles, country= country, docs= docs, json_city=json_city)

# Insertar usuario en la organización
@app.route('/insert_user_page',methods=['POST'])
def insert_user_page():

    first_name = request.form['first_name']
    second_name = request.form['second_name']
    first_surname = request.form['first_surname']
    second_surname = request.form['second_surname']
    doc_type_id  = request.form['doc_type_id']
    num_doc = request.form['num_doc']
    gender = request.form['gender']
    city_id = request.form['city_id']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    profile_photo = request.files['profile_photo']
    roles_user = request.form.getlist('roles[]')
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    roles = select_roles()
    country = select_country()
    docs = select_docs()
    citys = select_city(1)
    city = citys[0][0]
    json_city = json.loads(city)


    if password == confirm_password:

        if profile_photo.content_type == 'application/octet-stream':
            profile_photos = None
        else:
            profile_photos = save_image(profile_photo,'profile_photo')
            profile_photos= '/static/images/profile_photo/'+profile_photos+'.png'
 
        roless = tuple(int(x) for x in roles_user)  

        token_validation = jwt.encode({'user': email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(seconds=3600)}, app.config['SECRET_KEY'])
        token_validation = token_validation.decode('UTF-8')

        assign_data = insert_user(first_name,second_name,first_surname,second_surname,doc_type_id,num_doc,gender,city_id,email,phone,address,profile_photos,password,token_validation)

        if (assign_data == 'exists'): 

            msg_create_user ='Verifica el correo electrónico, número de celular o número de documento del usuario, ya que uno de estos datos se encuentran registrado en el sistema.'

            return render_template('pages/create_users.html', msg_create_user = msg_create_user,roles = roles, country= country, docs= docs, json_city=json_city)    

        else:
            
            msg = Message ( 'Gracias por tu registro!', 
                             sender = app.config['MAIL_USERNAME'],
                             recipients = [email] )

            msg.html = render_template('pages/email.html', user = first_name + " " + second_name, token_validation = token_validation)
            mail.send(msg)

            insert_users_organizations(session['organization_id'],assign_data[0][0])
            insert_roles_users_organizations(session['organization_id'],assign_data[0][0],roless)
            insert_roles_organization_demo(assign_data[0][0])
            list_user = list_user_data_edit(assign_data[0][0],session['organization_id'])
            roles_user = selec_users_roles(assign_data[0][0],session['organization_id'])

            msg_create_user ='Verifica tu correo electrónico en la bandeja de entrada, SPAN o correo no deseado y continua con el registro.'

            return render_template('pages/create_users_email_invitation.html',msg_create_user = msg_create_user, list_user = list_user, roles = roles_user)  
            

    else:
        
        msg_create_user ='La contraseñas no coiciden, llena el formulario nuevamente y verifica estos campos.'

        return render_template('pages/create_users.html', msg_create_user = msg_create_user,roles = roles, country= country, docs= docs,json_city=json_city)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        
        token_verified = request.args.get('token_verified')

        if not token_verified :
            return jsonify({'message': 'Missing token'}),403

        try:
            data = jwt.decode(token_verified, app.config['SECRET_KEY'])
            
        except:
            return jsonify({'message': 'Invalid token'}),403

        else:
            update_verified_user(token_verified) 

        return f(*args, **kwargs)

    return decorated

@app.route('/verification_email', methods=['GET'])
@token_required
def verification_email():
    msg_user= 'Usuario validado exitosamente!'
    msg_content = 'Registro completado, ingresa con tu usuario y contraseña y tendrás acceso a nuestra plataforma '
    return render_template('pages/login.html',msg_user=msg_user, msg_content=msg_content)


# Editar usuario en la organización
@app.route('/edit_users/<user_id>' )
def edit_users(user_id):
    list_user = list_user_data_edit(user_id,session['organization_id'])
    roles = selec_users_roles(user_id,session['organization_id'])
    country = select_country()
    docs = select_docs() 
    citys = select_city(list_user[0][12])
    city = citys[0][0]
    json_city = json.loads(city)
    
    return render_template('pages/edit_users.html',roles = roles, country= country, docs= docs, json_city=json_city, list_user= list_user)

# Actualizar usuario en la organización

@app.route('/update_user',methods=['POST'] )
def update_user():

    user_id = request.form['user_id']
    profile_photo = request.files['profile_photo']
    profile_photo_user = request.form['profile_photo_user']
    first_name = request.form['first_name']
    second_name = request.form['second_name']
    first_surname = request.form['first_surname']
    second_surname = request.form['second_surname']
    doc_type_id  = request.form['doc_type_id']
    num_doc = request.form['num_doc']
    gender = request.form['gender']
    city_id = request.form['city_id']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    roles_user = request.form.getlist('roles[]')
    verified = request.form['verified']
    approved = request.form['approved']
    
    if profile_photo.content_type == 'application/octet-stream':
        if profile_photo_user =='None':
            profile_photos = None 
        else:
            profile_photos = profile_photo_user
    else:
        if profile_photo_user =='None':
            image_name = save_image(profile_photo,'profile_photo')
            profile_photos = '/static/images/profile_photo/'+image_name+'.png'  
        else:
            os.remove('.'+profile_photo_user)
            image_name = save_image(profile_photo,'profile_photo')
            profile_photos = '/static/images/profile_photo/'+image_name+'.png'       

    roless = tuple(int(x) for x in roles_user) 
    update_data = update_data_user(user_id,profile_photos,first_name,second_name,first_surname,second_surname,doc_type_id,num_doc,gender,city_id,email,phone,address,verified)

    list_user = list_user_data_edit(user_id,session['organization_id'])
    roles = selec_users_roles(user_id,session['organization_id'])
    country = select_country()
    docs = select_docs() 
    citys = select_city(list_user[0][12])
    city = citys[0][0]
    json_city = json.loads(city)

    if (update_data == 'update'):

        disable_roles_users_organizations(session['organization_id'],user_id,roless)
        insert_roles_users_organizations(session['organization_id'],user_id,roless)
        update_user_organizations(approved,user_id,session['organization_id'])
        roles = selec_users_roles(user_id,session['organization_id'])
  
        return render_template('pages/edit_users_validate.html',roles = roles, country= country, docs= docs, json_city=json_city, list_user= list_user )
    
    else :
    
        return render_template('pages/edit_users.html', msg_create_user = 'error', roles = roles, country= country, docs= docs, json_city=json_city, list_user= list_user)

# Listar usuario de la organización   
  
@app.route('/admin_users')
def admin_users():

    all_users = admin_users_organizations()
    
    return render_template('pages/admin_users.html',all_users=all_users)    


# Crear usuario Super Admin 

@app.route('/admin_create_users')
def admin_create_users():
    roles = select_roles()
    country = select_country()
    docs = select_docs()
    citys = select_city(1)
    city = citys[0][0]
    json_city = json.loads(city)

    return render_template('pages/admin_create_users.html',roles = roles, country= country, docs= docs, json_city=json_city)

# Insertar Usuario Super Admin

@app.route('/admin_insert_user_page',methods=['POST'])
def admin_insert_user_page():

    first_name = request.form['first_name']
    second_name = request.form['second_name']
    first_surname = request.form['first_surname']
    second_surname = request.form['second_surname']
    doc_type_id  = request.form['doc_type_id']
    num_doc = request.form['num_doc']
    gender = request.form['gender']
    city_id = request.form['city_id']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    profile_photo = request.files['profile_photo']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    country = select_country()
    docs = select_docs() 
    citys = select_city(1)
    city = citys[0][0]
    json_city = json.loads(city)

    if password == confirm_password:

        if profile_photo.content_type == 'application/octet-stream':
            profile_photos = None
        else:
            profile_photos = save_image(profile_photo,'profile_photo')
            profile_photos= '/static/images/profile_photo/'+profile_photos+'.png'

        token_validation = jwt.encode({'user': email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(seconds=3600)}, app.config['SECRET_KEY'])
        token_validation = token_validation.decode('UTF-8')

        assign_data = insert_user(first_name,second_name,first_surname,second_surname,doc_type_id,num_doc,gender,city_id,email,phone,address,profile_photos,password,token_validation)

        if (assign_data == 'exists'): 

            msg_create_user ='Verifica el correo electrónico, número de celular o número de documento del usuario, ya que uno de estos datos se encuentran registrado en el sistema.'

            return render_template('pages/create_users.html', msg_create_user = msg_create_user, country= country, docs= docs, json_city=json_city)    

        else:
            
            msg = Message ( 'Gracias por tu registro!', 
                             sender = app.config['MAIL_USERNAME'],
                             recipients = [email] )

            msg.html = render_template('pages/email.html', user = first_name + " " + second_name, token_validation = token_validation)
            mail.send(msg)

            list_user = admin_list_user_data_edit(assign_data[0][0])
            insert_users_organizations(1,assign_data[0][0])
            insert_roles_organization_demo(assign_data[0][0])
            country = select_country()
            docs = select_docs() 
            citys = select_city(list_user[0][12])
            city = citys[0][0]
            json_city = json.loads(city)

            msg_title ='Usuario creado exitosamente!'
            msg_user='Verifica tu correo electrónico en la bandeja de entrada, SPAN o correo no deseado y continua con el registro.'
   
            return render_template('pages/admin_edit_users.html',msg_type='created', msg_title= msg_title, msg_user = msg_user, list_user = list_user, country= country, docs= docs, json_city=json_city)  

    else:
        
        msg_create_user ='La contraseñas no coiciden, llena el formulario nuevamente y verifica estos campos.'

        return render_template('pages/create_users.html', msg_create_user = msg_create_user,country= country, docs= docs,json_city=json_city) 


# Editar usuarios Super Admin

@app.route('/standar_edit_users/<user_id>' )
def standar_edit_users(user_id):

    list_user = admin_list_user_data_edit(user_id)
    assign_org = list_remaining_users_organizations(user_id)
    list_user_org= selec_roles_users_organizations(user_id)
    roles = select_roles()
    country = select_country()
    docs = select_docs() 
    citys = select_city(list_user[0][12])
    city = citys[0][0]
    json_city = json.loads(city)

    if session['type'] =='A':

        return render_template('pages/admin_edit_users.html', country= country, docs= docs, json_city=json_city, list_user= list_user, roles=roles, assign_org=assign_org, list_user_org=list_user_org)
    
    else:
        
        return render_template('pages/standar_edit_users.html', country= country, docs= docs, json_city=json_city, list_user= list_user, roles=roles, assign_org=assign_org, list_user_org=list_user_org)

        
# Actualizar usuario en la organización

@app.route('/standar_update_user',methods=['POST'])
def standar_update_user():

    profile_photo = request.files['profile_photo']
    profile_photo_user = request.form['profile_photo_user']
    user_id = request.form['user_id']
    first_name = request.form['first_name']
    second_name = request.form['second_name']
    first_surname = request.form['first_surname']
    second_surname = request.form['second_surname']
    doc_type_id  = request.form['doc_type_id']
    num_doc = request.form['num_doc']
    gender = request.form['gender']
    city_id = request.form['city_id']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    verified = request.form['verified']
    
    if profile_photo.content_type == 'application/octet-stream':
        if profile_photo_user =='None':
            profile_photos = None 
        else:
            profile_photos = profile_photo_user
    else:
        if profile_photo_user =='None':
            image_name = save_image(profile_photo,'profile_photo')
            profile_photos = '/static/images/profile_photo/'+image_name+'.png'  
        else:
            os.remove('.'+profile_photo_user)
            image_name = save_image(profile_photo,'profile_photo')
            profile_photos = '/static/images/profile_photo/'+image_name+'.png'       

    update_data = update_data_user(user_id,profile_photos,first_name,second_name,first_surname,second_surname,doc_type_id,num_doc,gender,city_id,email,phone,address,verified)

    list_user = admin_list_user_data_edit(user_id)
    assign_org = list_remaining_users_organizations(user_id)
    list_user_org= selec_roles_users_organizations(user_id)
    roles = select_roles()
    country = select_country()
    docs = select_docs() 
    citys = select_city(list_user[0][12])
    city = citys[0][0]
    json_city = json.loads(city)
    

    if (update_data == 'update'):
          
        msg_title ='Usuario actualizado exitosamente!!'
        msg_user='Verifica que datos del usuario esten atulizados correctamente.'

        if session['type'] =='A':

            return render_template('pages/admin_edit_users.html', msg_type='created', msg_title= msg_title, msg_user = msg_user, country= country, docs= docs, json_city=json_city, list_user= list_user, roles=roles, assign_org=assign_org, list_user_org=list_user_org) 
        
        else:

             return render_template('pages/standar_validate_edit_users.html', msg_type='created', msg_title= msg_title, msg_user = msg_user, country= country, docs= docs, json_city=json_city, list_user= list_user, roles=roles, assign_org=assign_org, list_user_org=list_user_org) 
        
    else :

        if session['type'] =='A':

            return render_template('pages/admin_edit_users.html', msg_error='error', country= country, docs= docs, json_city=json_city, list_user= list_user, roles=roles, assign_org=assign_org, list_user_org=list_user_org) 

        else:

            return render_template('pages/standar_edit_users.html', msg_error='error', country= country, docs= docs, json_city=json_city, list_user= list_user, roles=roles, assign_org=assign_org, list_user_org=list_user_org) 

# Agregar organizaciones al usuario super admin

@app.route('/insert_user_org',methods=['POST'] )
def insert_user_org():

    organization_id = request.form['organization_id']
    user_id = request.form['user_id']
    roles_user = request.form.getlist('roles[]')

    roles = tuple(int(x) for x in roles_user) 

    insert_users_organizations(organization_id,user_id)
    insert_roles_users_organizations(organization_id,user_id,roles)
  

    list_user = admin_list_user_data_edit(user_id)
    assign_org = list_remaining_users_organizations(user_id)
    list_user_org= selec_roles_users_organizations(user_id)
    roles = select_roles()
    country = select_country()
    docs = select_docs() 
    citys = select_city(list_user[0][12])
    city = citys[0][0]
    json_city = json.loads(city)

    msg_title ='Organización agregada exitosamente!!'
    msg_user='Verifica que organizacion y roles asignados esten correctament'
    
    return render_template('pages/admin_edit_users.html',msg_type='update_role_user', msg_title= msg_title, msg_user = msg_user, country= country, docs= docs, json_city=json_city, list_user= list_user, roles=roles, assign_org=assign_org, list_user_org=list_user_org)


# Actualizar roles del usuario super admin

@app.route('/update_role_user',methods=['POST'] )
def update_role_user():

    organization_id = request.form['organization_id']
    user_id = request.form['user_id']
    roles_user = request.form.getlist('roles[]')

    roles = tuple(int(x) for x in roles_user) 

    insert_roles_users_organizations(organization_id,user_id,roles)
    disable_roles_users_organizations(organization_id,user_id,roles)

    list_user = admin_list_user_data_edit(user_id)
    assign_org = list_remaining_users_organizations(user_id)
    list_user_org= selec_roles_users_organizations(user_id)
    roles = select_roles()
    country = select_country()
    docs = select_docs() 
    citys = select_city(list_user[0][12])
    city = citys[0][0]
    json_city = json.loads(city)

    msg_title ='Usuario actualizado exitosamente!!'
    msg_user='Verifica que roles del usuario esten atulizados correctamente.'
    
    return render_template('pages/admin_edit_users.html',msg_type='update_role_user', msg_title= msg_title, msg_user = msg_user, country= country, docs= docs, json_city=json_city, list_user= list_user, roles=roles, assign_org=assign_org, list_user_org=list_user_org)

# Habiltar o desabiltar usuario en una organización 

@app.route('/update_user_org/<approved>/<user_id>/<organization_id>' )
def update_user_org(approved,user_id,organization_id):

    update_user_organizations(approved,user_id,organization_id)

    list_user = admin_list_user_data_edit(user_id)
    assign_org = list_remaining_users_organizations(user_id)
    list_user_org= selec_roles_users_organizations(user_id)
    roles = select_roles()
    country = select_country()
    docs = select_docs() 
    citys = select_city(list_user[0][12])
    city = citys[0][0]
    json_city = json.loads(city)
    
    msg_title ='Organizaciones actualizadas exitosamente!!'

    if approved == '1':

        msg_user='Se habalito la organización al usuario de manera correcta.'
    else :

        msg_user='Se deshabilito la organización al usuario de manera correcta.'
    
    return render_template('pages/admin_edit_users.html',msg_type='update_us_org',msg_title=msg_title, msg_user= msg_user, country= country, docs= docs, json_city=json_city, list_user= list_user, roles=roles, assign_org=assign_org, list_user_org=list_user_org)



# Listar organizaciones Super Admin
@app.route('/organization')
def organization():
    
    list_organization = list_data_all_organizations()
    return render_template('pages/organization.html', list_organization = list_organization)  

# Crear organizaciones Super Admin
@app.route('/admin_create_organization')
def admin_create_organization():

    country = select_country()
    citys = select_city(1)
    city = citys[0][0]
    json_city = json.loads(city)  


    return render_template('pages/admin_create_organization.html', country= country, json_city=json_city)

# Insertar organizaciones Super Admin
@app.route('/insert_organization',methods=['POST'])
def insert_organization():

    name = request.form['name']
    email = request.form['email']
    website = request.form['website']
    phone = request.form['phone']
    addres = request.form['addres']
    organization_photo = request.files['organization_photo']
    legal_id = request.form['legal_id']
    city_id = request.form['city_id']

    if organization_photo.content_type == 'application/octet-stream':
        organization_photos = None
    else:
        image_name = save_image(organization_photo,'organization_photo')
        organization_photos = '/static/images/organization_photo/'+image_name+'.png'        

    assign_data = admin_create_organizations(name,email,website,phone,addres,organization_photos,legal_id,city_id)

    if assign_data == 'exists':

        country = select_country()
        citys = select_city(1)
        city = citys[0][0]
        json_city = json.loads(city)  

        return render_template('pages/admin_create_organization.html', msg_create = 'error', country= country, json_city=json_city)
    
    else :

        list_organization = list_data_organization(assign_data[0][0])

        country = select_country()
        citys = select_city(list_organization[0][7])
        city = citys[0][0]
        json_city = json.loads(city)

        list_model_crop = list_model_crop_organization(assign_data[0][0])

        allcrops = select_remaining_crops(assign_data[0][0])
        model_crops = organization_all_model_crops(allcrops[0][0])
        model_crop = model_crops[0][0]
        json_model_crop = json.loads(model_crop)

        msg_create_org ='Organización creada exitosamente!'
        msg_org ='Bienvenido ahora tendrás acceso a todos nuestros servicios, continua  el proceso y agrega los cultivos y  modelos a la organización.'

        return render_template('pages/admin_edit_organization.html', msg_type='created', msg_create_org = msg_create_org, msg_org =msg_org, country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)

# Editar organizaciones Super Admin      
@app.route('/admin_edit_organization/<organization_id>' )
def admin_edit_organization_(organization_id):

    list_organization = list_data_organization(organization_id)

    country = select_country()
    citys = select_city(list_organization[0][7])
    city = citys[0][0]
    json_city = json.loads(city)

    list_model_crop = list_model_crop_organization(organization_id)

    allcrops = select_remaining_crops(organization_id)
    model_crops = organization_all_model_crops(allcrops[0][0])
    model_crop = model_crops[0][0]
    json_model_crop = json.loads(model_crop)
    
    return render_template('pages/admin_edit_organization.html', country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)


# Actulizar organizaciones Super Admin

@app.route('/update_organization',methods=['POST'])
def update_organization():

    organization_id = request.form['organization_id']
    name = request.form['name']
    email = request.form['email']
    website = request.form['website']
    phone = request.form['phone']
    addres = request.form['addres']
    organization_photo = request.files['organization_photo']
    photo_previous = request.form['photo_previous']
    legal_id = request.form['legal_id']
    city_id = request.form['city_id']
    approved = request.form['approved']

    if organization_photo.content_type == 'application/octet-stream':
        if photo_previous =='None':
            organization_photos = None 
        else:
            organization_photos = photo_previous
    else:
        if photo_previous =='None':
            image_name = save_image(organization_photo,'organization_photo')
            organization_photos = '/static/images/organization_photo/'+image_name+'.png'  
        else:
            os.remove('.'+photo_previous)
            image_name = save_image(organization_photo,'organization_photo')
            organization_photos = '/static/images/organization_photo/'+image_name+'.png'        

    update_data = update_organization_data(organization_id, name, email, website, phone, addres, organization_photos, legal_id, city_id, approved)

    list_organization = list_data_organization(organization_id)

    country = select_country()
    citys = select_city(list_organization[0][7])
    city = citys[0][0]
    json_city = json.loads(city)

    list_model_crop = list_model_crop_organization(organization_id)

    allcrops = select_remaining_crops(organization_id)
    model_crops = organization_all_model_crops(allcrops[0][0])
    model_crop = model_crops[0][0]
    json_model_crop = json.loads(model_crop)
    

    if update_data == 'update':
    
        msg_create_org ='Datos actualizados exitosamente!'
        msg_org ='Verifica que los datos de la organización esten actualizados esten correctamente'

        if session['type'] =='A':    
            return render_template('pages/admin_edit_organization.html', msg_type='update', msg_create_org= msg_create_org, msg_org= msg_org, country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)
        else:
            return render_template('pages/edit_organization_validate.html', country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)

    else :
        
        return render_template('pages/admin_edit_organization.html', msg_create = 'error', country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)


# Insertar nuevos cultivos y modelos a la organización

@app.route('/insert_model_crop',methods=['POST'])
def insert_model_crop():

    organization_id = request.form['organization_id']
    crop_id = request.form['crop_id']
    model_crop = request.form.getlist('model_crop[]')

    model_crops = tuple(int(x) for x in model_crop) 

    insert_update_organization_crop(organization_id,crop_id)
    insert_organization_model_train(organization_id,model_crops)

    list_organization = list_data_organization(organization_id)
  

    country = select_country()
    citys = select_city(list_organization[0][7])
    city = citys[0][0]
    json_city = json.loads(city)

    list_model_crop = list_model_crop_organization(organization_id)

    allcrops = select_remaining_crops(organization_id)
    model_crops = organization_all_model_crops(allcrops[0][0])
    model_crop = model_crops[0][0]
    json_model_crop = json.loads(model_crop)

    msg_create_org ='Cultivos actualizados exitosamente!'
    msg_org ='Verifica que los datos de los cultivos y modelos esten actualizados esten correctamente'
    
    return render_template('pages/admin_edit_organization.html',msg_type='update_crop', msg_create_org= msg_create_org, msg_org= msg_org, country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)


# Actualizar cultivos y modelos a la organización

@app.route('/update_model_crop',methods=['POST'])
def update_model_crop():

    organization_id = request.form['organization_id']
    crop = request.form['crop']
    model_crop = request.form.getlist('model_crop[]')

    model_crops = tuple(int(x) for x in model_crop) 

    disable_organization_model_train(organization_id,crop,model_crops)
    insert_organization_model_train(organization_id,model_crops)

    list_organization = list_data_organization(organization_id)
  
    country = select_country()
    citys = select_city(list_organization[0][7])
    city = citys[0][0]
    json_city = json.loads(city)

    list_model_crop = list_model_crop_organization(organization_id)

    allcrops = select_remaining_crops(organization_id)
    model_crops = organization_all_model_crops(allcrops[0][0])
    model_crop = model_crops[0][0]
    json_model_crop = json.loads(model_crop)

    msg_create_org ='Cultivos actualizados exitosamente!'
    msg_org ='Verifica que los datos de los cultivos y modelos esten actualizados esten correctamente'
    
    return render_template('pages/admin_edit_organization.html',msg_type='update_crop', msg_create_org= msg_create_org, msg_org= msg_org, country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)


# Desabilitar cultivos y modelos a la organización

@app.route('/get_disable_crop/<organization_id>/<crop_id>')
def get_disable_crop(organization_id,crop_id):

    disable_crop_organization(organization_id,crop_id)

    list_organization = list_data_organization(organization_id)
  
    country = select_country()
    citys = select_city(list_organization[0][7])
    city = citys[0][0]
    json_city = json.loads(city)

    list_model_crop = list_model_crop_organization(organization_id)

    allcrops = select_remaining_crops(organization_id)
    model_crops = organization_all_model_crops(allcrops[0][0])
    model_crop = model_crops[0][0]
    json_model_crop = json.loads(model_crop)

    msg_create_org ='Cultivo deshabilitado exitosamente!'
    msg_org ='Verifica que los datos de los cultivos esten actualizados esten correctamente'
    
    return render_template('pages/admin_edit_organization.html',msg_type='update_crop', msg_create_org= msg_create_org, msg_org= msg_org, country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)

# Habilitar cultivos y modelos a la organización

@app.route('/get_enable_crop/<organization_id>/<crop_id>')
def get_enable_crop(organization_id,crop_id):

    enable_crop_organization(organization_id,crop_id)

    list_organization = list_data_organization(organization_id)
  
    country = select_country()
    citys = select_city(list_organization[0][7])
    city = citys[0][0]
    json_city = json.loads(city)

    list_model_crop = list_model_crop_organization(organization_id)

    allcrops = select_remaining_crops(organization_id)
    model_crops = organization_all_model_crops(allcrops[0][0])
    model_crop = model_crops[0][0]
    json_model_crop = json.loads(model_crop)

    msg_create_org ='Cultivo habilitado exitosamente!'
    msg_org ='Verifica que los datos de los cultivos esten actualizados esten correctamente'
    
    return render_template('pages/admin_edit_organization.html',msg_type='update_crop', msg_create_org= msg_create_org, msg_org= msg_org, country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)

# Editar organización 

@app.route('/edit_organization/<organization_id>' )
def edit_organization_(organization_id):

    list_organization = list_data_organization(organization_id)

    country = select_country()
    citys = select_city(list_organization[0][7])
    city = citys[0][0]
    json_city = json.loads(city)

    list_model_crop = list_model_crop_organization(organization_id)

    allcrops = select_remaining_crops(organization_id)
    model_crops = organization_all_model_crops(allcrops[0][0])
    model_crop = model_crops[0][0]
    json_model_crop = json.loads(model_crop)
    
    return render_template('pages/edit_organization.html', country= country, json_city=json_city, list_organization= list_organization, list_model_crop= list_model_crop , allcrops = allcrops, json_model_crop = json_model_crop)


# Calular etapa del cultivo de la organización

@app.route('/stages_crop')
def stages_crop():
    crops= organization_crops(session['organization_id'])
    model_crops=organization_model_crops(session['organization_id'],crops[0][0])
    model_crop = model_crops[0][0]
    json_crop= json.loads(model_crop)

    return render_template('pages/stages_crop.html', crops = crops, json_crop = json_crop) 

# Predecir etapa del cultivo de la organización

@app.route('/predict_stage', methods=['POST'])
def predict_stage():

    files = glob.glob('./static/images/stages_calculation/*.png')
    for f in files:
         os.remove(f)

    f1 = request.files['layer1']
    crop_id = request.form['crop_id']
    model_crop_id = request.form['model_crop_id']

    image_name=save_image(f1,'stages_calculation')
    model_weight = list_model_weight(model_crop_id)
    answer = predict_image(image_name,model_weight[0][0])
    stage = calculate_stage(session['organization_id'],model_crop_id,int(answer))

    return render_template('pages/predict_stage.html',stage = stage, image_name = image_name)  

# Insertar datos calculados en los histoircos del cultivo de la organización
    
@app.route('/insert_stage', methods=['POST'])
def insert_stage():

    stage_id = request.form['stage_id']
    image_url = request.form['image_url']
    notes = request.form['notes']

    if notes =='':
        notess = None
    else :
        notess = notes

    origin = './static/images/stages_calculation/'+image_url
    destiny = './static/images/stages_calculation/stages_crop/'+image_url
    shutil.copyfile(origin, destiny)
    
    insert_stage_attachments(image_url, stage_id, session['user_id'], notess, session['organization_id'])

    crops= organization_crops(session['organization_id'])
    model_crops=organization_model_crops(session['organization_id'],crops[0][0])
    model_crop = model_crops[0][0]
    json_crop= json.loads(model_crop)

    return render_template('pages/stages_crop.html', crops = crops, json_crop = json_crop) 

    
# Mostrar histoircos del cultivo de la organización


@app.route('/stage_attachments/')
def stage_attachments():
    
    list_stage= list_calculate_stage(session['organization_id'])
    return render_template('pages/stage_attachments.html',list_stage = list_stage)  
  

# Calular la humedad del terreno

@app.route('/humidity_ground')
def humidity_ground():

    return render_template('pages/humidity_ground.html')    


@app.route('/predict_humidity',methods=['POST'])
def predict_humidity():
    
    files = glob.glob('./static/images/humidity_calculation/*.png')
    for f in files:
         os.remove(f)

    f1 = request.files['layer1']

    image_name=save_image(f1,'humidity_calculation')
    humidity = humidity_calculation(image_name)

    return render_template('pages/predict_humidity.html',humidity= humidity, image_name = image_name)  


@app.route('/insert_humidity', methods=['POST'])
def insert_humidity():
    
    image_url = request.form['image_url']
    high_humidity = request.form['high_humidity']
    optimal_humidity = request.form['optimal_humidity']
    low_humidity = request.form['low_humidity']
    notes = request.form['notes']

    if notes =='':
        notess = None
    else :
        notess = notes

    origin = './static/images/humidity_calculation/'+image_url
    destiny = './static/images/humidity_calculation/humidity_crop/'+image_url
    shutil.copyfile(origin, destiny)
    
    insert_humidity_attachments(high_humidity, optimal_humidity, low_humidity, session['user_id'], notess, image_url, session['organization_id'])

    return render_template('pages/humidity_ground.html',msg_humidity = 'successful' ) 

@app.route('/humidity_attachments/')
def humidity_attachments():

    list_humidity = list_calculate_humidity(session['organization_id'])

    return render_template('pages/humidity_attachments.html',list_humidity = list_humidity ) 


@app.route('/health_calculation')
def health_calculation():

    return render_template('pages/health_calculation.html')    


@app.route('/predict_health',methods=['POST'])
def predict_health():
    
    files = glob.glob('./static/images/plant_health/*.png')
    for f in files:
         os.remove(f)

    f1 = request.files['layer1']

    img_name_user=save_image(f1,'plant_health')
    health = plant_health(img_name_user)
    plant_state = calculate_plant(health[3])

    return render_template('pages/predict_health.html', img_name_user = img_name_user, health=health, plant_state= plant_state)  


@app.route('/insert_health', methods=['POST'])
def insert_health():
    
    green = request.form['green']
    yellow = request.form['yellow']
    brown = request.form['brown']
    plant_state_id = request.form['plant_state_id']
    notes = request.form['notes']
    img_name_user = request.form['img_name_user']
    img_name_cal = request.form['img_name_cal']

    if notes =='':
        notess = None
    else :
        notess = notes
    
    origin = './static/images/plant_health/'+img_name_user
    destiny = './static/images/plant_health/health_crop/'+img_name_user
    shutil.copyfile(origin, destiny)

    origin_cal = './static/images/plant_health/'+img_name_cal
    destiny_cal = './static/images/plant_health/health_crop/'+img_name_cal
    shutil.copyfile(origin_cal, destiny_cal)
    
    insert_plant_attachments(green, yellow, brown, plant_state_id, session['user_id'], notess, img_name_user, img_name_cal, session['organization_id'])

    return render_template('pages/health_calculation.html',msg_plant = 'successful' ) 

@app.route('/health_attachments/')
def health_attachments():

    list_health = list_calculate_plant(session['organization_id'])

    return render_template('pages/health_attachments.html',list_health = list_health ) 

@app.route('/stages_calculation', methods=['POST'])
def stages_calculation():
    
    f2 = request.files['layer2']
    filename2 = secure_filename(f2.filename)
    f2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
    os.rename(os.path.join(app.config['UPLOAD_FOLDER'], filename2), os.path.join(app.config['UPLOAD_FOLDER'], 'layer5.tiff'))

    selected_checkbox = request.form.get('selected_checkbox')
    
    if selected_checkbox == 'ndvi':

        f1 = request.files['layer1']
        filename1 = secure_filename(f1.filename)
        f1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename1))
        os.rename(os.path.join(app.config['UPLOAD_FOLDER'], filename1), os.path.join(app.config['UPLOAD_FOLDER'], 'layer4.tiff'))
      
        humidily_ndvi()
        
        file = os.path.join(app.config['UPLOAD_FOLDER'], 'NDVI_Image.tiff')
        return send_file(file, as_attachment=True)     

    if selected_checkbox == 'ndwi':

        f3 = request.files['layer3']
        filename3 = secure_filename(f3.filename)
        f3.save(os.path.join(app.config['UPLOAD_FOLDER'], filename3))
        os.rename(os.path.join(app.config['UPLOAD_FOLDER'], filename3), os.path.join(app.config['UPLOAD_FOLDER'], 'layer6.tiff'))
      
        humidily_ndwi()
        
        file = os.path.join(app.config['UPLOAD_FOLDER'], 'NDWI_Image.tiff')
        return send_file(file, as_attachment=True) 
        


if __name__ == '__main__':
    csrf.init_app(app)
    mail.init_app(app)

    app.run(debug=True, threaded=False)     