import sys
from socket import *
from utils import *
import time, struct, random
import signal
import time
from threading import Thread
import functools
import timeout_decorator
import threading

THRES_HOLD = 10
SLOW_START_WND_SIZE = 1
UPPER_BOUND = 0.5

#from PA2.wrapt_timeout_decorator import *
# print(sys.path)
# sys.path.append(os.path.abspath('../../'))

"""
https://github.com/bitranox/wrapt_timeout_decorator
https: // stackoverflow.com / questions / 40305424 / using - one - socket - in -udp - chat - using - threading
https://pythontic.com/socketserver/threadingudpserver/introduction
"""

#TODO make pkt 0 must be successfully transmited - finished
#TODO congestion control: does pkt loss include all abnormal behaviour like ack corrupt, duplicate acks and timeout? - finished
#TODO adjust timeout - finished

"""
1. Reliable, using sliding window
    Be reliable under: 
        Loss
        Corruption
        Re-ordering
        Delay
2. Can accept ACK from Receiver: 
    a. Ack packet with invalid checksum should be ignored. 
    b. Can place sequence number 0 in the start packet.
3. 500ms timeout to automatically retransmit -> adaptive timeout(Bonus Part)
    Fast retransmission: 3 duplicate acks, will retransmit the corresponding packet without waiting for timeout.
    Only retransmit the oldest unacknowledged packet.
4. Support a window size W of at most WND_SIZE packets -> adaptive window size(Bonus Part)
5. Handle arbitrary files: image/text/...
6. Ignore invalid ACK with wrong checksum.
7. Sender must not produce console output during normal execution, except exception message.
8. Correctness, time of completion, number of packets sent/resent. <Will be compared with TA's>
9. Pipeline.
"""

# specify an initial sequence number
# append checksum to each packet
# Function that generating checksum/ making packet, extracting fields from a packet is in utils.py
# read_file function that divides the file into chunks of size chunk_size

"""
class DuplicateError(Exception):
    def __init__(self, i):
        self.i = i  
"""

class RttUtils:
    def __init__(self, sample_rtt):


    def update(self, estimated_rtt):

        return self.timeout_interval, estimated_rtt

class Sender:
    global timeout_interval
    timeout_interval = 0.3
    global force_kill
    force_kill = False

    def __init__(self, filename, clientSocket, ip, port):
        try:
            self.filename = open(filename, 'rb')
        except Exception as e:
            print 'The input file does not exist! Please specify a correct input file.'
            sys.exit(1)

        self.rtt = {}
        self.estimated_rtt = 0.5
        self.timeout_interval = 0.3
        self.pkts = self.make_pkt_from_data(filename)  # list of str
        #self.my_timeout()
        global timeout_interval
        timeout_interval = self.timeout_interval

        ack = None
        # Guarantee the first pkt is successfully arrived.
        while not ack:
            try:
                self.transmit_wnd(clientSocket, ip, port, [self.pkts[0]], 0, 0)
                self.rtt[0] = time.time()
                ack = self.wait_ack(clientSocket)
                ...
                #print 'estimated_rtt: ' + str(self.estimated_rtt)
                #print 'timeout_interval: ' + str(self.timeout_interval)
                if ack:
                    break
            except Exception as e:
                print "the first packet's error: ", e

    # For Linux:
    #def set_timeout(num, callback):
    # def set_timeout(self, num):
    #     """
    #     https://blog.csdn.net/zelinhehe/article/details/77529844
    #     """
    #     num = self.timeout_interval
    #     def wrap(func):
    #         def handle(signum, frame):
    #             raise RuntimeError
    #
    #         def to_do(*args, **kwargs):
    #             try:
    #                 signal.signal(signal.SIGALRM, handle)
    #                 signal.alarm(num)
    #                 print 'start alarm signal.'
    #                 r = func(*args, **kwargs)
    #                 print 'close alarm signal.'
    #                 signal.alarm(0)
    #                 return r
    #             except RuntimeError as e:
    #                 print(e)
    #                 #callback()
    #         return to_do
    #     return wrap

    #@staticmethod
    #@classmethod
    def my_timeout(self):  # For Windows
        # timeout = self.timeout_interval
        global timeout_interval
        global force_kill

        def deco(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                global force_kill
                res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, timeout_interval))]
                def newFunc():
                    try:
                        res[0] = func(*args, **kwargs)
                    except Exception, e:
                        res[0] = e

                #res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, timeout_interval))]

                t = Thread(target=newFunc)
                t.daemon = True
                try:
                    t.start()
                    t.join(timeout_interval)  # wait timeout_interval secs for thread to finish it's work
                    #####
                    # if not t.is_alive():
                    #     print "***********"
                    #     # if force_kill:
                    #     #     t.terminate()
                    #     return res[0]
                    #####
                except Exception, je:
                    print 'error starting thread'
                    raise je

                """Don't know why, but it repeated too may times. If I use return kill it, it will work as well. It will have an error, and won't return the real ack. """
                # if t.is_alive():
                #     if force_kill:
                #         force_kill = False
                #         return res[0]

                ret = res[0]
                if isinstance(ret, BaseException):
                    raise ret

                return ret

            return wrapper

        return deco

    #@set_timeout(1)
    #@self.my_timeout()
    #@staticmethod
    #@my_timeout.__get__(timeout_interval)
    #@my_timeout(None, timeout_interval) # also works
    #@my_timeout.__get__(timeout_interval)
    #@timeout_decorator.timeout(timeout_interval)
    @my_timeout(None)
    def wait_ack(self, clientSocket): #, pkts, ip, port, i):

            try:
                ack, serverAddress = clientSocket.recvfrom(2048)
                if ack:
                    checked_sum, received_sum, ack_seq, flag, data = extract_packet(ack)
                    #print ["wait_ack received ack, ack_seq is", ack_seq]
                    can_break = True
                    force_kill = True
                    return ack
            except Exception as e:
                print 'timeout, closing socket', e
                clientSocket.close()

    # def wait_ack(self, clientSocket):
    #     global timeout_interval
    #     func = self.my_timeout(timeout_interval=timeout_interval)(self._wait_ack(clientSocket))
    #     try:
    #         func()
    #     except Exception as e:
    #         print "11111111", e
    #         pass  # handle errors here

    def transmit_wnd(self, clientSocket, ip, port, pkts, send_start, send_end):
        """
        :param clientSocket:
        :param ip:
        :param port:
        :param pkts: all the packets from seqnum = 0 to seqnum = last pkt seqnum
        :param wnd_start:
        :param wnd_end:
        :return:
        """
        try:
            i = send_start
            while i <= send_end:  # window
                clientSocket.sendto(pkts[i], (ip, port))
                checked_sum, received_sum, seqnum, flag, data = extract_packet(pkts[i])
                self.rtt[seqnum] = time.time()
                #print ("transmit_wnd: send ", i, "-th pkt, ", "seqnum of pkt is ", seqnum)
                #print ("pkts csum is", checked_sum, "pkt received_sum is: ", received_sum)
                i += 1
        except timeout:
            print('timeout, closing socket')
            clientSocket.close()

    def retransmit_oldest(self, clientSocket, pkts, ip, port, i):
        """
        recursion will cause weird situation, maybe not because recursion, but the wait_ack throw clientsocket timeout exception is confusing.
        try:
            checked_sum, received_sum, seqnum, flag, data = extract_packet(pkts[i])
            print seqnum, i
            clientSocket.sendto(pkts[i], (ip, port))
            print "22222"
            s = time.time()
            print "start: ", time.time()
            ack = wait_ack(clientSocket)
            print "end: ", time.time()
            e = time.time()
            print "interval:", s - e
            checked_sum, received_sum, ack_seq, flag, data = extract_packet(ack)
            if checked_sum != received_sum:
                raise ValueError("corrupt ack")
            print "retransmit succeed"
            return
        #if not ack:
        #   raise ValueError("still need retransmit")
        except Exception as e:  # RuntimeError:
            print "retransmit error:", e
            retransmit_oldest(clientSocket, pkts, ip, port, i)
        #return ack
        """
        #can_break = False
        global timeout_interval
        ack = None
        #while not ack:
        try:
            self.rtt[i] = time.time()   # update time for retransmit pkt
            ...
            return ack

        except Exception as e:  # RuntimeError:
            print "retransmit error:", e

    def reliable_transmit(self, clientSocket, pkts, ip, port):
        """
        :param clientSocket:
        :param pkts:
        :param ip:
        :param port:
        :param map: map seqnum to i
        :return:
        """
        global timeout_interval
        wnd_size_var = SLOW_START_WND_SIZE
        send_start = 1 #0, will send 0 seperately
        wnd_start = 0
        send_end = wnd_size_var #wnd_size_var - 1  # = wnd_end
        n = len(pkts)
        #print("n", n)
        ack_seq = 0
        if_retransmit = False
        ack = None
        i = 0
        ack_dic = {}  # ack_dic = {"": 0 for _ in range(wnd_size_var)}
        mark_send_end = 0
        retransmit_ack = None

        while True:
            # ack_dic = {}  # ack_dic = {"": 0 for _ in range(wnd_size_var_var)}
            try:
                # if send_start >= n:
                #     break
                #print "current window size:", wnd_size_var
                if send_start <= send_end and mark_send_end != send_end:
                    #print " to be sended pkt in current window is from pkt", send_start, " to", send_end

                # while i < send_end - send_start:
                #re_checked_sum, re_received_sum, re_ack_seq, re_flag, re_data = extract_packet(retransmit_ack)
                #cur_ack = wait_ack(clientSocket)
                #checked_sum, received_sum, ack_seq, flag, data = extract_packet(cur_ack)
                if if_retransmit and retransmit_ack:

                else:
                    ack = self.wait_ack(clientSocket)  # if retransmit get ack seq = 5, means before packet 5 is ok. Then here will get larger than 5.

                if ack:
                    #i += 1

                    #print "received ack is: ", ack, "ack_seq is: ", ack_seq


                        #print "too large interval, bad for multi-thread", timeout_interval
                        timeout_interval = UPPER_BOUND
                    #print 'estimated_rtt: ' + str(self.estimated_rtt)
                    #print 'modified timeout_interval: ' + str(self.timeout_interval)
                    # del useless ack in dic to save space.
                    # for i in range(wnd_start, ack_seq):
                    #     if ack_dic[i]:
                    #         del ack_dic[i]

                    #ack_dic[ack_seq] = ack_dic.get(ack_seq, 0) + 1
                    if ack_dic[ack_seq] >= 3:
                        #i_pkt_seq_of_wrong_ack = ack_seq  # ack_seq - 1 corresponding to the pkt the invoke ack_seq, which is the lost pkt
                        #i = i_pkt_seq_of_wrong_ack
                        wnd_start = ack_seq
                        raise ValueError("Duplicate Ack, Will Do Fast Retransmit")  #DuplicateError(i_pkt_seq_of_wrong_ack)
                    elif checked_sum != received_sum:
                        wnd_start = ack_seq
                        raise ValueError("Corrupted Ack")
                    else:
                        if wnd_size_var + 1 < THRES_HOLD:
                            wnd_size_var += 1
                        else:  # CA

                        # moving sliding window
                        send_start = max(wnd_start, send_end + 1)
                        if ack_seq < n:
                            wnd_start = ack_seq
                            if ack_seq + wnd_size_var < n:
                                send_end = wnd_start + wnd_size_var
                            else:
                                send_end = n - 1
                    # ack = wait_ack(clientSocket)

                if ack_seq >= n:
                    break
                # if i == wnd_size_var:
                #     i = 0
            except Exception as e: # or DuplicateError(i):

                    break
                #print "start retransmit"
                retransmit_ack = self.retransmit_oldest(clientSocket, pkts, ip, port, i=wnd_start)

    def make_pkt_from_data(self, file_name):
        f = read_file(file_name, chunk_size=DATA_LENGTH)  # DATA_LENGTH)
        # print(f)
        chunk = []
        try:

        except Exception as e:
            print e

        #print "chunk", chunk
        # 0-start;  1-data;  2-end;  3-special;   4-ACK
        packet_with_csum = []
        packet_with_csum.append(make_packet(seqnum=0, data=chunk[0], flag=0))

        # for i in range(num_pkt):
        #     checked_sum, received_sum, seqnum, flag, data = extract_packet(packet_with_csum[i])
        #     map_seqnum_to_i[seqnum] = i
        return packet_with_csum


    def main(self):
        global timeout_interval
        start_time = time.clock()
        packet_with_csum = self.make_pkt_from_data(file_name) # list of str
        self.reliable_transmit(clientSocket=clientSocket, pkts=packet_with_csum, ip=udp_server_ip_address, port=udp_server_port)
        end_time = time.clock()
        print("start_time: {}, end_time: {}".format(start_time, end_time))
        # print("Sended: {}.".format(file_name))

def usage():
    print("Usage: python Sender.py InputFile ReceiverAddress ReceiverPort")
    exit()

if __name__ == '__main__':
    if len(sys.argv) < 4:

    sender = Sender(filename=file_name, clientSocket=clientSocket, ip=udp_server_ip_address, port=udp_server_port)
    #sender.main()

    #print("Client - Main thread started")
    ThreadList = []
    ThreadCount = 20
    # Create as many connections as defined by ThreadCount
    for index in range(ThreadCount):
        ThreadInstance = threading.Thread(target=sender.main())
        ThreadList.append(ThreadInstance)
        ThreadInstance.start()
    # Main thread to wait till all connection threads are complete
    for index in range(ThreadCount):
        ThreadList[index].join()




