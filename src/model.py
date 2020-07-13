import psycopg2
import pprint
import sys
import conexion
from passlib.hash import sha256_crypt

con = conexion.con
cur = con.cursor()
execute = cur.execute


def select_organizations():
    
    select_organizations = """Select id, name from organizations order by name"""
    execute(select_organizations)

    return cur.fetchall()  

def select_roles():
    
    select_roles = """
            select 	r.id,
                    i.singular_txt 
            from 	roles r
            join 	internationalizations i on r."name" = i.msg_id 
            order 	by 2
       """
    execute(select_roles)

    return cur.fetchall()


def select_country():
    
    select_country = "Select id, name from country"
    execute(select_country)

    return cur.fetchall()

def select_city(country_id):
    
    select_city = """
            select  concat('[',array_to_string(array_agg(concat('{ "id":','"',id,'"',',','"name":','"',"name",'"','}')),','),']')
            from    city
            where   country_id = %s
        """
    execute(select_city,(country_id,))
  
    return cur.fetchall()     


def select_docs():
    
    select_docs = "Select id, name from docs_types where name not in ('NIT','RUT')"
    execute(select_docs)

    return cur.fetchall()  

def select_crops():
    
    select_crops = "Select id, name from crops order by name"
    execute(select_crops)

    return cur.fetchall()         


# Validar si un correo electronico esta registrado 

def select_email(email):

    select_email = """
            select 	u.id,
                    concat(u.first_name,' ', u.first_surname) as user,
                    u.email
            from 	users u 
            where 	u.email  = %s
        """
    execute(select_email,(email,))
    
    return cur.fetchall()

# Insertar nuevo usuario

# Insertar usuario

def insert_user(first_name,second_name,first_surname,second_surname,doc_type_id,num_doc,gender_id,city_id,email,phone,address,profile_photo,password,token_validation):

    select_validation_user = """
            select 	u.email,
                    u.phone,
                    u.verified 
            from 	users u 
            where   u.email  = %s or phone = %s or num_doc = %s 
        """
    execute(select_validation_user, (email,phone,num_doc))
    validation_user = cur.fetchall()

    if len(validation_user) > 0:

        return 'exists'

    else:

        hash_password = sha256_crypt.encrypt(password)
        first_names = first_name[0:1].upper() + first_name[1:len(first_name)].lower()
        second_names = second_name[0:1].upper() + second_name[1:len(second_name)].lower()
        first_surnames = first_surname[0:1].upper() + first_surname[1:len(first_surname)].lower()
        second_surnames = second_surname[0:1].upper() + second_surname[1:len(second_surname)].lower()

        insert_user_query = """
                INSERT INTO users
                (verified, inserted_at, updated_at, "type", first_name, second_name, first_surname, second_surname, doc_type_id, 
                num_doc, gender_id, city_id, email, phone, address, profile_photo, hash_password, token_validation)
                values (false,now(),now(),'C',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                returning id
            """
        execute(insert_user_query, (first_names,second_names,first_surnames,second_surnames,doc_type_id,num_doc,gender_id,city_id,email,phone,address,profile_photo,hash_password,token_validation))
        con.commit()

        return cur.fetchall()

# Insertar organización del usuario

def insert_users_organizations(organization_id,user_id):
      
    insert_users_organizations = """
                insert  into users_organizations (user_id ,organization_id , approved, inserted_at ,updated_at )
                select 	 %s, id, True, now(), now() 
                from 	organizations  
                where 	id  in (1,%s);
                
            """
    execute(insert_users_organizations,(user_id,organization_id))
    con.commit() 


# Insertar roles del usuario

def insert_roles_organization_demo(user_id):
    insert_roles_organization_demo ="""
            insert  into roles_users_organizations (users_organization_id, role_id , inserted_at , updated_at ,approved)
                    select 	uo.id,
                            1,
                            now(),
                            now(),
                            true
                    from 	users_organizations uo
                    where	uo.user_id = %s
                    and 	uo.organization_id  = 1
        """
    execute(insert_roles_organization_demo,(user_id,))
    con.commit() 

def disable_roles_users_organizations(organization_id,user_id,roles):

    disable_roles_users_organizations = """
                update 	roles_users_organizations
                set 	approved = False,
                        updated_at = now() 
                where 	id in ( select 	ruo.id 
                                from 	roles_users_organizations ruo 
                                join 	users_organizations uo on ruo.users_organization_id  = uo.id 
                                where 	uo.organization_id = %s
                                and 	uo.user_id = %s
                                and     ruo.role_id not in %s)
                and     approved = true
        """
    execute(disable_roles_users_organizations,(organization_id,user_id,roles))
    con.commit() 

def insert_roles_users_organizations(organization_id,user_id,roles):

    for role in roles:

        select_roles_users_organizations ="""
                select 	ruo.id 
                from 	roles_users_organizations ruo 
                join 	users_organizations uo on ruo.users_organization_id  = uo.id 
                where 	uo.organization_id = %s
                and 	uo.user_id = %s
                and 	ruo.role_id = %s
            """
        execute(select_roles_users_organizations,(organization_id,user_id,role))
        validation = cur.fetchall()   
 
        if len(validation) >0:

            update_roles_users_organizations = """
                    update 	roles_users_organizations
                    set 	approved = true,
                            updated_at = now()  
                    where 	id = (	select 	ruo.id 
                                    from 	roles_users_organizations ruo 
                                    join 	users_organizations uo on ruo.users_organization_id  = uo.id 
                                    where 	uo.organization_id = %s
                                    and 	uo.user_id = %s
                                    and 	ruo.role_id = %s )
                    and     approved = false
                """
            execute(update_roles_users_organizations,(organization_id,user_id,role))
            con.commit() 

        else:
      
            insert_roles_users_organizations = """
                    insert into roles_users_organizations (users_organization_id, role_id , inserted_at , updated_at ,approved)
                    select 	uo.id,
                            %s,
                            now(),
                            now(),
                            true
                    from 	users_organizations uo
                    where	uo.user_id = %s
                    and 	uo.organization_id  = %s
                """
            execute(insert_roles_users_organizations,(role,user_id,organization_id))
            con.commit() 



# Confirmar usuario por correo electronico 

def update_verified_user(token_verified):

    update_verified_user = """
            update  users 
            set     verified = true 
            where   token_validation = %s 
        """
    execute(update_verified_user, (token_verified,))
    con.commit()


#Login de usuario        

def login_users(email,password):

    select_validation = """
            select 	u.id,
                    concat(u.first_name,' ', u.first_surname) as user_name,
                    u.hash_password,
                    o.id, 
                    o."name",
                    u.gender_id
            from 	users u 
            join 	users_organizations uo on u.id = uo.user_id 
            join 	organizations o on uo.organization_id  = o.id
            where 	u.email  = %s 
            and     verified = true
            and 	uo.approved = true
            and 	o.approved = true 
            order   by o.name
        """
    execute(select_validation,(email,))
    validation = cur.fetchall()
    
    if len(validation) > 0:
        if sha256_crypt.verify(password, validation[0][2]):

            return validation
        
        else:

            return 'error_pass' 
    else:

        validation = select_email(email)

        if len(validation) > 0:

            return 'no_verified' 

        else:

            return 'error_usu' 

# listar organizaciones del usuario para ingreso

def login_user_organization(user_id,organization_id):

    login_user_organization = """
            select 	u.id,
                    concat(u.first_name,' ', u.first_surname) as user_name,
                    profile_photo,
                    o.id, 
                    o."name",
                    array_to_string(array_agg(ruo.role_id) ,','),
                    u.type
            from 	users u 
            join 	users_organizations uo on u.id = uo.user_id 
            join 	organizations o on uo.organization_id  = o.id
            join 	roles_users_organizations ruo on uo.id = ruo.users_organization_id 
            where 	u.id  = %s 
            and     uo.organization_id = %s 
            and 	ruo.approved = true 
            group 	by 1,2,3,4,5
        """
    execute(login_user_organization,(user_id,organization_id))
    validation = cur.fetchall()

    if len(validation) > 0:
        return validation

    else:
        validation_super_admin = """
                select 	u.id,
                        concat(u.first_name,' ', u.first_surname) as user_name,
                        profile_photo,
                        o.id, 
                        o."name",
                        '',
                        u.type
                from 	users u 
                join 	users_organizations uo on u.id = uo.user_id 
                join 	organizations o on uo.organization_id  = o.id
                where 	u.id  = %s 
                and     uo.organization_id = %s 
            """
        execute(validation_super_admin,(user_id,organization_id))
        return cur.fetchall()

# Traer listado de todos los usuarios super admin   

def admin_users_organizations():

    admin_users_organizations ="""
            select 	u.id,
                    concat(u.first_name ,' ',u.second_name ,' ',first_surname ,' ', second_surname ) as user_name,
                    dt.doc_code ,
                    u.num_doc,
                    u.phone,
                    u.email,
                    u.verified ,
                    u.address,
                    concat(ci."name",', ',co."name") as city,
                    to_char(u.inserted_at , 'dd-mm-yyyy HH24:MI:SS'), 
                    to_char(u.updated_at , 'dd-mm-yyyy HH24:MI:SS')
            from 	users u 
            join 	docs_types dt on u.doc_type_id = dt.id
            join 	city ci on u.city_id = ci.id
            join 	country co on ci.country_id = co.id
			order   by 2
         """
    execute(admin_users_organizations)
    con.commit()

    return cur.fetchall()


# Traer listado de usuarios de una organizacion     

def users_organizations(organization_id):

    select_users_organizations ="""
            select 	usorg.*
			from (
			select 	u.id,
                    concat(u.first_name ,' ',u.second_name ,' ',first_surname ,' ', second_surname ) as user_name,
                    dt.doc_code ,
                    u.num_doc,
                    u.phone,
                    u.email,
                    u.verified ,
                    uo.approved,
                    u.address,
                    concat(ci."name",', ',co."name") as city,
                    array_to_string(array_agg(i.singular_txt),', ') as roles,
                    to_char(u.inserted_at , 'dd-mm-yyyy HH24:MI:SS'), 
                    to_char(u.updated_at , 'dd-mm-yyyy HH24:MI:SS')
            from 	users u 
            join 	docs_types dt on u.doc_type_id = dt.id
            join 	city ci on u.city_id = ci.id
            join 	country co on ci.country_id = co.id
            join 	users_organizations uo on u.id = uo.user_id 
            join 	roles_users_organizations  ruo on uo.id  =ruo.users_organization_id 
            join 	roles r on ruo.role_id = r.id
            join 	internationalizations i on r."name" = i.msg_id 	
            where 	uo.organization_id  = %s
            and 	ruo.approved = true
            group 	by 1,2,3,4,5,6,7,8,9,10,12,13
			union 	all
            select 	u.id,
                    concat(u.first_name ,' ',u.second_name ,' ',first_surname ,' ', second_surname ) as user_name,
                    dt.doc_code ,
                    u.num_doc,
                    u.phone,
                    u.email,
                    u.verified ,
                    uo.approved,
                    u.address,
                    concat(ci."name",', ',co."name") as city,
                    null,
                    to_char(u.inserted_at , 'dd-mm-yyyy HH24:MI:SS'), 
                    to_char(u.updated_at , 'dd-mm-yyyy HH24:MI:SS')
            from 	users_organizations uo  
            left 	join 	roles_users_organizations ruo on uo.id  = ruo.users_organization_id
            join 	users u on uo.user_id  = u.id
            join 	docs_types dt on u.doc_type_id = dt.id
            join 	city ci on u.city_id = ci.id
            join 	country co on ci.country_id = co.id
            where 	ruo.id is null
            and 	uo.organization_id = %s ) as usorg
            order 	by 2
         """
    execute(select_users_organizations,(organization_id,organization_id))
    con.commit()

    return cur.fetchall()

def selec_users_roles(user_id,organization_id):
    
    selec_users_roles ="""
           (    select 	r.id,
                        i.singular_txt,
                        2 as validation
                from 	roles r 
                join 	internationalizations i on r."name" = i.msg_id 
                left 	join (	select 	r.id
                                from 	users u
                                join 	users_organizations  uo on u.id = uo.user_id 
                                join 	roles_users_organizations ruo on uo.id = ruo.users_organization_id 
                                join	roles r on ruo.role_id  = r.id
                                where 	u.id = %s
                                and 	uo.organization_id =  %s
                                and     ruo.approved = True) as ru on r.id = ru.id
                where 	ru.id is null
                order by r."name")
                union all
                (select 	r.id,
                            i.singular_txt,
                            1 as validation        
                            from 	users u
                            join 	users_organizations  uo on u.id = uo.user_id 
                            join 	roles_users_organizations ruo on uo.id = ruo.users_organization_id 
                            join	roles r on ruo.role_id  = r.id
                            join 	internationalizations i on r."name" = i.msg_id 
                            where 	u.id = %s
                            and uo.organization_id  = %s  
                            and ruo.approved = True       
                order by 2)
        """
    execute(selec_users_roles,(user_id,organization_id,user_id,organization_id))
  
    return cur.fetchall()            

def admin_list_user_data_edit(user_id):
    admin_list_user_data_edit ="""
            select  u.id,
                    u.profile_photo,
                    u.first_name,
                    u.second_name,
                    u.first_surname,
                    u.second_surname,
                    u.gender_id,
                    u.email,
                    u.phone,
                    u.doc_type_id,
                    dt."name", 
                    u.num_doc,
                    co.id,
                    co.name,
                    ci.id,
                    ci.name,
                    u.address,
                    case 
                        when u.verified = True then 1
                        else 2
                    end as verified
            from 	users u 
            join 	docs_types dt on u.doc_type_id = dt.id 
            join 	city ci on u.city_id  = ci.id 
            join    country co on ci.country_id = co.id
         	where 	u.id = %s
        """
    execute(admin_list_user_data_edit,(user_id,))
    con.commit() 

    return cur.fetchall()    

def list_user_data_edit(user_id,organization_id):
    list_user_data_edit ="""
            select  u.id,
                    u.profile_photo,
                    u.first_name,
                    u.second_name,
                    u.first_surname,
                    u.second_surname,
                    u.gender_id,
                    u.email,
                    u.phone,
                    u.doc_type_id,
                    dt."name", 
                    u.num_doc,
                    co.id,
                    co.name,
                    ci.id,
                    ci.name,
                    u.address,
                    case 
                        when u.verified = True then 1
                        else 2
                    end as verified,
                    case 
                        when uo.approved = True then 1
                        else 2
                    end as approved
            from 	users u 
            join 	docs_types dt on u.doc_type_id = dt.id 
            join 	city ci on u.city_id  = ci.id 
            join    country co on ci.country_id = co.id
            join 	users_organizations  uo on u.id = uo.user_id 
         	where 	u.id = %s
            and 	uo.organization_id = %s
        """
    execute(list_user_data_edit,(user_id,organization_id))
    con.commit() 

    return cur.fetchall()

# Actulizar datos del usuario

def update_data_user(user_id,profile_photo,first_name,second_name,first_surname,second_surname,doc_type_id,num_doc,gender,city_id,email,phone,address,verified):

    select_validation_user = """
            select 	u.id,        
					u.email,
                    u.phone,
                    u.verified 
            from 	users u 
            where   (u.email  = %s or phone = %s or num_doc = %s)
            and     u.id not in (%s)
        """
    execute(select_validation_user, (email,phone,num_doc,user_id))
    validation_user = cur.fetchall()

    if len(validation_user) > 0:

        return 'exists'

    else:

        first_names = first_name[0:1].upper() + first_name[1:len(first_name)].lower()
        second_names = second_name[0:1].upper() + second_name[1:len(second_name)].lower()
        first_surnames = first_surname[0:1].upper() + first_surname[1:len(first_surname)].lower()
        second_surnames = second_surname[0:1].upper() + second_surname[1:len(second_surname)].lower()

        update_data_user ="""
                update 	users u
                set 	profile_photo = %s,
                        first_name  = %s,
                        second_name = %s,
                        first_surname = %s,
                        second_surname = %s,
                        doc_type_id = %s,
                        num_doc = %s,
                        gender_id = %s,
                        city_id = %s,
                        email = %s,
                        phone = %s,
                        address = %s,
                        verified =  case 
                                        when %s = 1 then True
                                        else False
                                    end,
                        updated_at = now()
                where 	id = %s
            """
        execute(update_data_user,(profile_photo,first_names,second_names,first_surnames,second_surnames,doc_type_id,num_doc,gender,city_id,email,phone,address,verified,user_id))
        con.commit()

        return 'update'


# Acttulizar el estado del usuario en la organización

def update_user_organizations(approved,user_id,organization_id):

    update_user_organizations = """
            update	users_organizations uo
            set 	approved = 	case 
                                    when %s = 1 then True
                                    else False
                                end
            where 	user_id = %s
            and 	organization_id = %s
        """
    execute(update_user_organizations,(approved,user_id,organization_id))
    con.commit()

# Listar organizaciones no asignadas al usuario

def list_remaining_users_organizations(user_id):

    list_remaining_users_organizations = """
            select 	o.id,
                    o."name" 
            from 	organizations o 
            left 	join (	select 	id,
                                    organization_id 
                            from	users_organizations 
                            where 	user_id = %s) as uo on o.id = uo.organization_id
            where 	uo.id is null
            order 	by o."name" 
        """
    execute(list_remaining_users_organizations,(user_id,))

    return cur.fetchall()

# listar organizaciones y roles del usuario super admin

def selec_roles_users_organizations(user_id):

    selec_roles_users_organizations ="""
            select 	ruo.id_o,
                    ruo."name",
                    ruo.approved_o, 
                    cast(concat('[',array_to_string(array_agg(concat('{ "id" : ','"',ruo.id,'"',',','"name" : ','"',ruo.singular_txt ,'" ,','"approved" : ','"',ruo.approved,'"','}')),','),']') as jsonb),
                    array_to_string(array_agg(case when ruo.approved = true then ruo.id end),',')
            from (	select 	o.id as id_o,
                            o."name",
                            uo.approved as approved_o, 
                            r.id,
                            i.singular_txt,
                            ruo.approved
                    from 	users_organizations uo 
                    join 	organizations  o on uo.organization_id  = o.id
                    left    join 	roles_users_organizations ruo on uo.id = ruo.users_organization_id 
                    left    join 	roles r on ruo.role_id = r.id
                    left    join 	internationalizations  i on r."name" = i.msg_id 
                    where 	uo.user_id = %s
                    order 	by  1,5) as ruo
            group 	by 1,2,3
            order 	by 2
        """
    execute(selec_roles_users_organizations,(user_id,))

    return cur.fetchall()

# Cambiar contraseña

# Insertar codigo de cambio de contraseña

def insert_code(user_id,code):
    
    insert_code = """
            insert into code_users (user_id,code,inserted_at)
            values (%s,%s,now())
        """
    execute(insert_code,(user_id,code))
    con.commit()

# Validar codigo de cambio de contraseña

def validation_code(code,user_id):
    
    validation_code = """
            select  user_id 
            from    code_users 
            where   code  = %s
            and     now()::TIMESTAMP - '5 min'::interval < inserted_at
            and 	inserted_at = (	select inserted_at  
            						from code_users 
									where inserted_at  = (	select max(inserted_at ) 
															from code_users  
															where user_id = %s))
        """
  
    execute(validation_code,(code,user_id))
    validation = cur.fetchall()

    return validation

# Actualizar contraseña

def change_password_user(user_id,change_password):

    hash_password = sha256_crypt.encrypt(change_password)
    
    change_password_user = """
            update 	users
            set 	hash_password  = %s
            where   id = %s
        """
    execute(change_password_user,(hash_password,user_id))
    con.commit()


