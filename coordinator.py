from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from threading import Thread
import httplib
import xmlrpclib
from sys import argv
from socket import gethostname
from time import sleep
import traceback

def client_hello(client_name):
    '''handshake function for client
    add client to client list
    args: client_name [client name]'''
    global clients
    try:
        if client_name not in clients:
            clients.append(client_name)
        return 'DONE'
    except:
        return 'FAILURE'

def deposit(acnt,amt):
    '''coordinator side deposit function
    forwards the request to all active servers
    args: acnt [account number]
            amt [amount]'''
    global server_conns
    global account
    success_list = []
    # if any action on account or not in normal mode then sleep
    while acnt in account or op_mode != 'NORMAL':
        sleep(5)
    account.append(acnt)
    for server in server_conns:
        # forward request to all servers
        try:
            success_list.append(server_conns[server].deposit(acnt,amt))
        except httplib.CannotSendRequest:
            del server_conns[server]
    account.remove(acnt)
    if len(set(success_list)) == 1 and success_list[0] != False:
        # return if valid data received from all servers
        return success_list[0]
    else:
        return False

def withdraw(acnt,amt):
    '''coordinator side withdraw function
    forwards the request to all active servers
    args: acnt [account number]
            amt [amount]'''
    global server_conns
    global account
    success_list = []
    # if any action on account or not in normal mode then sleep
    while acnt in account or op_mode != 'NORMAL':
        sleep(5)
    account.append(acnt)
    for server in server_conns:
        # forward request to all servers
        try:
            success_list.append(server_conns[server].withdraw(acnt,amt))
        except httplib.CannotSendRequest:
            del server_conns[server]
    print success_list
    account.remove(acnt)
    if len(set(success_list)) == 1 and success_list[0] != False:
        # return if valid data received from all servers
        return success_list[0]
    else:
        return False

def balance_check(acnt):
    '''coordinator side withdraw function
    forwards the request to all active servers
    args: acnt [account number]'''
    global server_conns
    global account
    success_list = []
    # if any action on account or not in normal mode then sleep
    while acnt in account or op_mode != 'NORMAL':
        sleep(5)
    account.append(acnt)
    for server in server_conns:
        # forward request to all servers
        try:
            success_list.append(server_conns[server].balance_check(acnt))
        except httplib.CannotSendRequest:
            del server_conns[server]
    print success_list
    account.remove(acnt)
    if len(set(success_list)) == 1 and success_list[0] != False:
        # return if valid data received from all servers
        return success_list[0]
    else:
        return False

def server_hello(server_name,server_ip,port_num,optional_msg = ''):
    '''handshake function for server
    resyncs server if recovered after crash [ALIVE in optional_msg with last op id]
    add connection to dictionary for use later
    args: server_name [server name]
            server_ip [server ip]
            port_num [port number]
            optional_msg [usually empty if normal connection else will have alive]'''
    global servers
    global server_conns
    global op_mode
    try:
        # add server name to servers dictionary
        if server_name not in servers:
            servers[server_name] = port_num
        # check if normal connection or connecting after crash
        if 'ALIVE' in optional_msg:
            op_mode = 'RESYNCH'
            # get last operation number from message
            failed_log_number = int(optional_msg.split()[1])
            # print 'failed after',failed_log_number
            log_data = []
            # get logs from all other servers and forward to serfver
            for sname,sconn in server_conns.iteritems():
                if sname != server_name:
                    log_data.append(sconn.get_logs(failed_log_number))
            return log_data
        else:
            # add connection to active connection dictionary
            server_conns[server_name] =  ServerConnection(str(server_ip)+":"+str(port_num)).server
            # only work if more than 2 servers
            if len(server_conns) >= 2:
                op_mode = 'NORMAL'
            return 'DONE'
    except Exception as e:
        print(traceback.format_exc())
        return 'FAILURE'

def resynch_done(server_name,server_ip,port_num):
    '''coordinator function to be called when crashed server has 
    successfully recovered and resynced
    args: server_name [server name]
            server_ip [server ip]
            port_num [port number]'''
    global op_mode
    server_conns[server_name] =  ServerConnection(str(server_ip)+":"+str(port_num)).server
    op_mode = 'NORMAL'


def heartbeat():
    '''heartbeat function to check alive servers at regular intervals'''
    global server_conns
    while True:
        for sname,sconn in server_conns.iteritems():
            # if ping does not return true then remove from active server dict
            try:
                if not sconn.ping():
                    del server_conns[sname]
                    # change mode from normal if less than 2 servers
                    if len(server_conns.keys() < 2):
                            op_mode = 'NEED MORE SERVERS'
                    else:
                            op_mode = 'NORMAL'
            except httplib.CannotSendRequest:
                del server_conns[sname]
        sleep(10)


class TimeoutTransport(xmlrpclib.Transport):
    timeout = 10.0
    def set_timeout(self, timeout):
        self.timeout = timeout
    def make_connection(self, host):
        h = httplib.HTTPConnection(host, timeout=self.timeout)
        return h      

class ServerConnection():
    def __init__(self, address_port):
        (self.address, self.port_num) = address_port.split(':')
        self.server = xmlrpclib.ServerProxy(
            'http://'+self.address+':'+self.port_num,
            transport=TimeoutTransport())
        
def main():
    global clients
    global servers
    global op_mode
    global account
    global server_conns

    clients = []
    servers = {}
    op_mode = 'NORMAL'
    account = []
    server_conns = {}
    try:
        if len(argv) != 2:
            raise IndexError()
        port_num = int(argv[1])
    except IndexError:
        print "use: python server.py <port_num>"
        exit(0)
        
    try:    
        server = SimpleXMLRPCServer(
            ('', port_num),
            allow_none=True)
    except Exception as e:
        print e
        print "unable to create server"
        exit(0)

    # run heartbeat function as a background thread 
    background_thread = Thread(target=heartbeat, args=())
    background_thread.daemon = True
    background_thread.start() 
    # start rpc server and register functions
    server.register_introspection_functions()
    server.register_function(deposit)
    server.register_function(withdraw)
    server.register_function(balance_check)
    server.register_function(client_hello)
    server.register_function(server_hello)
    server.register_function(resynch_done)
    server.serve_forever()
    
if __name__ == "__main__":
    main()
