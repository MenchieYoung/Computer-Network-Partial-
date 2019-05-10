import SocketServer
import threading
from utils import *
import sys

class MyUDPRequestHandler(SocketServer.DatagramRequestHandler):
    # Override the handle() method
    def handle(self):
        global nextseq
        global receiver_buffer
        global flag
        global datafile

        #local_socket.settimeout(5)  # receiver closes idle connection after 5 seconds
        while True:
            try:
                # Print the name of the thread
                print("Thread Name:{}".format(threading.current_thread().name))
                # datagram = self.rfile.readline().strip()
                datagram = self.request[0]#.strip()   # finally find a way to correctly read the datagram as recv...
                #print("Datagram Recieved from client is:".format(datagram))
                message = channel(datagram)

                if message is None:
                    print("dropped")
                    continue
                #else:
                csum, rsum, seqnum, flag, data = extract_packet(message)
                # print "seqnummmmm, nextseqqqqq", seqnum, "*****", nextseq
                # print "csum, rsum", csum, "++++++", rsum
                #print "data", data
                # #Send a message to the client
                if nextseq == -1:
                    # if packet is not corrupted
                    if csum == rsum:
                        #case when initial packet is sent out of order
                        if flag == DATA_OPCODE or flag == END_OPCODE:



                        #if initial packet is the last packet
                        if flag == SPECIAL_OPCODE:
                            #  UDPServerObject.shutdown()
                            break
                            # return
                            # UDPServerObject.shutdown()

                elif csum != rsum:


                elif seqnum > nextseq:

                # case when the packet is GOOD!
                elif seqnum == nextseq:

                    # print "receiver_buffer", receiver_buffer[nextseq]
                    while nextseq in receiver_buffer:

                    ack = make_ack(nextseq)
                    socket = self.request[1]
                    socket.sendto(ack, self.client_address)
                    #self.wfile.write(ack.encode(), ServerAddress)

                    if flag == END_OPCODE:
                        print("\n last packet received.")
                        #UDPServerObject.shutdown()
                        #UDPServerObject.server_close()
                        return


                            #self.wfile.write("Message from Server! Hello Client".encode())
            except Exception as err:
                print('timeout', err)

def write_data():
    global datafile
    # can't write this way, don't know why..., will be empty
    # for data in datafile:
    #     print "data", data
    with open(file_name, 'wb+') as dl:
        dl.write(datafile)



if __name__ == "__main__":
    #
    # def usage():
    #     print("Usage: python Receiver2.py Outputfile ReceiverAddress ReceiverPort")
    #     exit()

    # if len(sys.argv) < 4:
    #     usage()
    #     sys.exit(-1)
    print "Please type the output filename"
    file_name = sys.stdin.readline().strip()
    print "waiting for file"
    # file_name = sys.argv[1]
    # address = sys.argv[2]
    # port = int(sys.argv[3])

    address = "localhost"
    port = 6789
    #file_name = "./text/rece_file.txt"
    ServerAddress = (address, port)

    nextseq = -1
    receiver_buffer = {}  # buffer for storing out of order packets
    datafile = ""

    # ServerAddress = ("localhost", 6789)
    UDPServerObject = SocketServer.ThreadingUDPServer(ServerAddress, MyUDPRequestHandler)
    # UDPServerObject.timeout = 0.003
    # UDPServerObject.handle_request()

    try:
        UDPServerObject.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt: #Exception as e: #KeyboardInterrupt:
        write_data()
    finally:
        UDPServerObject.server_close()



