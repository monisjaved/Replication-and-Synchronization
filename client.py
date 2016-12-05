import xmlrpclib
import httplib
from sys import argv

def deposit(acnt, amt):
    '''client side deposit functionality
    args: acnt [account number]
            amt [amount]'''
    global coordinator
    if amt <= 0:
        print("Amount should be positive")
    # call coordinator deposit method
    elif str(coordinator.deposit(acnt, amt)) != "False":
        print("Successfully deposit %s to account %s!"%(amt, acnt))
    else:
        print("No such user or account, %s!"%(acnt))

def withdraw(acnt, amt):
    '''client side withdraw functionality
    args: acnt [account number]
            amt [amount]'''
    global coordinator
    if amt <= 0:
        print("Amount should be positive")
    # call coordinator deposit method
    elif str(coordinator.withdraw(acnt, amt)) != "False":
        print("Successfully withdraw %s from account %s!"%(amt,acnt))
    else:
        print("No such user or account, %s!"%(acnt))
    
def balance_check(acnt):
    '''client side balnce check functionality
    args: acnt [account number]'''
    global coordinator
    # call coordinator deposit method
    amt = coordinator.balance_check(acnt)
    if str(amt) != "False":
        print("The current balance of user %s is %s"%(acnt, amt))
    else:
        print("No such user or account, %s!"%(acnt))

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
        self.coordinator = xmlrpclib.ServerProxy(
            'http://'+self.address+':'+self.port_num,
            transport=TimeoutTransport())
        
def main():
    global coordinator
    try:
        if len(argv) < 3:
            print 'usage: python client.py <coordinator_ip:port number> <client name>'
            exit(0)

        coordinator = ServerConnection(argv[1]).coordinator
        if coordinator.client_hello(argv[2]) == 'FAILURE':
            print 'Error connecting to coordinator'
        while True:
            print '1. Deposit'
            print '2. Withdraw'
            print '3. Inquire'
            print '4. Quit'
            print 'Enter your response:\t',
            res = raw_input()
            if res == '1':
                print 'Account number:\t',
                acnt = raw_input()
                print '\nAmount:\t',
                amt = raw_input()
                deposit(acnt,amt)
            elif res == '2':
                print 'Account number:\t',
                acnt = raw_input()
                print '\nAmount:\t',
                amt = raw_input()
                withdraw(acnt,amt)
            elif res == '3':
                print 'Account number:\t',
                acnt = raw_input()
                balance_check(acnt)
            elif res == '4':
                break
            else:
                print 'Invalid Option'
    except Exception as e:
        print e 
        print 'Error'      
        
if __name__ == '__main__':
    main()