import requests
import pandas as pd
import pymysql
import datetime

url1 = "https://pi.stiee.com/api/manager/util/encode?id="
headers = {
    'content-type': 'application/json',
}

conn_pi = pymysql.connect(host="192.168.0.236", user='dba', passwd='#', database='stiee_basic', port=3306,
                          use_unicode=True, charset="utf8", cursorclass=pymysql.cursors.DictCursor )

conn_pitest = pymysql.connect(host="101.43.47.152", user='dba', passwd='#', database='stiee_basic', port=60568,
                              use_unicode=True, charset="utf8")
def get_organization_encode(organization_id):
    url = url1+str(organization_id)
    resp = requests.get(url,headers=headers)
    encode_number = resp.json()
    return encode_number.get('extData')

def get_roleid(role_list):
    roleid_list = []
    for role_name in role_list:
        try:
            sql = "select id from member_role where name in (%s)" % role_name
            result_df = pd.read_sql(sql=sql, con=conn_pi)
            if len(result_df[0][0]) ==0:
                dict = {"id":int(result_df[0][0]),"role_name":role_name}
                roleid_dict.append(dict)
            else:
                print("角色： %s 不存在"%role_name)
        except:
            print( "角色 ： %s 获取失败"%role_name)
    return  roleid_list

def get_roleinfo(roleid_list):






if __name__ == '__main__':
    role_list =['职能部门','标准管理员','科技管理员','市场部批准','质量部部长','系统运维','板块财务经理','人力资源部部长','市场部评审']
    conn_pi = pymysql.connect(host="192.168.0.236", user='dba', passwd='#', database='stiee_basic', port=3306,
                              use_unicode=True, charset="utf8")

    conn_pitest = pymysql.connect(host="101.43.47.152", user='dba', passwd='#', database='stiee_basic', port=60568,
                                  use_unicode=True, charset="utf8")
    roleid_list =  get_roleid(role_list)


    conn_pi.close()
    conn_pitest
