#! /usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import dialog
import subprocess
import paramiko
import time

class LocalCommand(object):

    def __init__(self):
        self.local_hostname = ""
        self.local_ipaddress = ""
        self.local_netmask = "255.255.255.0"
        self.local_gw = ""
        self.local_dev = "eth0"


    def local_cmd(self, cmd):
        """

        :param cmd: 命令行，str
        :return: obj 标准输出+标准错误
        """
        cmd_list = cmd.split()
        obj = subprocess.Popen(cmd_list,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return obj

class RemoteCommand(object):

    def __init__(self):
        self.remote_hostname = ""
        self.remote_ipaddress = ""
        self.remode_netmask="255.255.255.0"
        self.remote_username = "root"
        self.remote_password = "root"
        self.remote_os_type = ""
        self.remote_disk = ""
        self.port = 22

    def connect(self):
        transport = paramiko.Transport((self.remote_ipaddress, self.port))
        transport.connect(username=self.remote_username, password=self.remote_password)
        self.__transport = transport

    def close(self):
        self.__transport.close()

    def upload(self, local_path, target_path):
        sftp = paramiko.SFTPClient.from_transport(self.__transport)
        sftp.put(local_path, target_path)

    def remote_cmd(self, command):
        ssh = paramiko.SSHClient()
        ssh._transport = self.__transport
        # 执行命令
        stdin, stdout, stderr = ssh.exec_command(command)
        return stderr.read(),stdout.read()

class Menu(LocalCommand, RemoteCommand):


    def __init__(self, product_name):

        super(LocalCommand, self).__init__()
        super(RemoteCommand, self).__init__()

        self.role = ""
        self.local_disk = ""
        self.PRODUCT_NAME = product_name
        self.source_disk_partition_count = 0
        self.my_dialog = dialog.Dialog(dialog="dialog")
        self.my_dialog.set_background_title(self.PRODUCT_NAME)
        self.top_menu()


    def err_msg(self, msg):
        '''
        如果执行过程有错误，显示错误信息，并且退出
        :param msg: 消息
        :return:
        '''
        code, _ = self.my_dialog.msgbox(u"错误: \n---\n%s" %msg)
        if code == self.my_dialog.OK:
            exit(100)
        elif code == self.my_dialog.CANCEL or code == self.my_dialog.ESC:
            exit(100)



    def top_menu(self):
        code, tags = self.my_dialog.menu(
            text=u"欢迎使用 %s ..." % self.PRODUCT_NAME,
            # height=23,
            # width=76,
            choices=[
                ("1", u"配置为源端（SOURCE）"),
                ("2", u"配置为目标端（TARGET）"),
                ("3", u"高级配置"),
            ]
        )

        if code == self.my_dialog.OK:
            if tags == "1":
                self.role = "SOURCE"
                self.config_ip_host()
            elif tags == "2":
                self.role = "TARGET"
                self.config_ip_host()
            elif tags == "3":
                self.my_dialog.msgbox(u"TODO，敬请期待...")
                exit(100)
        elif code == self.my_dialog.CANCEL or code == self.my_dialog.ESC:
            exit(100)


    def config_ip_host(self):
        # hostname = self.local_hostname or "localhost"
        # device = self.local_dev or "eth0"
        # ip_address = self.local_ipaddress or "192.168.88.11"
        # netmask = self.local_netmask or "255.255.255.0"
        # gw = self.local_gw or "192.168.88.1"
        hostname = "target"
        device =  "enp0s8"
        ip_address =  "192.168.88.11"
        netmask =  "255.255.255.0"
        gw = "192.168.88.1"

        code, tags = self.my_dialog.form(
            text=u"配置(%s)服务器的主机名和IP地址" % self.role,
            elements=[
                (u"主机名",    1, 3, hostname, 1, 15, 16, 15),
                (u"网卡名称",   2, 3, device,   2, 15, 16, 15),
                (u"IP 地址",  3, 3, ip_address, 3, 15, 16, 15),
                (u"子网掩码", 4, 3, netmask,     4, 15, 16, 15),
                (u"网关地址", 5, 3, gw,          5, 15, 16, 15),
            ],
        )

        if code == self.my_dialog.OK:

            self.local_hostname, self.local_dev, self.local_ipaddress,self.local_netmask, self.local_gw = tags

            # config ip
            cmd = "ip address add %s/%s dev %s" % (self.local_ipaddress, self.local_netmask,  self.local_dev)
            self.local_cmd(cmd)
            # link up
            self.local_cmd("ip link set %s up" % self.local_dev)
            # set hostname
            self.local_cmd("hostname %s" % self.local_hostname)

            if self.role == "TARGET":
                self.source_config()
            else:
                self.my_dialog.msgbox(u"配置完成!\n退出...")
                exit(100)

        elif code == self.my_dialog.CANCEL or code == self.my_dialog.ESC:
            self.top_menu()




    def source_config(self):
        code, tags = self.my_dialog.form(
            text=u"本%s服务器主机名：%s，请配置源端服务器：" % (self.role, self.local_hostname),
            elements=[
                (u"IP 地址", 2, 3, "192.168.88.12", 2, 15, 20, 15),
                (u"用户名", 3, 3, "root", 3, 15, 20, 15),
                (u"密码", 4, 3, "root", 4, 15, 20, 15),
            ],
        )

        if code == self.my_dialog.OK:
            self.remote_ipaddress, self.remote_username, self.remote_password = tags

            self.connect()  # 远程连接到remote主机

            self.source_os()


            # err, out = self.cmd('parted -s /dev/sda unit s print ')
            # print out
            # self.close()


        elif code == self.my_dialog.CANCEL or code == self.my_dialog.ESC:
            self.close()


    def source_os(self):

        code, tags = self.my_dialog.menu(
            text=u"本%s服务器主机名：%s，选择源端操作系统类型：" % (self.role, self.local_hostname),
            choices=[
                ("1", u"windows server 2008 r2"),
                ("2", u"windows server 2012 r2"),
                ("3", u"windows 7"),
                ("11", u"RHEL/CentOS 6"),
                ("12", u"RHEL/CentOS 7"),
            ]
        )

        if code == self.my_dialog.OK:

            if int(tags) < 10:
                print "source server is a windows server "
                self.source_disk()
            else:
                print "source server is a linux server"

        elif code == self.my_dialog.CANCEL or code == self.my_dialog.ESC:
            self.source_config()

    # def source_listpart(self):
    #
    #     cmd = "parted -s %s unit s print" % self.remote_disk
    #     err, source_part_msg = self.remote_cmd(cmd)
    #
    #     self.my_dialog.msgbox(
    #         text=u"本服务器为%s，源端分区表为：\n---\n%s" % (self.local_hostname, source_part_msg),
    #         width=80,
    #         height=20,
    #
    #     )
    #     self.target_mkpart()


    def source_disk(self):

        code, tags = self.my_dialog.form(
            text=u"本%s服务器主机名：%s，需要复制的源端和目标端硬盘" % (self.role, self.local_hostname),
            elements=[
                (u"源端硬盘1", 1, 3, "/dev/sda", 1, 25, 20, 15),
                (u"源端硬盘2(如果有)", 2, 3, "", 2, 25, 20, 15),
                (u"目标硬盘1", 4, 3, "/dev/sda", 4, 25, 20, 15),
                (u"目标硬盘2(如果有)", 5, 3, "", 5, 25, 20, 15),
            ],
        )

        if code == self.my_dialog.OK:
            # 只支持一个硬盘的复制
            # TODO : 支持多个硬盘
            if tags[1]:
                self.my_dialog.msgbox(u"SORRY!!!\n敬请期待多个硬盘的复制。。。")
                exit(100)
            self.remote_disk = tags[0]
            self.local_disk = tags[2]
            # print(self.remote_disk)
            self.target_mkpart()
            # self.source_listpart()

        elif code == self.my_dialog.CANCEL or code == self.my_dialog.ESC:
            self.source_os()


    def target_mkpart(self):
        cmd = "parted -s %s unit s print" % self.remote_disk
        err, part_msg = self.remote_cmd(cmd)

        if "msdos" in part_msg.split('\n')[3]:
            disk_label = "msdos"
        else:
            disk_label = "gpt"

        part_list = part_msg.split('\n')[7:]

        self.source_disk_partition_count = len(part_list)

        elements = []
        for i in range(len(part_list)):
            p_list = part_list[i].split()
            if not p_list: continue
            print(p_list)

            start = p_list[1]
            end = p_list[2]
            p_type = p_list[4]
            fs = p_list[5]
            if len(p_list) == 7:
                boot = p_list[6]
            else:
                boot = ""
            ele = [

                (u"分区%s    分区类型： (%s)"   % (i+1, p_type), 6*i+1, 3, p_type, 6*i+1, 35, 20, 15),
                (u"分区%s     fs类型：  (%s)"   % (i+1, fs),     6*i+2, 3, fs,     6*i+2, 35, 20, 15),
                (u"分区%s     start：  (%s)"   % (i + 1, start), 6*i+3, 3, start, 6 * i + 3, 35, 20, 15),
                (u"分区%s       end：  (%s)"   % (i + 1, end), 6*i+4, 3, end, 6 * i + 4, 35, 20, 15),
                (u"分区%s boot(或空)：  (%s)"   % (i+1, boot),   6*i+5, 3, boot,   6*i+5, 35, 20, 15),
            ]

            elements += ele

        code, tags = self.my_dialog.form(
            text=u"本%s服务器主机名：%s，开始为%s硬盘分区\n注意分区将格式化所有数据！！！"
                 % (self.role, self.local_hostname,self.local_disk),
            elements=elements,
        )

        if code == self.my_dialog.OK:

            # print tags
            part_cmd = "parted -s %s -- " % self.local_disk
            part_cmd += "mklabel %s " % disk_label
            if len(tags) % 5 != 0:
                exit(100)
            else:
                # primary 替换为mkpart primary
                # boot 替换为set 1 boot on
                for i in range(len(tags)/5):
                    tags[i*5] = "mkpart %s" % tags[i*5]
                    if tags[i*5+4] =="boot":
                        tags[i * 5 + 4] = "set %s boot on" % str(i+1)
            part_cmd += " ".join(tags)

            print(part_cmd)
            # self.local_cmd(part_cmd)

            self.fs_clone()

        elif code == self.my_dialog.CANCEL or code == self.my_dialog.ESC:
            self.source_disk()


    def _fs_clone_by_part(self, part_name, nc_port):
        
        local_clone_cmd = "nc -l %d | gunzip -c | ntfsclone --restore-image --overwrite %s - " % (nc_port, part_name)
        self.local_cmd(local_clone_cmd)
        time.sleep(2)
        remote_clone_cmd = "ntfsclone --save-image --output - %s |gunzip -c |nc %s %d " % (part_name, self.local_ipaddress, nc_port)
        self.remode_cmd(remote_clone_cmd)

    def fs_clone(self):
        code, tags = self.my_dialog.yesno(u"是否开始复制？")
        if code == self.my_dialog.OK:
            pass
        elif code == self.my_dialog.CANCEL or code == self.my_dialog.ESC:
            exit(100)

        for i in range(self.source_disk_partition_count):
            self._fs_clone_by_part(part_name = self.local_disk+str(i),
                    nc_port= 5000 + i )
        

    def copy_file(self):
        pass



if __name__ == '__main__':

    PRODUCT_NAME = "Migration LiveCD Tools"


    m = Menu(PRODUCT_NAME)
















