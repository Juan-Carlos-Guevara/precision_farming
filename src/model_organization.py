import psycopg2
import pprint
import sys
import conexion


con = conexion.con
cur = con.cursor()
execute = cur.execute


# Crear organización Super Admin

def admin_create_organizations(name,email,website,phone,addres,organization_photo,legal_id,city_id):

    validation_organization = " select * from organizations where email = %s or phone = %s or legal_id = %s "
    execute(validation_organization,(email,phone,legal_id))
    validation = cur.fetchall()

    if len(validation) > 0:

        return 'exists'
    
    else :
        admin_create_organization = """
                insert into organizations
                (name, email, website, phone, addres, inserted_at, updated_at, image, legal_id, city_id)
                values(%s, %s, %s, %s, %s, now(), now(), %s, %s, %s)
                returning id
            """
        execute(admin_create_organization,(name,email,website,phone,addres,organization_photo,legal_id,city_id))
        con.commit()

        return cur.fetchall()

# insertar nuevos cultivos y modelos a la organizacion 

def insert_update_organization_crop(organization_id,crop_id):

    insert_update_organization_crop="""
                INSERT INTO organization_crop
                (organization_id, crop_id, approved, inserted_at, updated_at)
                select 	%s, id, true, now(), now()
                from 	crops 
                where 	id = %s
        """
    execute(insert_update_organization_crop,(organization_id,crop_id))
    con.commit()
    
# asignar modelos del cultivos a la organizacion Super Admin


def disable_organization_model_train(organization_id,crop,model_crops):
    
    disable_organization_model_train = """
            update 	organization_model_train
            set     approved = false,
                    updated_at = now()
            where 	organization_id = %s
            and 	model_train_id in ( select  model_train_id 
                                        from    crop_model_train  
                                        where   crop_id = %s
                                        and     model_train_id not in %s)
            and     approved = true
        """
    execute(disable_organization_model_train,(organization_id,crop,model_crops))
    con.commit() 

def insert_organization_model_train(organization_id, model_crops):

    for model_crop in model_crops:

        select_organization_model_train = """
                    select 	id 
                    from 	organization_model_train 
                    where 	organization_id  = %s
                    and 	model_train_id = %s
            """
        execute(select_organization_model_train,(organization_id,model_crop))
        validation_model_train = cur.fetchall()
    
        if  len(validation_model_train) > 0 :
            
            update_organization_model_train = """ 
                        update 	organization_model_train  
                        set 	approved = True,
                                updated_at = now() 
                        where 	organization_id  = %s
                        and 	model_train_id = %s
                        and     approved = false
                """
            execute(update_organization_model_train,(organization_id,model_crop))
            con.commit()

        else:    
            insert_organization_model_train = """
                        INSERT INTO organization_model_train
                        (organization_id, model_train_id, patent, approved, inserted_at, updated_at)
                        select %s, id, false, true, now(), now() from model_train mt 
                        where id = %s
                """
            execute(insert_organization_model_train,(organization_id,model_crop))
            con.commit()

# Listar datos de la organización Super Admin

def list_data_organization(organization_id):

    list_data_organization = """
            select 	o.id,
                    o.image ,
                    o."name" ,
                    o.legal_id ,
                    o.email ,
                    o.website ,
                    o.phone ,
                    co.id,
                    co.name,
                    ci.id,
                    ci.name,
                    o.addres,
                    case 
                        when o.approved = True then 1
                        else 2
                    end  as approved
            from 	organizations o 
            join    city ci on o.city_id = ci.id
            join    country co on ci.country_id = co.id
            where 	o.id = %s
        """
    execute(list_data_organization,(organization_id,))

    return cur.fetchall()


# listar Cultivo y modelos de la organización Super Admin 

def list_model_crop_organization(organization_id):

    list_model_crop_organization = """
                select 	corg.id,
                        corg.singular_txt,
                        corg.approved,
                        cast(concat('[',array_to_string(array_agg(concat('{ "id" : ','"',omodel.idm,'"',',','"name" : ','"',omodel.singular_txt ,'" ,','"approved" : ','"',omodel.approved,'"','}')),','),']') as jsonb)
                from (	select 	c.id,
                                i.singular_txt,
                                oc.approved 
                        from 	organization_crop oc 
                        join 	crops c on oc.crop_id  = c.id 
                        join 	internationalizations i on c."name" = i.msg_id 
                        where 	oc.organization_id = %s) as corg  
                join (	select	omodel.idc ,
                                omodel.idm ,
                                omodel.singular_txt,
                                omodel.approved
                        from    (  select 	c.id as idc,
                                            mt.id as idm,
                                            i.singular_txt,
                                            omt.approved
                                    from 	organization_model_train omt 
                                    join 	model_train mt on omt.model_train_id  = mt.id 
                                    join 	crop_model_train cmt on cmt.model_train_id = mt.id 
                                    join 	crops c on cmt.crop_id = c.id
                                    join 	internationalizations i on mt."name" = i.msg_id 
                                    where 	omt.organization_id = %s
                                    union all
                                    select 	cmt.crop_id ,
                                            mt.id,
                                            i.singular_txt,
                                            false
                                    from 	model_train mt 
                                    join 	crop_model_train cmt on mt.id = cmt.model_train_id 
                                    join 	internationalizations i on mt."name" = i.msg_id 
                                    left 	join (select	mt.id
                                                from 		organization_model_train omt
                                                join 		model_train mt on omt.model_train_id  = mt.id
                                                join 		crop_model_train cmt on cmt.model_train_id = mt.id 
                                                join 		crops c on cmt.crop_id = c.id
                                                where 	omt.organization_id = %s) as orgmt on mt.id = orgmt.id
                                    where 	orgmt.id is null  ) as omodel 
                                    order   by 3 ) as omodel on corg.id = omodel.idc
                group 	by 1,2,3
                order 	by 2
        """
    execute(list_model_crop_organization,(organization_id,organization_id,organization_id))

    return cur.fetchall()

def select_remaining_crops(organization_id):
    
    select_remaining_crops= """
                select 	c.id ,
                        i.singular_txt 
                from	crops c
                join 	internationalizations  i on c."name" = i.msg_id 
                left 	join  (	select 	oc.crop_id 
                                from	organization_crop oc 
                                join 	crops c on oc.crop_id  = c.id 
                                where 	oc.organization_id = %s) as oc on c.id = oc.crop_id
                where 	oc.crop_id is null
                order 	by i.singular_txt 
        """
    execute(select_remaining_crops,(organization_id,))

    return cur.fetchall()


# Listar modelos de los cultivos 

def organization_all_model_crops(crop_id):
    
    organization_all_model_crops = """
            select 	concat('[',array_to_string(array_agg(concat('{ "id":','"',mc.id,'"',',','"name":','"',mc.singular_txt ,'"','}')),','),']')
            from 	
            (select mt.id,
                    i.singular_txt
            from 	crop_model_train cmt 
            join 	model_train mt on cmt.model_train_id = mt.id 
            join 	internationalizations i on mt."name" = i.msg_id 
            where 	cmt.crop_id = %s
            order 	by i.singular_txt ) as mc
        """
  
    execute(organization_all_model_crops,(crop_id,))

    return cur.fetchall()

# Listar datos de la organización Super Amdmin

def list_data_all_organizations():
    
    list_data_all_organizations = """
            select 	o.id	,
                    o."name" ,
                    o.legal_id ,
                    o.email ,
                    o.phone ,
                    o.approved, 
                    o.addres ,
                    ci.name,
                    co.name ,
                    o.website,
                    array_to_string(array_agg(i.singular_txt ),', ')
            from 	organizations o 
            join    city ci on o.city_id = ci.id
            join    country co on ci.country_id = co.id
            left    join 	organization_crop oc on o.id = oc.organization_id 
            left    join 	crops c on oc.crop_id = c.id
            left join 	internationalizations  i on c."name" = i.msg_id 
            group 	by 1,2,3,4,5,6,7,8,9,10
        """
    execute(list_data_all_organizations)

    return cur.fetchall()

# Actualizar organizacion Super Amdmin

def update_organization_data(organization_id, name, email, website, phone, addres, organization_photos, legal_id, city_id, approved):

    validation_organization = """ 
            select  * 
            from    organizations 
            where   (email = %s or phone = %s or legal_id = %s) 
            and     id not in (%s)
        """
    execute(validation_organization,(email,phone,legal_id,organization_id))
    validation = cur.fetchall()

    if len(validation) > 0:

        return 'exists'

    else :
        
        update_organization_data= """
                update 	organizations 
                set 	"name" = %s,
                        email = %s,
                        website  = %s,
                        phone  = %s,
                        addres  = %s,
                        updated_at  = now(),
                        image  = %s,
                        legal_id = %s,
                        city_id = %s, 
                        approved =    case 
                                            when %s = 1 then True
                                            else False
                                        end 
                where 	id = %s
            """
        execute(update_organization_data,(name, email, website, phone, addres, organization_photos, legal_id, city_id, approved,organization_id))
        con.commit()

        return 'update'


def disable_crop_organization(organization_id,crop_id):
    
    disable_crop_organization = """
            update 	organization_crop
            set     approved = false
            where 	organization_id = %s
            and     crop_id =  %s
        """
    execute(disable_crop_organization,(organization_id,crop_id))
    con.commit() 

def enable_crop_organization(organization_id,crop_id):
    
    enable_crop_organization = """
            update 	organization_crop
            set     approved = true
            where 	organization_id = %s
            and     crop_id =  %s  
        """
    execute(enable_crop_organization,(organization_id,crop_id))
    con.commit() 


def crops_organization(organization_id):

    crops_organization = """
            select	c.id,
                    i.singular_txt ,
                    array_to_string(array_agg(imt.singular_txt ),','),
                    c.description		 
            from 	organization_model_train omt 
            join 	model_train mt on omt.model_train_id = mt.id
            join 	crop_model_train cmt on mt.id = cmt.model_train_id 
            join 	crops c on cmt.crop_id = c.id
            join 	internationalizations i on c."name" = i.msg_id 
            join 	internationalizations imt on mt."name" = imt.msg_id 
            where 	omt.organization_id = %s
            and 	omt.approved = true
            group 	by 1,2,4
        """   
    execute(crops_organization,(organization_id,))

    return cur.fetchall()


def crops_model_organization(crop_id,organization_id):

    crops_model_organization="""
            select	cr_smt.id,
                    cr_smt.model,
                    cast(concat('[',array_to_string(array_agg(concat('{ "stage":','"',cr_smt.singular_txt,'"',',','"description":','"',cr_smt.plural_txt  ,'"','}')),','),']') as json)
            from (	select 	mt.id,
                            i.singular_txt as model,
                            s."order", 
                            ist.singular_txt,
                            ist.plural_txt
                    from 	crops c
                    join 	crop_model_train cmt on c.id = crop_id 
                    join 	model_train mt on cmt.model_train_id  = mt.id 
                    left 	join 	stages s on mt.id = s.model_train_id 
                    left 	join 	internationalizations i on mt."name" = i.msg_id 
                    left 	join 	internationalizations ist on s."name"  = ist.msg_id 
                    where 	c.id = %s
                    and 	mt.id in (	select 	omt.model_train_id 
                                        from 	organization_model_train omt
                                        where 	omt.organization_id = %s
                                        and 	omt.approved=true ) 
                    order 	by 2,3) as cr_smt
            group 	by 1,2
            order	by 2
        """   
    execute(crops_model_organization,(crop_id,organization_id))

    return cur.fetchall()
