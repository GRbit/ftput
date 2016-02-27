import ftput.conn as conn
import ftput.error as error
import re
import socket
import telnetlib

_re227_ = re.compile(r'\d+,\d+,\d+,\d+,\d+,\d+')
CRLF = '\r\n'

def check_resp(resp, code):
    """

    :type resp: str or unicode
    :type code: str or unicode
    :rtype: bool
    """
    for line in resp.split(CRLF):
        if code in line[:3]:
            return True
    return False

class FTP:
    """Basic ftp class operating in 'control connection' by using ftp_conn class"""

    def __init__(self, host, user='anonymous', passwd='', port=21, timeout=60,
                 debug=0):
        self.connected = False
        print("\n", user, passwd, "\n")
        self.conn = conn.FTPConn(host, port, user, passwd, timeout, debug)

    def isdir(self, pathname):
        pwd = self.pwd()
        resp = self.conn.CWD(pathname)
        if check_resp(resp, '250'):
            self.conn.CWD(pwd)
            return True
        elif check_resp(resp, '550'):
            return False
        raise error.ImpossiburuAnswer("can't check is it directory or not: " + pathname)

    def pwd(self):
        resp = self.conn.PWD()
        if check_resp(resp, '257'):
            resp = resp.split('"', 1)[1]
            resp = resp.rsplit('"', 1)[0]
            return resp
        return False

    def cd(self, pathname=''):
        if pathname:
            resp = self.conn.CWD(pathname)
        else:
            resp = self.conn.CDUP()
        if check_resp(resp, '250'):
            return resp
        return False

    def ls(self, pathname='.'):
        t_conn = self.make_psv(use_telnet=True)
        resp = str(self.conn.NLST(pathname))
        if check_resp(resp, '150'):
            ls = t_conn.read_all().split(CRLF)
            if not check_resp(resp, '226'):
                self.conn.get_resp()
            return filter(None, ls)
        return False

    def ll(self, pathname='.'):
        t_conn = self.make_psv(use_telnet=True)
        resp = str(self.conn.LIST(pathname))
        if check_resp(resp, '150'):
            ll = t_conn.read_all().split(CRLF)
            if not check_resp(resp, '226'):
                self.conn.get_resp()
            return filter(None, ll)
        return False

    def mkdir(self, path):
        if '257' in self.conn.MKD(path):
            return True
        return False

    def rmdir(self, path):
        if '250' in self.conn.RMD(path):
            return True
        return False

    def retrieve(self, remote_path, local_path, chunk_in_kb=16):
        s_conn = self.make_psv()
        resp = self.conn.RETR(remote_path)
        if check_resp(resp, '150'):
            f = open(local_path, 'w')
            while True:
                try:
                    data = s_conn.recv(chunk_in_kb*1024)
                except socket.error:
                    return False
                if not data:
                    break
                f.write(data)
            s_conn.close()
            f.close()
            # begin: for small files
            if not check_resp(resp, '226'):
                resp = self.conn.get_resp()
            # end: for small files
            if check_resp(resp, '226'):
                return True
        elif check_resp(resp, '550'):
            self.conn.ABOR()
            raise error.FileUnavailable(remote_path)
        return False

    def store(self, local_path, remote_path, chunk_in_kb=16):
        s_conn = self.make_psv()
        resp = self.conn.STOR(remote_path)
        if check_resp(resp, '150'):
            f = open(local_path, 'r')
            while 1:
                chunk = f.read(chunk_in_kb*1024)
                if not chunk: break
                try:
                    s_conn.sendall(chunk)
                except socket.error:
                    return False
            s_conn.close()
            f.close()
            resp = self.conn.get_resp()
        if not check_resp(resp, '226'):
            return False
        return True

    def make_psv(self, use_telnet=False):
        resp = self.conn.PASV()
        m = _re227_.search(resp)
        if not m:
            raise error.ImpossiburuAnswer('Can\'t find ip/port for passive connection\n' + resp)
        s = m.group(0).split(',')
        ip = '.'.join(s[:4])
        port = int(s[-2])*256 + int(s[-1])
        if use_telnet:
            return telnetlib.Telnet(ip, port)
        return socket.create_connection((ip, port), 60)
