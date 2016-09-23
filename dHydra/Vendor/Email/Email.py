# -*- coding: utf-8 -*-
"""
# Created on
# @author: Emptyset
# @contact: 21324784@qq.com
"""
# 以下是自动生成的 #
# --- 导入系统配置
from dHydra.core.Vendor import Vendor
# --- 导入自定义配置
# 以上是自动生成的 #
# ========================================
# 导入smtplib和MIMEText
# ========================================
from email.mime.text import MIMEText
import smtplib


class Email(Vendor):
    def __init__(self, mail_host="smtp.126.com", mail_user="", mail_pass="", mail_postfix="126.com"):
        super().__init__()
        # =================================
        # 设置服务器，用户名、口令以及邮箱的后缀
        # =================================
        self.mail_host = mail_host
        self.mail_user = mail_user
        self.mail_pass = mail_pass
        self.mail_postfix = mail_postfix

    # ======================================
    # 发送邮件
    # ======================================
    def send(self, nickname="dHydra", to=[], sub="", content=""):
        '''''
        to_list:发给谁
        sub:主题
        content:内容
        send_mail("aaa@126.com","sub","content")
        '''
        me = nickname + "<" + self.mail_user + "@" + self.mail_postfix + ">"
        msg = MIMEText(content)
        msg['Subject'] = sub
        msg['From'] = me
        msg['To'] = ";".join(to)
        try:
            s = smtplib.SMTP()
            s.connect(self.mail_host)
            s.login(self.mail_user, self.mail_pass)
            s.sendmail(me, to, msg.as_string())
            s.close()
            return True
        except Exception as e:
            print(str(e))
            return False
