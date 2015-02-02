#!/usr/bin/python

import zmq
import time
import serial
import threading

NB_BUTTON = 10

class ButtonReplay(threading.Thread):
    def __init__(self, eventFilename):
        threading.Thread.__init__(self)
        self.daemon = True
        self.isRunning = True

        self.eventFilename = eventFilename

        self.time_ref = time.time()
        self.button_state = [0] * NB_BUTTON
        self.time_stamp = 0

    def kill(self):
        self.isRunning = False

    def run(self):
        with open(self.eventFilename, 'r') as f:
            while self.isRunning:            
                t = time.time() - self.time_ref
                strNextEvent = f.readline().strip()
                if strNextEvent:
                    nextEvent = eval(strNextEvent)
                    while t < nextEvent[1]:
                        t = time.time() - self.time_ref
                        time.sleep(0.001)
                    self.button_state[nextEvent[0]] = nextEvent[2]
                    self.time_stamp = t
                else:
                    time.sleep(1)

class ButtonEventRecorder(object):
    def __init__(self, buttonevent, filename):
        self.buttonevent = buttonevent
        self.buttonevent.add_callback(self.add_event)

        self.filename = filename

    def add_event(self, event):
        with open(self.filename, 'a') as f:
            f.writelines(["{}\n".format(event)])

class ButtonEvent(threading.Thread):
    def __init__(self, freq, button):
        threading.Thread.__init__(self)
        self.daemon = True
        self.isRunning = True

        if freq == 0:
            self.period = 0
        else:
            self.period = 1.0 / freq

        self.callback = []

        self.button = button
        self.state = [0] * NB_BUTTON

    def kill(self):
        self.isRunning = False

    def add_callback(self, clb):
        if not clb in self.callback:
            self.callback.append(clb)

    def del_callback(self, clb):
        if clb in self.callback:
            self.callback.remove(clb)

    def which_change(self, diff):
        if diff == 1:
            return True
        if diff == -1:
            return False

    def events(self, old_state, new_state):
        diff_state = [new_state - old_state for new_state, old_state in zip(new_state, old_state)]
        events = map(self.which_change, diff_state)
        return events

    def update(self):
        time_stamp = self.button.time_stamp
        new_state = self.button.button_state
        events = self.events(self.state, new_state)
        self.state = new_state

        for idx, e in enumerate(events):
            if e is not None:
                for clb in self.callback:
                    clb((idx, time_stamp, int(e)))

    def run(self):
        if not self.button.isAlive():
            self.button.start()
        while self.isRunning:
            t = time.time()
            self.update()
            time.sleep(max(0, self.period - time.time() + t))

class Button(threading.Thread):
    def __init__(self, time_ref=time.time(), port='/dev/ttyACM0', baudrate=115200):
        threading.Thread.__init__(self)
        self.daemon = True
        self.isRunning = True

        self.time_ref = time_ref
        self.ser = serial.Serial(port=port,
                                 baudrate=baudrate,
                                 parity=serial.PARITY_ODD,
                                 stopbits=serial.STOPBITS_TWO,
                                 bytesize=serial.SEVENBITS)

        self.button_state = [0] * NB_BUTTON
        self.time_stamp = 0

    def kill(self):
        self.isRunning = False

    def run(self):
        if not self.ser.isOpen():
            self.ser.open()
        while self.isRunning:
            try:
                self.button_state = [int(s) for s in (self.ser.readline().strip())]
            except ValueError:
                self.button_state = [0] * NB_BUTTON
            self.time_stamp = time.time() - self.time_ref
        self.ser.close()


class ButtonServer(threading.Thread):
    def __init__(self, button, addr='127.0.0.1', port=5555):
        threading.Thread.__init__(self)
        self.daemon = True
        self.isRunning = True

        self.button = button

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind('tcp://{}:{}'.format(addr, port))

    def kill(self):
        self.isRunning = False

    def run(self):
        if not self.button.isAlive():
            self.button.start()
        while self.isRunning:
            self.socket.recv()
            self.socket.send('{}'.format(self.button.button_state))
        self.socket.close()


class ButtonClient(threading.Thread):
    def __init__(self, freq=100, addr='127.0.0.1', port=5555, time_ref=time.time()):
        threading.Thread.__init__(self)
        self.daemon = True
        self.isRunning = True

        if freq == 0:
            self.period = 0
        else:
            self.period = 1.0 / freq

        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect('tcp://{}:{}'.format(addr, port))

        self.time_ref = time_ref
        self.button_state = [0] * NB_BUTTON
        self.time_stamp = 0

    def kill(self):
        self.isRunning = False

    def run(self):
        while self.isRunning:
            t = time.time()
            self.socket.send('')
            button_state_str = self.socket.recv()
            self.button_state = eval(button_state_str)
            self.time_stamp = time.time() - self.time_ref
            time.sleep(max(0, self.period - time.time() + t))
        self.socket.close()


class ButtonPersistOn(threading.Thread):
    def __init__(self, button, persistTime=1, freq=50):
        threading.Thread.__init__(self)
        self.daemon = True
        self.isRunning = True

        self.button = button
        if persistTime < 0:
            persistTime = 0
        self.persistTime = persistTime

        if freq == 0:
            self.period = 0
        else:
            self.period = 1.0 / freq

        self.time_ref = self.button.time_ref
        self.button_state = [0] * NB_BUTTON
        self.buttonOnTime = [0] * NB_BUTTON
        self.time_stamp = 0

    def kill(self):
        self.isRunning = False

    def run(self):
        if not self.button.isAlive():
            self.button.start()
        self.buttonOnTime = [time.time() -  10 * self.persistTime] * NB_BUTTON
        while self.isRunning:
            t = time.time()
            realButtonState = self.button.button_state
            for i in range(len(realButtonState)):
                if realButtonState[i] == 1:
                    self.buttonOnTime[i] = t
                self.button_state[i] = int(t <= self.persistTime + self.buttonOnTime[i])

            ## this is just for that class to look like other button but it really means nothing interresting
            self.time_stamp = t

            time.sleep(max(0, self.period - time.time() + t))


if __name__ == '__main__':
    mybut = Button()
    butserver = ButtonServer(mybut)
    butserver.start()

    butclient = ButtonClient(100)
    b = ButtonEvent(100, butclient)

    def p(event):
        print event

    b.add_callback(p)

    b.start()

    while True:
        resp = raw_input('Type quit to exit: ')
        if resp == 'quit':
            break

    b.kill()
    butserver.kill()

    b.join()
    butserver.join()
