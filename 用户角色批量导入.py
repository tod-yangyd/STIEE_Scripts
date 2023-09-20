import requests
import pandas as pd
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder
import pymysql
import datetime
import json

class Mysql_Connection:
    def __init__(self, db_address, db_user, db_password):
        self.db = 'stiee_basic'
        self.host = db_address.split(":")[0]
        port = int(db_address.split(":")[1])
        self.con = pymysql.connect(host=self.host, user=db_user, passwd=db_password, database=self.db, port=port,
                                    use_unicode=True, charset="utf8")
        # conn_pi = create_engine(
        #     'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8' % (self.db_user, db_password, host, port, self.db))
        # self.con = conn_pi.connect()

    def close(self):
        self.con.close()

    def querysql(self, sql):
        result_df = pd.read_sql(sql=sql, con=self.con)
        return result_df


    def encode_number(self,number):
        url1 = "https://pi.stiee.com/api/manager/util/encode?id="
        headers = {
            'content-type': 'application/json',
        }
        url = url1 + str(number)
        resp = requests.get(url, headers=headers)
        encode_number = resp.json()
        return encode_number.get('extData')

    def get_role_info(self, role_list):
        roleinfo_list = []

        for role_name in role_list:
            sql1 = "select id from member_role where name in ('%s') and is_deleted=0" % role_name
            result_df = self.querysql(sql1)
            try:
                role_id = result_df.at[0, 'id']
            except Exception as e:
                print("角色 ： %s 在地址：%s 不存在" % (role_name,self.host))
            else:
                try:
                    sql2 = "select c.real_name ,b.name ,a.organization_id  from   member_account_role a  \
                                          left join member_role b on a.role_id = b.id \
                                          left join member_account c on a.member_id = c.id\
                                          where  (a.organization_id <>0 or a.organization_id is not null) \
                                           and role_id in (%d) " % role_id
                    result_df2 = self.querysql(sql2)
                    for idx, data in result_df2.iterrows():
                        org_id_list = data['organization_id'].split(",")
                        org_sp_name_list = []
                        for org_id in org_id_list:
                            sql3 = "select name from member_organization where id= '%s'" % org_id
                            result_df = self.querysql(sql3)
                            org_name = result_df.at[0, 'name']
                            org_sp_name_list.append(org_name)
                        role_info = {"member_name": data['real_name'], "org_sp_name_list": org_sp_name_list,
                                      "role_name": data['name']}

                        roleinfo_list.append(role_info)
                except Exception as e:
                    print("角色 ： %s 获取角色信息失败，失败原因：%s,失败行号： %s" % (role_name, e, e.__traceback__.tb_lineno))
        print ("###########获取角色信息完成####################")
        return roleinfo_list

    def trans_org(self,roleinfo_list):
        for role_info in roleinfo_list:
            org_sp_name_list = role_info['org_sp_name_list']
            role_name = role_info['role_name']
            try:
                query_name = "select id,name from member_role  where name='%s' and is_deleted=0" % role_name
                result_df = self.querysql(query_name)
                role_id = result_df.at[0, 'id']
            except Exception as e:
                print("角色：%s在地址：%s 获取信息失败，失败原因：%s" % (role_name, self.host, e))
            else:
                org_sp = {}
                for org_sp_name in org_sp_name_list:
                    sql = "select id,name from member_organization where is_deleted =0 and name = '%s'" % org_sp_name
                    result_df = self.querysql(sql)
                    try:
                        org_id_encode = self.encode_number(result_df.at[0, 'id'])
                    except Exception as e:
                        print("组织：%s 在地址：%s 获取信息失败，失败原因：%s" % (org_sp_name, self.host, e))
                    else:
                        org_sp_tmp = {"organizationId": org_id_encode, "organizationName": org_sp_name}
                        org_sp.update(org_sp_tmp)
                        tmp = {"role_id": role_id, "org_sp": org_sp}
                        role_info.update(tmp)
        return roleinfo_list

    def generate_sql(self,roleinfo_list):
        sql_list = []
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for role_info in roleinfo_list:
            sql = ("insert into member_account_role (member_id, organization_id ,role_id ,creator ,gmt_create \
            ,gmt_modified ,organization_sp ,role_sp ,position_id) values({0},{1},{2},{3},{4},{5},{6},{7},{8})".format
                   (role_info['member_id'], role_info['org_id'],role_info['role_id'], "", time, time,
                    role_info['org_sp'], role_info['role_sp'], ""))
            sql_list.append(sql)
        return sql_list

class Mysql_Connection_ssh(Mysql_Connection):
    def __init__(self, db_address, db_user, db_password, ssh_private_key_password):
        self.db = 'stiee_basic'
        self.db_user = db_user
        self.ssh_host = '124.71.128.48'
        self.ssh_port = 17025
        self.ssh_username = 'root'
        self.ssh_pkey = "D:\\YYD\\PrivateKey\\id_rsa_002"
        self.host = db_address.split(":")[0]
        db_port = int(db_address.split(":")[1])
        self.server = SSHTunnelForwarder(
            (self.ssh_host, self.ssh_port),
            ssh_username=self.ssh_username,
            ssh_pkey=self.ssh_pkey,
            ssh_private_key_password=ssh_private_key_password,
            local_bind_address=('127.0.0.1', 4306),
            remote_bind_address=(self.host, db_port))
        self.server.start()
        host = "127.0.0.1"  # 必须为127.0.0.1
        port = 4306
        conn_pi = create_engine(
            'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8' % (self.db_user, db_password, host, port, self.db))
        self.con = conn_pi.connect()

    def close(self):
        self.con.close()
        self.server.close()




if __name__ == '__main__':
    role_list = ['职能部门', '标准管理员', '科技管理员', '市场部批准', '质量部部长', '系统运维', '板块财务经理', '人力资源部部长', '市场部评审']
    # 从生产同步至模拟，否则从模拟同步至生产
    Sync_from_pi = True
    pro_conn = Mysql_Connection_ssh('192.168.0.236:3306','dba', 'F9v#gRjx2jDy!9mV', 'Stiee123@@@')
    test_conn = Mysql_Connection('101.43.47.152:60568','production','Stiee123@')

    if Sync_from_pi:
        roleinfo_list = pro_conn.get_role_info(role_list)
        roleinfo_list1 = test_conn.trans_org(roleinfo_list)
        sql_list = pro_conn.generate_sql(roleinfo_list1)
        print(sql_list)
    else:
        roleinfo_list = test_conn.get_role_info(role_list)
        roleinfo_list1 = pro_conn.trans_org(roleinfo_list)
    pro_conn.close()
    test_conn.close()

