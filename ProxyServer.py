from socket import *
import sys
import os
import threading
global hostn_cache

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
    sys.exit(2)
# Create a server socket, bind it to a port and start listening

def get_host_name(filename):

def make_cache_path(filename):

def get_last_M_date(Last_M_Line):
    if "Last-Modified" in Last_M_Line:
        # get cache date
        return cache_date
    else:
        return None

def write_to_cache_send(tmpFile, buff, can_cache, msg):
    # write last modified date from buff to tmpFile/cache file
    if can_cache:

    # write html file to tmpFile
    # send msg to client

    # send message back to client

def recv(tcpCliSock, addr):
    global hostn_cache
    message = tcpCliSock.recv(2048)
    msg = tcpCliSock.makefile('r', 0) #client <-> proxyserver
    #message = msg.read(1024)   # read will return a string # proxy server read from client

    # store message client sending to proxy, and forward it to web server
    if message != "":
        message_temp = ""
        # for...
        message_temp += (lines + '\r\n')
    else:
        return

    if message != "":
        #print message.split()[1]
        filename = message.split(" ")[1].partition("/")[2]
        # if filename[-1] == "/":
        #     filename = filename[0:-1]
    else:
        return

    try:
        # Check whether the file exist in the cache
        print 'try to read from cache'
        
        f = open(filetouse[1:], "r") # if not exist, IOError
        outputdata = f.readlines()

        # return last modified date, or raise IOError to query the web server
        cache_Last_M_date = get_last_M_date(outputdata[0])
        print "cache_Last_M_date", cache_Last_M_date
        # if don't have the last modified date, we don't know if the cache is
        # up-to-date, thus need to query the web server through proxyserver.

        if not cache_Last_M_date:
            raise IOError
        fileExist = "true"
        print 'File Exists!'

        #if have last modified date in cache, we could send If-Modified-Since query
        if cache_Last_M_date:
            c_cache = socket(AF_INET, SOCK_STREAM)
            try:
                hostn = get_host_name(filename) # will be "www.xxx.xxx" at first then None
                if not hostn:
                    hostn = hostn_cache
                hostn_cache = hostn

                c_cache.connect((hostn, 80))
                print 'Socket connected to port 80 of the host to query If Modified'

                fileobj_cache = c_cache.makefile('r', 0)  # Instead of using send and recv, we can use makefile

                # fileobj_cache.write("GET " + "http://" + filename + " HTTP/1.0\n\n")
                #hostn_temp = get_host_name(filename)
                # if hostn == hostn_temp:
                fileobj_cache.write("...")
                # else:
                #     fileobj_cache.write("GET " + "/" + filename + " HTTP/1.0\n\n")
                fileobj_cache.write("Host: "...")
                fileobj_cache.write("If-Modified-Since: " + cache_Last_M_date + "\r\n")
                fileobj_cache.write("\r\n")

                buff_cache = fileobj_cache.readlines() #currecnt message
                if "304" in buff_cache[0]:
                    print "304 response after query If-Modified-Since"
                    print "Read From Cache"
                    #pass     # read from cache as following

                can_cache = False
                tmpFile = None
                if "200" in buff_cache[0]:
                    can_cache = True
                if can_cache:
                    print "200 response after query If-Modified-Since"
                    print "Cache out-of-date, Get From Web Page"
                    #if "www" not in filename:
                    #make_cache_path(filename)
                    # open the cache file, the cache will gone, then write as following
                    if filename[-1] == "/":
                        path = filename[0:-1]
                    else:
                        path = filename
                        
                    make_cache_path(path)
                    tmpFile = open("./" + path, "wb")
                    
                # hand all situations: 304, 200, 501, 404...
                write_to_cache_send(tmpFile, buff_cache, can_cache, msg)  # tmpFile can be None and can_cache = False at this time
                c_cache.close()

            except:
                print 'When cache exists and has last modified date, but an Error'

        msg.write("HTTP/1.0 200 OK\r\n")
        msg.write("Content-Type:text/html\r\n")
        msg.write("\r\n")

        for i in range(len(outputdata)):
            msg.write(outputdata[i])

        f.close()
        print "read from cache"


    except IOError:
        if fileExist == "false":
            # Create a socket on the proxyserver
            # Fill in start.
            c = socket(AF_INET, SOCK_STREAM)  # proxyserver -> server
            # Fill in end.
            hostn = get_host_name(filename)
            if not hostn:
                hostn = hostn_cache
            hostn_cache = hostn

            try:
                # Connect to the socket to port 80
                c.connect((hostn, 80))
                print 'Socket connected to port 80 of the host'

                # Create a temporary file on this socket and ask port 80 for the file requested by the client
                fileobj = c.makefile('r', 0)  # Instead of using send and recv, we can use makefile

                if "www" in filename:
                    if "/" in filename:
                        sections = filename.split("/")
                        print "sections", sections[1]
                        if len(sections) > 1:
                            secendory = sections[1]
                        fileobj.write("GET " + "/" + secendory + "/" + " HTTP/1.0\r\n")
                    else:
                        fileobj.write("GET " + "/" + " HTTP/1.0\r\n")
                else:
                    fileobj.write("GET " + "/" + filename + " HTTP/1.0\r\n")

                #If this line does not work, write separate lines for "Get .." and "Host:..
                fileobj.write("Host:" + hostn + "\r\n")

                #fileobj.write(message_temp)
                fileobj.write("\r\n")

                buff = fileobj.readlines()

                can_cache = False
                tmpFile = None

                if "200" in buff[0]:
                    can_cache = True
                if can_cache:
                    #if "www" not in filename:
                        #make_cache_path(filename)
                    #tmpFile = open('./' + hostn_cache + "/" + filename, "wb")
                    if filename[-1] == "/":
                        path = filename[0:-1]
                    else:
                        path = filename
                        
                    make_cache_path(path)
                    tmpFile = open("./" + path, "wb")

                write_to_cache_send(tmpFile, buff, can_cache, msg)
                # tmpFile can be None and can_cache = False at this time
                c.close()

            except Exception as e:
                print "Illegal request" + str(e)
        else:
            # HTTP response message for file not found
            # Fill in start.
            msg.write("HTTP/1.0 404 Not Found\r\n")
            msg.write("Content-Type:text/html\r\n")
            msg.write("\r\n")
            # Fill in end.

        # Close the client and the server sockets

    tcpCliSock.close()
    #tcpSerSock.close()

def main():
    global hostn_cahce
    hostn_cache = ""
    tcpSerSock = socket(AF_INET, SOCK_STREAM)
    tcpSerPort = 8080
    tcpSerSock.bind(('', tcpSerPort))
    tcpSerSock.listen(5)  # the maximum number of queued connections
    while 1:
        # Start receiving data from the client
        print 'Ready to serve...'
        tcpCliSock, addr = tcpSerSock.accept()
        print 'Received a connection from:', addr

        # tcpSerSock can listen more threads
        # after the client is connect, create a thread to pass the client socket

        t1 = threading.Thread(target=recv, args=(tcpCliSock, addr))
        t1.setDaemon(True)# Setting thread daemons
        t1.start()

if __name__ == '__main__':
    main()
