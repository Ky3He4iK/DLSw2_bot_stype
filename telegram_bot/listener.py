import socket
from threading import Thread

_thread = None  # private variables in python so private
_stop_word = b"Stop\n"
_port = 4717


def _listener(callback, port, accept_addresses):
    _bufferSize = 200
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', port))
        looping = True
        s.listen(10)
        while looping:
            client_socket, client_address = s.accept()
            if client_address[0] not in accept_addresses and client_address[0] not in ('127.0.0.1', "::1"):
                client_socket.close()
                continue
            msg = client_socket.recv(_bufferSize)
            client_socket.close()
            if msg == _stop_word:
                print("Stopping")
                break
    finally:
        s.close()  # Must close connection to port
        callback()  # if can't establish listener on port, just stop bot's work


def listen_for_interrupt(callback, port=4717, stop_word=b"Stop", accept_addresses=()):
    """
     Listens given port and calls [callback] if got message from one of [accept_addresses] with content [stop_word]
    """
    global _thread, _stop_word, _port
    if _thread:
        raise RuntimeError("Another instance has already listening. Only one instance possible")
    _thread = Thread(name="Listener", target=_listener, args=(callback, port, accept_addresses))
    _thread.start()
    _stop_word = stop_word + b'\n'
    _port = port


def stop():
    """
    If you need to stop bot from external function, call this
    """
    global _thread
    if _thread:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', _port))
        s.send(_stop_word)
        s.close()
    _thread = None
