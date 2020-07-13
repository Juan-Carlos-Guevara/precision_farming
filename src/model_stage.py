import psycopg2
import pprint
import sys
import conexion


con = conexion.con
cur = con.cursor()
execute = cur.execute


# Listar cultivos por organizacion

def organization_crops(organization_id):
    
    organization_crops = """
            select 	c.id,
                    i.singular_txt 
            from 	organization_crop oc 
            join 	crops c on oc.crop_id  = c.id 
            join 	internationalizations  i on c."name" = i.msg_id 
            where 	oc.organization_id = %s
            and     approved = True
            order 	by 2
        """
    execute(organization_crops,(organization_id,))

    return cur.fetchall()

# Listar modelos del cultivo de la organizacion 

def organization_model_crops(organization_id,crop_id):
    
    organization_model_crops = """
            select 	concat('[',array_to_string(array_agg(concat('{ "id":','"',mo.id,'"',',','"name":','"',mo.singular_txt ,'"','}')),','),']')
            from  	(select mt.id,
                            i.singular_txt
                    from 	model_train mt 
                    join 	crop_model_train cmt on mt.id = cmt.model_train_id 
                    join 	organization_model_train omt on mt.id = omt.model_train_id 
                    join 	internationalizations  i on mt ."name" = i.msg_id 	
                    where 	omt.organization_id  = %s
                    and 	cmt.crop_id = %s
                    and     omt.approved = True
                    order 	by i.singular_txt) as mo
        """
  
    execute(organization_model_crops,(organization_id,crop_id))

    return cur.fetchall()

# Traer model y weight del modelo del cultivo

def list_model_weight(model_train_id):

    list_model_weight = """
            select 	json_name 
            from 	model_train mt 
            where 	id = %s
        """
    execute(list_model_weight,(model_train_id,))

    return cur.fetchall()

# Validar etapa del cultivo 

def calculate_stage(organization_id,model_train_id,answer):
    
    calculate_stage = """
            select 	s.id,
                    i.singular_txt ,
                    i.plural_txt
            from 	organization_model_train omt 
            join 	model_train mt on omt.model_train_id  = mt.id
            join 	stages s on mt.id  = s.model_train_id 
            join 	internationalizations  i on s."name" = i.msg_id 
            where 	omt.organization_id = %s
            and 	mt.id = %s
            and 	s."order"  = %s
        """
    execute(calculate_stage,(organization_id,model_train_id,answer))

    return cur.fetchall()

def insert_stage_attachments(image_url, stage_id, user_id, notes, organization_id):

    image_urls= '/static/images/stages_calculation/stages_crop/'+image_url

    insert_stage_attachments= """
            insert into stage_attachments (url, stage_id, inserted_at, user_id, notes, organization_id )
            values (%s,%s,now(),%s,%s,%s)
        """
    execute(insert_stage_attachments,(image_urls, stage_id, user_id, notes, organization_id))
    con.commit()


def list_calculate_stage(organization_id):

    list_calculate_stage = """
            select 	sa.id,
                    ic.singular_txt ,
                    imt.singular_txt ,
                    ist.singular_txt ,
                    ist.plural_txt,
                    concat(u.first_name ,' ',u.second_name ,' ',first_surname ,' ', second_surname ) as user_name,
                    to_char(sa.inserted_at, 'dd-mm-yyyy HH24:MI:SS'),
                    case 
                        when sa.notes is null then 'Sin comentarios'
                        else sa.notes 
                    end as note,
                    sa.url 
            from 	stage_attachments sa 
            join 	stages s on sa.stage_id = s.id
            join 	model_train mt on s.model_train_id  = mt.id 
            join 	crop_model_train cmt on mt.id  = cmt.model_train_id 
            join 	crops c on cmt.crop_id  = c.id
            join 	users u on sa.user_id =  u.id
            join 	internationalizations ic on c."name" = ic.msg_id 
            join 	internationalizations imt on mt."name" = imt.msg_id
            join 	internationalizations ist on s."name" = ist.msg_id
            where 	sa.organization_id = %s
            order   by sa.id
        """
    execute(list_calculate_stage,(organization_id,))

    return cur.fetchall()

def insert_humidity_attachments(high, optimal, low, user_id, notes, image_url, organization_id):

    image_urls= '/static/images/humidity_calculation/humidity_crop/'+image_url

    insert_humidity_attachments ="""
            INSERT INTO humidity_attachments
            (high, optimal, low, user_id, inserted_at, notes, url, organization_id)
            VALUES(%s, %s, %s, %s, now(), %s, %s, %s);
        """
    execute(insert_humidity_attachments,(high, optimal, low, user_id, notes, image_urls, organization_id))
    con.commit()
    

def list_calculate_humidity(organization_id):

    list_calculate_humidity="""
                select 	ha.id,
                        ha.high,
                        ha.optimal,
                        ha.low, 
                        concat(u.first_name ,' ',u.second_name ,' ',first_surname ,' ', second_surname ) as user_name,
                        ha.inserted_at,
                        case 
                            when ha.notes is null then 'Sin comentarios'
                            else ha.notes
                        end notes,
                        ha.url 
                from 	humidity_attachments ha 
                join 	users u on ha.user_id = u.id
                join 	organizations o on ha.organization_id = o.id
                where 	o.id = %s
                order   by ha.id
        """
    execute(list_calculate_humidity,(organization_id,))

    return cur.fetchall()


def calculate_plant(plant_id):

    select_calculate_plant ="""
                select 	ps.id,
                        i.singular_txt,
                        i.plural_txt 
                from 	plant_states ps 
                join 	internationalizations i on ps."name" = i.msg_id 
                where 	ps.id = %s
        """
    execute(select_calculate_plant,(plant_id,))

    return cur.fetchall()

def insert_plant_attachments(green, yellow, brown, plant_state_id, user_id, notes, url_user, url_calulate, organization_id):
    
    url_users= '/static/images/plant_health/health_crop/'+url_user
    url_calulates= '/static/images/plant_health/health_crop/'+url_calulate

    insert_plant_attachments =""" 
            INSERT INTO plant_attachments
            (green, yellow, brown, plant_state_id, user_id, inserted_at, notes, url_user, url_calulate, organization_id)
            VALUES(%s, %s, %s, %s, %s, now(), %s, %s, %s, %s);
        """
    execute(insert_plant_attachments,(green, yellow, brown, plant_state_id, user_id, notes, url_users, url_calulates, organization_id))
    con.commit()
    

def list_calculate_plant(organization_id):

    list_calculate_plant="""
                select 	pa.id,
                        pa.green,
                        pa.yellow,
                        pa.brown, 
                        i.singular_txt ,
                        i.plural_txt ,
                        concat(u.first_name ,' ',u.second_name ,' ',first_surname ,' ', second_surname ) as user_name,
                        pa.inserted_at ,
                        case 
                        when pa.notes is null then 'Sin comentarios'
                        else pa.notes
                        end notes,
                        pa.url_user,
                        pa.url_calulate
                from 	plant_attachments pa
                join 	plant_states ps on pa.plant_state_id = ps.id
                join 	users u on pa.user_id = u.id
                join 	organizations  o on pa.organization_id = o.id
                join 	internationalizations i on ps."name" = i.msg_id 
                where 	o.id = %s
                order   by  pa.id
        """
    execute(list_calculate_plant,(organization_id,))

    return cur.fetchall()

