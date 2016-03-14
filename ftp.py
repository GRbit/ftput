import sys
import socket
import telnetlib
import re

import ftput.conn as conn
import ftput.error as error

_re227_ = re.compile(r'\d+,\d+,\d+,\d+,\d+,\d+')
CRLF = '\r\n'


def check_resp(resp, code):
    """

    :type resp: str or unicode
    :type code: str or unicode
    :rtype: bool
    """
    for line in resp.split(CRLF):
        if code in line[:len(code)]:
            return True
    return False


class FTP:
    """Basic ftp class operating in 'control connection' by using ftp_conn class"""

    def __init__(self, host, user='anonymous', passwd='', port=21, timeout=60,
                 debug=0):
        self.connected = False
        self.conn = conn.FTPConn(host, port, user, passwd, timeout, debug)

    def exist(self, pathname):
        """

        :type pathname: str or unicode
        :rtype: bool
        """
        if self.stat(pathname):
            return True
        return False

    def isfile(self, pathname):
        """

        :type pathname: str or unicode
        :rtype: bool
        """
        stat = self.stat(pathname)
        if stat and (len(stat) == 1) and (stat[1][0] == '-'):
            return True
        return False

    def isdir(self, pathname):
        """

        :type pathname: str or unicode
        :rtype: bool
        """
        pwd = self.pwd()
        resp = self.conn.CWD(pathname)
        if check_resp(resp, '250'):
            self.conn.CWD(pwd)
            return True
        elif check_resp(resp, '550'):
            return False
        raise error.ImpossiburuAnswer("can't check is it directory or not: " + pathname)

    def pwd(self):
        """

        :rtype: str or unicode
        """
        resp = self.conn.PWD()
        if check_resp(resp, '257'):
            resp = resp.split('"', 1)[1]
            resp = resp.rsplit('"', 1)[0]
            return resp
        return ''

    def cd(self, pathname=''):
        """

        :type pathname: str or unicode
        :rtype: bool
        """
        if pathname:
            resp = self.conn.CWD(pathname)
        else:
            resp = self.conn.CDUP()
        if check_resp(resp, '250'):
            return resp
        return False

    def ls(self, pathname='.'):
        """

        :type pathname: str or unicode
        :rtype: list of str or unicode
        """
        t_conn = self.make_psv(use_telnet=True)
        resp = self.conn.NLST(pathname)
        if check_resp(resp, '150'):
            ls = t_conn.read_all()
            if sys.version[0] == '3':
                ls = ls.decode('utf-8')
            ls = ls.split(CRLF)
            t_conn.close()
            while not check_resp(resp, '226'):
                resp = self.conn.get_resp()
            return list(filter(None, ls))
        return False

    def ll(self, pathname='.'):
        """

        :type pathname: str or unicode
        :rtype: list of str or unicode
        """
        t_conn = self.make_psv(use_telnet=True)
        resp = self.conn.LIST(pathname)
        if check_resp(resp, '150'):
            ll = t_conn.read_all()
            if sys.version[0] == '3':
                ll = ll.decode('utf-8')
            ll = ll.split(CRLF)
            t_conn.close()
            while not check_resp(resp, '226'):
                resp = self.conn.get_resp()
            return list(filter(None, ll))
        return False

    def stat(self, pathname=''):
        """

        :type pathname: str or unicode
        :rtype: list of str or unicode
        """
        resp = str(self.conn.STAT(pathname))
        if check_resp(resp, '213-') or check_resp(resp, '211-'):
            while not check_resp(resp, '213 End') and not check_resp(resp, '211 End'):
                resp += self.conn.get_resp()
            resp = list(filter(None, resp.split(CRLF)))
            if len(resp) == 2:
                return list()
            return resp[1:-1]
        return False

    def mkdir(self, path):
        """

        :type path: str or unicode
        :rtype: bool
        """
        if '257' in self.conn.MKD(path):
            return True
        return False

    def rmdir(self, path):
        """

        :type path: str or unicode
        :rtype: bool
        """
        if '250' in self.conn.RMD(path):
            return True
        return False

    def rm(self, path):
        """

        :type path: str or unicode
        :rtype: bool
        """
        if '250' in self.conn.DELE(path):
            return True
        return False

    def retrieve(self, remote_path, local_path, chunk_in_kb=16):
        """

        :type remote_path: str or unicode
        :type local_path: str or unicode
        :type chunk_in_kb: int
        :rtype: int
        """
        # TODO return retrieved bytes
        s_conn = self.make_psv()
        resp = self.conn.RETR(remote_path)
        if check_resp(resp, '150'):
            f = open(local_path, 'wb')
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
        """

        :type local_path: str or unicode
        :type remote_path: str or unicode
        :type chunk_in_kb: int
        :rtype: int
        """
        # TODO return sended bytes
        s_conn = self.make_psv()
        resp = self.conn.STOR(remote_path)
        if check_resp(resp, '150'):
            f = open(local_path, 'rb')
            while 1:
                chunk = f.read(chunk_in_kb*1024)
                if not chunk:
                    break
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
        """

        :type use_telnet: bool
        :rtype: socket._socketobject or telnetlib.Telnet
        """
        resp = self.conn.PASV()
        m = _re227_.search(resp)
        if not m:
            raise error.ImpossiburuAnswer('Can\'t find ip/port for passive connection\n' + resp)
        s = m.group(0).split(',')
        ip = '.'.join(s[:4])
        port = int(s[-2])*256 + int(s[-1])
        if self.conn.debug > 1:
            if use_telnet:
                print('Open telnet connection on ip', ip, 'on port', port)
            else:
                print('Open socket on ip', ip, 'on port', port)
        if use_telnet:
            return telnetlib.Telnet(ip, port)
        try:
            return socket.create_connection((ip, port), 60)
        except socket.timeout:
            sys.stderr.write('ERROR: Disconnected on socket.create_connection, trying again\n')
            self.conn.connected = False
            return self.make_psv()
