import ftput.conn as conn
import ftput.error as error
import re
import socket

_re227_ = re.compile(r'\d+,\d+,\d+,\d+,\d+,\d+')
CRLF = '\r\n'


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
        if '250' in resp:
            self.conn.CWD(pwd)
            return True
        elif '550' in resp:
            return False
        raise error.ImpossiburuAnswer("can't check is it directory or not: " + pathname)

    def pwd(self):
        resp = self.conn.PWD()
        if '257' in resp:
            resp = resp.split('"', 1)[1]
            resp = resp.rsplit('"', 1)[0]
            return resp
        return False

    def cd(self, pathname=''):
        if pathname:
            resp = self.conn.CWD(pathname)
        else:
            resp = self.conn.CDUP()
        if '250' in resp:
            return resp
        return False

    def ls(self, pathname='.'):
        t_conn = self.make_psv()
        resp = str(self.conn.NLST(pathname))
        if '150' in resp:
            ls = t_conn.read_all().split(CRLF)
            if '226' not in resp:
                self.conn.get_resp()
            return ls
        return False

    def ll(self, pathname='.'):
        t_conn = self.make_psv()
        resp = str(self.conn.LIST(pathname))
        if '150' in resp:
            ll = t_conn.read_all().split(CRLF)
            if '226' not in resp:
                self.conn.get_resp()
            return ll
        return False

    def mkdir(self, path):
        if '257' in self.conn.MKD(path):
            return True
        return False

    def rmdir(self, path):
        if '250' in self.conn.RMD(path):
            return True
        return False

    def retrieve(self, remote_path, local_path):
        t_conn = self.make_psv()
        resp = self.conn.RETR(remote_path)
        if '150' in resp:
            f = open(local_path, 'w')
            try:
                f.write(t_conn.read_all())
            except socket.error:
                return False
            f.close()
            # begin: for small files
            if '226' not in resp:
                resp = self.conn.get_resp()
            # end: for small files
            if '226' in resp:
                return True
        elif '550' in resp:
            self.conn.ABOR()
            raise error.FileUnavailable(remote_path)
        return False

    def store(self, local_path, remote_path):
        t_conn = self.make_psv()
        resp = self.conn.STOR(remote_path)
        f = open(local_path, 'r')
        w = f.read()
        f.close()
        if '150' in resp:
            try:
                t_conn.write(w)
                t_conn.close()
                resp = self.conn.get_resp()
            except socket.error:
                return False
        if '226' not in resp:
            return False
        return True

    def make_psv(self):
        resp = self.conn.PASV()
        m = _re227_.search(resp)
        if not m:
            raise error.ImpossiburuAnswer('Can\'t find ip/port for passive connection\n' + resp)
        s = m.group(0).split(',')
        ip = '.'.join(s[:4])
        port = int(s[-2])*256 + int(s[-1])
        return self.conn.new_conn(ip, port)
