# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   开发人员：杨烨东
   开发日期：2023-09-22
   开发工具：PyCharm
   功能描述： 某些情况下派云两套环境的角色信息需要批量同步时，用脚本批量生产sql（不直接更新，而是生成sql是为了方便检查）

-------------------------------------------------
"""

import requests
import pandas as pd
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder
import pymysql
import datetime


class MysqlConnection:
    def __init__(self, db_address, db_user, db_password):
        self.db = 'stiee_basic'
        self.host = db_address.split(":")[0]
        port = int(db_address.split(":")[1])
        self.con = pymysql.connect(host=self.host, user=db_user, passwd=db_password, database=self.db, port=port,
                                   use_unicode=True, charset="utf8")
        # conn_pi = create_engine(
        #     'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8' % (self.db_user, db_password, host, port, self.db))
        # self.con = conn_pi.connect()

    def conn_close(self):
        self.con.close()

    def query_sql(self, sql):
        result_df = pd.read_sql(sql=sql, con=self.con)
        return result_df

    # 将字符串按派云的需要编码
    def encode_number(self, number):
        url1 = "https://pi.stiee.com/api/manager/util/encode?id="
        headers = {
            'content-type': 'application/json',
        }
        url = url1 + str(number)
        resp = requests.get(url, headers=headers)
        encode_number = resp.json()
        return encode_number.get('extData')

    # 获取每个角色下的人员信息，以及人员权限范围信息
    def get_role_info(self, role_list):
        roleinfo_list = []

        for role_name in role_list:
            sql1 = "select id from member_role where name in ('%s') and is_deleted=0" % role_name
            result_df = self.query_sql(sql1)
            try:
                role_id = result_df.at[0, 'id']
            except Exception as e:
                print("角色 ： %s 在地址：%s 不存在" % (role_name, self.host))
            else:
                try:
                    sql2 = "select c.real_name ,b.name ,a.organization_id  from   member_account_role a  \
                                          left join member_role b on a.role_id = b.id \
                                          left join member_account c on a.member_id = c.id\
                                          where  a.organization_id <>0 and a.organization_id is not null \
                                           and role_id in (%d) " % role_id
                    result_df2 = self.query_sql(sql2)
                    for idx, data in result_df2.iterrows():
                        org_id_list = data['organization_id'].split(",")
                        org_sp_name_list = []
                        for org_id in org_id_list:
                            sql3 = "select name from member_organization where id= '%s'" % org_id
                            result_df = self.query_sql(sql3)
                            org_name = result_df.at[0, 'name']
                            org_sp_name_list.append(org_name)
                        role_info = {"member_name": data['real_name'], "org_sp_name_list": org_sp_name_list,
                                     "role_name": data['name']}

                        roleinfo_list.append(role_info)
                except Exception as e:
                    print("角色 ： %s 获取角色信息失败，失败原因：%s,失败行号： %s" % (
                    role_name, e, e.__traceback__.tb_lineno))
        print("###########获取角色信息完成####################")
        return roleinfo_list

    # 获取各个名称对应的id号
    def trans_name(self, roleinfo_list):
        # 倒序循环避免删除时索引溢出
        for i in range(len(roleinfo_list) - 1, -1, -1):
            role_info = roleinfo_list[i]
            org_sp_name_list = role_info['org_sp_name_list']
            role_name = role_info['role_name']
            member_name = role_info['member_name']
            try:
                query_role_name = "select id,name from member_role  where name='%s' and is_deleted=0" % role_name
                result_df = self.query_sql(query_role_name)
                role_id = result_df.at[0, 'id']
            except Exception as e:
                print("角色：%s在地址：%s 获取信息失败，失败原因：%s" % (role_name, self.host, e))
                roleinfo_list.pop(i)
            else:
                try:
                    query_member_name = "select id from member_account ma where real_name ='%s'" % member_name
                    result_df = self.query_sql(query_member_name)
                    member_id = result_df.at[0, 'id']
                except:
                    print("姓名：'%s' 在地址：%s 不存在" % (member_name, self.host))
                    roleinfo_list.pop(i)
                else:
                    org_sp = {}
                    org_id = ''
                    for org_sp_name in org_sp_name_list:
                        sql = "select id,name from member_organization where is_deleted =0 and name = '%s'" % org_sp_name
                        result_df = self.query_sql(sql)
                        try:
                            org_id_encode = self.encode_number(result_df.at[0, 'id'])
                        except Exception as e:
                            print("组织：%s 在地址：%s 获取信息失败，失败原因：%s" % (org_sp_name, self.host, e))
                            roleinfo_list.pop(i)
                        else:
                            org_id = str(result_df.at[0, 'id']) + ',' + org_id
                            org_sp_tmp = {"organizationId": org_id_encode, "organizationName": org_sp_name}
                            org_sp.update(org_sp_tmp)
                    tmp = {"member_id": member_id, "role_id": role_id, "org_sp": org_sp, "org_id": org_id}
                    role_info.update(tmp)
        print("###########获取id信息完成############")
        return roleinfo_list

    # 生产sql脚本
    def generate_sql(self, roleinfo_list):
        sql_list = []
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for role_info in roleinfo_list:
            sql = ("insert into member_account_role (member_id, organization_id ,role_id ,creator ,gmt_create \
            ,gmt_modified ,organization_sp ,role_sp ) values({0},\"{1}\",{2},\"{3}\",\"{4}\",\"{5}\",\"{6}\",\"{7}\") \n".format
                   (role_info['member_id'], role_info['org_id'], role_info['role_id'], "", time, time,
                    role_info['org_sp'], role_info['role_name']))
            sql_list.append(sql)
            print(sql)



"""
ssh秘钥访问数据库
"""


class MysqlConnectionSSH(MysqlConnection):
    def __init__(self, db_address, db_user, db_password, ssh_private_key_password, ssh_address, ssh_key):
        self.db = 'stiee_basic'
        self.ssh_username = 'root'
        ssh_host = ssh_address.split(":")[0]
        ssh_port = int(ssh_address.split(":")[1])
        host = db_address.split(":")[0]
        db_port = int(db_address.split(":")[1])
        self.server = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=self.ssh_username,
            ssh_pkey=ssh_key,
            ssh_private_key_password=ssh_private_key_password,
            local_bind_address=('127.0.0.1', 4306),
            remote_bind_address=(host, db_port))
        self.server.start()
        host = "127.0.0.1"  # 必须为127.0.0.1
        port = 4306
        conn_pi = create_engine(
            'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8' % (db_user, db_password, host, port, self.db))
        self.con = conn_pi.connect()

    def close(self):
        self.con.close()
        self.server.close()


if __name__ == '__main__':
    # role_list = ['职能部门', '标准管理员', '科技管理员', '市场部批准', '质量部部长', '系统运维', '板块财务经理', '人力资源部部长', '市场部评审']
    role_list = ['标准管理员']
    # 从生产同步至模拟，否则从模拟同步至生产
    Sync_from_pi = True
    pro_conn = MysqlConnectionSSH('数据库地址', '数据库账户', '数据库密码',
                                  'ssh密码', "ssh地址", "ssh秘钥地址")
    test_conn = MysqlConnection('数据库地址', '数据库账户', '数据库密码')

    if Sync_from_pi:
        role_info_list = pro_conn.get_role_info(role_list)
        role_info_tran_list = test_conn.trans_name(role_info_list)
        pro_conn.generate_sql(role_info_tran_list)

    else:
        role_info_list = test_conn.get_role_info(role_list)
        role_info_tran_list = pro_conn.trans_name(role_info_list)
        test_conn.generate_sql(role_info_tran_list)

    pro_conn.conn_close()
    test_conn.conn_close()
