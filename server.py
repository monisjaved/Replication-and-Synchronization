from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from xmlrpclib import ServerProxy
import httplib
import xmlrpclib
from sys import argv
from socket import gethostname
import socket
import traceback
import threading


def deposit(acnt,amt):
    '''server side deposit function
    to be called by coordinator
    args: acnt [account number]
            amt [amount]'''
    global accounts
    global log_file_handler
    global op_ids
    try:
        # create acccount if not present
        if acnt not in accounts:
            accounts[acnt] = 0
        accounts[acnt] += int(amt)
        # write to file and flush so it gets written instantly
        log_file_handler.write(str(op_ids)+" "+str(acnt)+" "+str(amt)+"\n")
        log_file_handler.flush()
        op_ids += 1
        return accounts[acnt]
    except Exception as e:
        print(traceback.format_exc())
        return False

def withdraw(acnt,amt):
    '''server side withdraw function
    to be called by coordinator
    args: acnt [account number]
            amt [amount]'''
    global accounts
    global log_file_handler
    global op_ids
    try:
        # create acccount if not present
        if acnt not in accounts:
            accounts[acnt] = 0
        accounts[acnt] -= int(amt)
        amt = accounts[acnt]
        # write to file and flush so it gets written instantly
        log_file_handler.write(str(op_ids)+" "+str(acnt)+" "+str(amt)+"\n")
        log_file_handler.flush()
        op_ids += 1
        return accounts[acnt]
    except Exception as e:
        print e
        return False

def balance_check(acnt):
    '''server side balance check function
    to be called by coordinator
    args: acnt [account number]'''
    global accounts
    global log_file_handler
    global op_ids
    try:
        # create acccount if not present
        if acnt not in accounts:
            accounts[acnt] = 0
        amt = accounts[acnt]
        # write to file and flush so it gets written instantly
        log_file_handler.write(str(op_ids)+" "+str(acnt)+" "+str(amt)+"\n")
        log_file_handler.flush()
        op_ids += 1
        return accounts[acnt]
    except Exception as e:
        print e
        return False

def resynch(tuple_data):
    '''resynch function to resync when crashed
    args: tuple_data [data from other servers
                        passed from coordinator]'''
    global coordinator
    global server_name
    global op_ids
    flag = True
    log_file_handler.seek(-1,2)
    try:
        # dont do anything if no new log
        if len(tuple_data) == 0:
            return 'RESYNCH-DONE'
        for i in xrange(len(tuple_data[0])):
            # iterate through log and if logs from both other servers are same
            # then write it to our log
            print tuple_data[0][i],tuple_data[1][i]
            if tuple_data[0][i] == tuple_data[1][i] and len(tuple_data[0][i]) == 3:
                log_file_handler.write(" ".join(tuple_data[0][i])+"\n")
                log_file_handler.flush()
                op_id,acnt,amt = tuple_data[0][i]
                # load accounts in memory
                accounts[acnt] = int(amt)
                op_ids += 1
            else:
                flag = False

        if flag:
            return 'RESYNCH-DONE'
        else:
            return False
    except Exception as e:
        print(traceback.format_exc())

def get_op_count():
    '''get count of operations
        to be called by coordinator'''
    global op_ids
    return op_ids

def get_logs(op_id):
    '''get logs from the operation id
        to be called by coordinator'''
    global log_file_name
    temp_log_handler = open(log_file_name,'r')
    # read all logs if not blank line [to avoid last line read]
    log_tuples = [log.split() for log in temp_log_handler.read().split("\n") if log != ""]
    return log_tuples[(op_id-1):]

def ping():
    '''ping command to see if server is alive'''
    return True

        
def main():
    global log_file_handler
    global accounts
    global op_ids
    global server_name
    global server_ip
    global coordinator
    global log_file_name

    
    try:
        if len(argv) < 5:
            raise IndexError()
        connection = argv[1]
        port_num = int(argv[2])
        server_name = argv[3]
        log_file_name = argv[4]
        alive = ''
        if len(argv) > 5:
            alive = 'ALIVE'
    except IndexError:
        print "use: python server.py <coordinator_ip:port_num> <server_port_num> <server_name> <log_file_name> <alive(optional)>"
        exit()

    while True:
        op_ids = 1
        accounts = {}
        # open file and load accounts into memory
        try:
            log_file_handler = open(log_file_name,'r+')
            for lines in log_file_handler.read().split("\n"):
                if len(lines.split(" ")) == 3:
                    op_id,acnt,amt = lines.split(" ")
                    accounts[acnt] = int(amt)
                    op_ids += 1
            log_file_handler.seek(0,2)
        except Exception as e:
            print e
            print 'unable to use log file create file and try again'
            exit(0)

        # connect to coordinator using server hello
        try:
            coordinator = ServerProxy('http://' + connection)
            if alive == 'ALIVE':
                alive += " " + str(op_ids)
            # get local ip [can be hardcoded for each machine if no internet access]
            server_ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
            result = coordinator.server_hello(server_name,server_ip,port_num,alive)
            # server crash functionality
            if 'ALIVE' in alive:
                if not resynch(result):
                    raise Exception('Error resynching')
                else:
                    coordinator.resynch_done(server_name,server_ip,port_num)
                    alive = ''
        except Exception as e:
            print 'unable to connect to coordinator',e
            exit(0)

        # create rpc server to be called by the coordinator and register functions
        try:    
            server = SimpleXMLRPCServer(
                ('', port_num),
                allow_none=True)
            server.register_introspection_functions()
            server.register_function(deposit)
            server.register_function(withdraw)
            server.register_function(balance_check)
            server.register_function(resynch)
            server.register_function(get_op_count)
            server.register_function(get_logs)
            server.register_function(ping)
            server.serve_forever()
        except KeyboardInterrupt:
            # crash functionality test
            server.server_close()
            alive = 'ALIVE'
        except Exception as e:
            print e
            exit(0)

if __name__ == "__main__":  
    main()