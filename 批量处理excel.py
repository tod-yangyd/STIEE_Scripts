import json
import requests
import pandas as pd
import pymysql


url1 = "https://pi.stiee.com/api/manager/util/encode?id="
headers = {
    'content-type': 'application/json',
}

conn_prod=pymysql.connect(host="192.168.0.236",user='dba',passwd='#',database='stiee_basic',port=3306,use_unicode=True, charset="utf8")

def query_sql(sql):
    #open_conn()
    result_df = pd.read_sql(sql=sql,con=conn_prod)
    #conn_prod.close()
    #result = cursor.fetchall() 
    #close_conn()
    return result_df.values[0][0]





def read_excel(filename):
    df = pd.read_excel(filename,usecols=[0,1,2,3],sheet_name='Sheet2')
    #print (type(df))
    return df

def get_organization_id(organization):



    return 0

def get_organization_encode(organization_id):
    url = url1+str(organization_id)
    resp = requests.get(url,headers=headers)
    encode_number = resp.json()
    #str = "%s   %s"%(organization_id,encode_number.get('extData'))
    #print(encode_number.get('extData'))
    return encode_number.get('extData')


def get_data(dataframe):
    cols = dataframe.columns.tolist()
    sql=''
    error_namelist=''
    note=open('result.txt',mode='w')
    for col,row  in dataframe.iterrows():
        try:
            login_name = row['工号']
            real_name = row['姓名']
            name_sql = 'SELECT id FROM member_account where login_name ="%s" or real_name ="%s"'%(str(login_name),str(real_name))
            login_id = query_sql(name_sql)
            position = row['岗位类别']
            position_sql = 'SELECT id FROM member_position where name="%s"'%(str(position))
            position_id = query_sql(position_sql)
            organization = row['岗位管理范围(产品线或部门，多个用分号隔开）']
            organization_sql = 'SELECT id FROM member_organization where name="%s"'%(str(organization))
            organization_id =  query_sql(organization_sql)
            organization_id_encode = get_organization_encode(organization_id)
            organization_sp = "[{\"organizationId\":\"%s\",\"organizationName\":\"%s\"}]"%(organization_id_encode,organization)
            sql = "insert into member_account_position  (member_id,position_id,organization_ids,organization_sp,last_modifier,is_deleted,gmt_create,gmt_modified) VALUES('%s','%s','%s','%s','杨烨东','0','2023-03-16 16:07:46','2023-03-16 16:07:46'); \n"%(login_id,position_id,organization_id,organization_sp)
            note.writelines(sql)
        except:
            error_namelist = error_namelist+ str(login_name)+"\n"
        #docu = {k: v for k, v in zip(cols, vals)}
        #print(vals)
    """
    for login_name,position,organization in dataframe(columns=['工号','岗位类别','岗位管理范围(产品线或部门，多个用分号隔开）']):
        login_name = dataframe.columns[0]
        #name = dataframe.columns[1]
        position = dataframe.columns[2]
        organization = dataframe.columns[3]
    """
    print (error_namelist)
    return 0



if __name__ == '__main__':
    excel_data = read_excel("production.xls")
    get_data(excel_data)
    #print(sql)