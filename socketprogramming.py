from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8


def checksum(str):
     csum = 0
     countTo = (len(str) / 2) * 2

     count = 0
     while count < countTo:
         thisVal = str[count+1] * 256 + str[count]
         csum = csum + thisVal
         csum = csum & 0xffffffff
         count = count + 2
     if countTo < len(str):
         csum = csum + str[len(str) - 1]
         csum = csum & 0xffffffff

     csum = (csum >> 16) + (csum & 0xffff)
     csum = csum + (csum >> 16)
     answer = ~csum
     answer = answer & 0xffff
     answer = answer >> 8 | (answer << 8 & 0xff00)
     return answer


def receiveOnePong(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        #Fill in start
        #Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28] #ICMP header is 8 bytes right after IP header(20 bytes)
        icmpType, code, mychecksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if icmpType == 0 and packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent
        #Fill in end
        timeLeft = timeLeft - howLongInSelect

        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    # Make a dummy header with a 0 checksum.
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)

    #[ 8bytes header] [1 double to store time]

    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    # Convert 16-bit integers from host to network byte order.
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")

    # SOCK_RAW is a powerful socket type. For more details see:
    #http: // sock - raw.org / papers / sock_raw
    # Fill in start
    # Create Socket here
    mySocket = socket(AF_INET, SOCK_DGRAM, icmp)
    # Fill in end


    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePong(mySocket, myID, timeout, destAddr)

    mySocket.close()
    return delay


def ping(host, timeout=1):
    dest = gethostbyname(host)
    print("Pinging " + host + '(' + dest + ") using Python:")
    print("")
    # Send ping requests to a server separated by approximately one second
    while 1:
        delay = doOnePing(dest, timeout)
        print("{} s".format(delay))
        time.sleep(1)  # one second

ping("127.0.0.1")