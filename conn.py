import sys
import telnetlib
import ftput.error as error

CRLF = "\r\n"

USER_acceptable = ['421', '230', '530', '500', '501', '331', '332']
PASS_acceptable = ['421', '230', '202', '530', '500', '501', '503', '332']
ACCT_acceptable = ['421', '230', '202', '530', '500', '501', '503']
CWD_acceptable = ['421', '250', '500', '501', '502', '530', '550']
CDUP_acceptable = ['421', '200', '250', '500', '501', '502', '530', '550']
SMNT_acceptable = ['421', '202', '250', '500', '501', '502', '530', '550']
REIN_acceptable = ['421', '120', '220', '500', '502']
QUIT_acceptable = ['421', '221', '500']
PORT_acceptable = ['421', '200', '500', '501', '530']
PASV_acceptable = ['421', '227', '500', '501', '502', '530']
MODE_acceptable = ['421', '200', '500', '501', '504', '530']
TYPE_acceptable = ['421', '200', '500', '501', '504', '530']
STRU_acceptable = ['421', '200', '500', '501', '504', '530']
ALLO_acceptable = ['421', '200', '202', '500', '501', '504', '530']
REST_acceptable = ['421', '500', '501', '502', '530', '350']
STOR_acceptable = ['421', '125', '150', '110', '226', '250', '425', '426', '451',
                   '551', '552', '532', '450', '452', '553', '500', '501', '530']
STOU_acceptable = ['421', '125', '150', '110', '226', '250', '425', '426', '451',
                   '551', '552', '532', '450', '452', '553', '500', '501', '530']
RETR_acceptable = ['421', '125', '150', '110', '226', '250', '425', '426', '451',
                   '450', '550', '500', '501', '530']
LIST_acceptable = ['421', '125', '150', '226', '250', '425', '426', '451', '450',
                   '500', '501', '502', '530']
NLST_acceptable = ['421', '125', '150', '226', '250', '425', '426', '451', '450',
                   '500', '501', '502', '530']
APPE_acceptable = ['421', '125', '150', '110', '226', '250', '425', '426', '451',
                   '551', '552', '532', '450', '550', '452', '553', '500', '501',
                   '502', '530']
RNFR_acceptable = ['421', '450', '550', '500', '501', '502', '530', '350']
RNTO_acceptable = ['421', '250', '532', '553', '500', '501', '502', '503', '530']
DELE_acceptable = ['421', '250', '450', '550', '500', '501', '502', '530']
RMD_acceptable = ['421', '250', '500', '501', '502', '530', '550']
MKD_acceptable = ['421', '257', '500', '501', '502', '530', '550']
PWD_acceptable = ['421', '257', '500', '501', '502', '550']
ABOR_acceptable = ['421', '225', '226', '500', '501', '502']
SYST_acceptable = ['421', '215', '500', '501', '502']
STAT_acceptable = ['421', '211', '212', '213', '450', '500', '501', '502', '530']
HELP_acceptable = ['421', '211', '214', '500', '501', '502']
SITE_acceptable = ['421', '200', '202', '500', '501', '530']
NOOP_acceptable = ['421', '200', '500']
FEAT_acceptable = ['421']


class FTPConn:
    """Basic class which only connects to FTP host at init and checks basic commands"""

    def __init__(self, host, port=21, user='anonymous', passwd='', timeout=60, debug=0):
        self.telnet_c = None
        self.connected = False
        self.lastresp = ''
        self.lastcmd = ''

        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.timeout = timeout
        self.debug = debug

        self.connect()
        self.login()
        self.TYPE('I')

    def connect(self, host='', port='', timeout=''):
        if host:
            self.host = host
        if port:
            self.port = port
        if timeout:
            self.timeout = timeout
        self.telnet_c = telnetlib.Telnet(self.host, self.port, self.timeout)
        welcome = self.get_resp()
        if '421' not in welcome:
            self.connected = True
        return welcome

    def login(self):
        resp = self.USER(self.user)
        if '331' in resp:
            resp = self.PASS(self.passwd)
        else:
            raise error.ImpossiburuAnswer
        if resp[:1] == '5':
            if resp[:3] == '530':
                raise error.AuthError("Incorrect login")
            raise error.AuthError("Unexpected server answer: " + resp)
        return resp

    def get_resp(self, eager=False):
        """
        :type eager: bool
        :rtype: str
        """
        if eager:
            resp = self.telnet_c.read_very_eager()
        else:
            resp = self.telnet_c.read_some()
            resp += self.telnet_c.read_very_eager()
        if sys.version[0] == '3':
            resp = resp.decode('utf-8')
        if self.debug > 1:
            d = resp
            if resp[-2:] == CRLF:
                d = resp[:-2]
            elif resp[-1:] in CRLF:
                d = resp[:-1]
            print('RCI ' + d)
        self.lastresp = resp
        if resp[:3] == '421':
            self.connected = False
        return resp

    def send_cmd(self, cmd):
        if not self.connected:
            self.connect()
            self.login()
        if self.debug > 1:
            print('SND ' + cmd)
        self.lastcmd = cmd
        if sys.version[0] == '2':
            self.telnet_c.write(cmd + CRLF)
        else:
            self.telnet_c.write((cmd + CRLF).encode('utf-8'))

    def USER(self, username):
        """
        :type username: str
        :rtype: str
        """
        self.send_cmd('USER ' + username)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on USER command, trying again\n')
            self.connected = False
            resp = self.USER(username)
        if resp[:3] not in USER_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def PASS(self, password):
        """
        :type password: str
        :rtype: str
        """
        self.send_cmd('PASS ' + password)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on PASS command, trying again\n')
            self.connected = False
            resp = self.PASS(password)
        if resp[:3] not in PASS_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def ACCT(self, account_information):
        """
        :type account_information: str
        :rtype: str
        """
        self.send_cmd('ACCT ' + account_information)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on ACCT command, trying again\n')
            self.connected = False
            resp = self.ACCT(account_information)
        if resp[:3] not in ACCT_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def CWD(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('CWD ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on CWD command, trying again\n')
            self.connected = False
            resp = self.CWD(pathname)
        if resp[:3] not in CWD_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def CDUP(self):
        """
        
        :rtype: str
        """
        self.send_cmd('CDUP')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on CDUP command, trying again\n')
            self.connected = False
            resp = self.CDUP()
        if resp[:3] not in CDUP_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def SMNT(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('SMNT ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on SMNT command, trying again\n')
            self.connected = False
            resp = self.SMNT(pathname)
        if resp[:3] not in SMNT_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def QUIT(self):
        """
        
        :rtype: str
        """
        self.send_cmd('QUIT')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on QUIT command, trying again\n')
            self.connected = False
            resp = self.QUIT()
        if resp[:3] not in QUIT_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def REIN(self):
        """
        
        :rtype: str
        """
        self.send_cmd('REIN')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on REIN command, trying again\n')
            self.connected = False
            resp = self.REIN()
        if resp[:3] not in REIN_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def PORT(self, host_port):
        """
        :type host_port: str
        :rtype: str
        """
        self.send_cmd('PORT ' + host_port)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on PORT command, trying again\n')
            self.connected = False
            resp = self.PORT(host_port)
        if resp[:3] not in PORT_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def PASV(self):
        """
        
        :rtype: str
        """
        self.send_cmd('PASV')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on PASV command, trying again\n')
            self.connected = False
            resp = self.PASV()
        if resp[:3] not in PASV_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def TYPE(self, type_code):
        """
        :type type_code: str
        :rtype: str
        """
        self.send_cmd('TYPE ' + type_code)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on TYPE command, trying again\n')
            self.connected = False
            resp = self.TYPE(type_code)
        if resp[:3] not in TYPE_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def STRU(self, structure_code):
        """
        :type structure_code: str
        :rtype: str
        """
        self.send_cmd('STRU ' + structure_code)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on STRU command, trying again\n')
            self.connected = False
            resp = self.STRU(structure_code)
        if resp[:3] not in STRU_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def MODE(self, mode_code):
        """
        :type mode_code: str
        :rtype: str
        """
        self.send_cmd('MODE ' + mode_code)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on MODE command, trying again\n')
            self.connected = False
            resp = self.MODE(mode_code)
        if resp[:3] not in MODE_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def RETR(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('RETR ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on RETR command, trying again\n')
            self.connected = False
            resp = self.RETR(pathname)
        if resp[:3] not in RETR_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def STOR(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('STOR ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on STOR command, trying again\n')
            self.connected = False
            resp = self.STOR(pathname)
        if resp[:3] not in STOR_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def STOU(self):
        """
        
        :rtype: str
        """
        self.send_cmd('STOU')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on STOU command, trying again\n')
            self.connected = False
            resp = self.STOU()
        if resp[:3] not in STOU_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def APPE(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('APPE ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on APPE command, trying again\n')
            self.connected = False
            resp = self.APPE(pathname)
        if resp[:3] not in APPE_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def ALLO(self, decimal1, decimal2):
        """
        :type decimal1, decimal2: str
        :rtype: str
        """
        self.send_cmd('ALLO ' + decimal1 + ' ' + decimal2)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on ALLO command, trying again\n')
            self.connected = False
            resp = self.ALLO(decimal1, decimal2)
        if resp[:3] not in ALLO_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def REST(self, marker):
        """
        :type marker: str
        :rtype: str
        """
        self.send_cmd('REST ' + marker)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on REST command, trying again\n')
            self.connected = False
            resp = self.REST(marker)
        if resp[:3] not in REST_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def RNFR(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('RNFR ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on RNFR command, trying again\n')
            self.connected = False
            resp = self.RNFR(pathname)
        if resp[:3] not in RNFR_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def RNTO(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('RNTO ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on RNTO command, trying again\n')
            self.connected = False
            resp = self.RNTO(pathname)
        if resp[:3] not in RNTO_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def ABOR(self):
        """
        
        :rtype: str
        """
        self.send_cmd('ABOR')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on ABOR command, trying again\n')
            self.connected = False
            resp = self.ABOR()
        if resp[:3] not in ABOR_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def DELE(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('DELE ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on DELE command, trying again\n')
            self.connected = False
            resp = self.DELE(pathname)
        if resp[:3] not in DELE_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def RMD(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('RMD ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on RMD command, trying again\n')
            self.connected = False
            resp = self.RMD(pathname)
        if resp[:3] not in RMD_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def MKD(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('MKD ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on MKD command, trying again\n')
            self.connected = False
            resp = self.MKD(pathname)
        if resp[:3] not in MKD_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def PWD(self):
        """
        
        :rtype: str
        """
        self.send_cmd('PWD')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on PWD command, trying again\n')
            self.connected = False
            resp = self.PWD()
        if resp[:3] not in PWD_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def LIST(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('LIST ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on LIST command, trying again\n')
            self.connected = False
            resp = self.LIST(pathname)
        if resp[:3] not in LIST_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def NLST(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('NLST ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on NLST command, trying again\n')
            self.connected = False
            resp = self.NLST(pathname)
        if resp[:3] not in NLST_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def SITE(self, string):
        """
        :type string: str
        :rtype: str
        """
        self.send_cmd('SITE ' + string)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on SITE command, trying again\n')
            self.connected = False
            resp = self.SITE(string)
        if resp[:3] not in SITE_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def SYST(self):
        """
        
        :rtype: str
        """
        self.send_cmd('SYST')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on SYST command, trying again\n')
            self.connected = False
            resp = self.SYST()
        if resp[:3] not in SYST_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def STAT(self, pathname):
        """
        :type pathname: str
        :rtype: str
        """
        self.send_cmd('STAT ' + pathname)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on STAT command, trying again\n')
            self.connected = False
            resp = self.STAT(pathname)
        if resp[:3] not in STAT_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def HELP(self, string):
        """
        :type string: str
        :rtype: str
        """
        self.send_cmd('HELP ' + string)
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on HELP command, trying again\n')
            self.connected = False
            resp = self.HELP(string)
        if resp[:3] not in HELP_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def NOOP(self):
        """
        
        :rtype: str
        """
        self.send_cmd('NOOP')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on NOOP command, trying again\n')
            self.connected = False
            resp = self.NOOP()
        if resp[:3] not in NOOP_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp

    def FEAT(self):
        """
        
        :rtype: str
        """
        self.send_cmd('FEAT')
        try:
            resp = self.get_resp()
        except EOFError:
            sys.stderr.write('ERROR: Disconnected on FEAT command, trying again\n')
            self.connected = False
            resp = self.FEAT()
        if resp[:3] not in FEAT_acceptable:
            raise error.ImpossiburuAnswer(resp)
        return resp
