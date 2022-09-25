import zmq


class Pushing:
    def __init__(self, port=5000):
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        self.socket.bind("tcp://*:{:d}".format(port))

    def put(self, msg):
        self.socket.send_json(msg)


class Pulling:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
        self.socket.connect("tcp://{}:{:d}".format(host, port))

    def get(self):
        msg = self.socket.recv_json()
        return msg