from pythonosc import dispatcher, osc_server
import argparse
import os
import sys
import time
import logging

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="pymuse.log",
                    level=logging.INFO,
                    format=LOG_FORMAT,
                    filemode='w')

logger = logging.getLogger()


class Headband:
    def __init__(self, **kwargs):
        # connection variables
        self.connection_status = [4, 4, 4, 4]
        self.connection_notified = False

        # brainwaves lists
        self.brainwave_theta = []
        self.brainwave_delta = []
        self.brainwave_alpha = []
        self.brainwave_beta = []
        self.brainwave_gamma = []
        # brainwave eeg
        self.brainwave_raw = []

        # set the default server info
        if "ip" in kwargs.keys():
            self.ip = kwargs['ip']
        else:
            self.ip = "127.0.0.1"

        if "port" in kwargs.keys():
            self.port = kwargs['port']
        else:
            self.port = 5000

        self.server = self.create_server(self.ip, self.port)

    def setServerInfo(self, ip, port):
        try:
            if isinstance(ip, str) and isinstance(port, int):
                # update the values and create server
                self.ip = ip
                self.port = port
                self.server = self.create_server(self.ip, self.port)
                # log the information
                logging.info("Server IP set to " + ip)
                logging.info("Server Port set to " + str(port))
        except BaseException:
            logging.error("setServerInfo: ip and/or port given is not valid")
            print("ERROR: IP and/or Port is not valid")
            sys.exit(1)

    def start_server(self):
        """ starts an osc server """
        print("[server ip:", self.ip, "] [server port:", self.port, "]")
        print("awaiting headband connection\n")
        # start the progam
        try:
            logging.info("server started")
            self.server.serve_forever()
        except KeyboardInterrupt:
            logging.debug("start_server: Program ended - KeyboardInterrupt")
            sys.exit(0)

    def stop(self):
        logging.info("server stopped")
        self.server.shutdown()

    def run(self):
        """ a method updates at 10hz """
        if self.check_connection():
            print(self.get_brainwaves())
            # print(self.get_raw_brainwaves())

    def exit_handler(self):
        print("Program End")
        pass

    def round_values(self, ls, dp=5):
        for val in ls:
            val = round(val, dp)
        return ls

    def connection_handler(self, addr, args, TP9, Fp1, Fp2, TP10):
        self.connection_status = [TP9, Fp1, Fp2, TP10]

    def check_connection(self):
        # ignore inital connection_status of [4,4,4,4]
        if type(self.connection_status[0]) is type(4):
            return True

        try:
            # if connection is good return true, else return false
            if all([self.connection_status[i] < 3 for i in range(4)]):
                # reset connection notification
                self.connection_notified = False
                return True
            else:
                # if the user hasn't been notified, then do so
                if not self.connection_notified:
                    logging.info("poor Connection - " +
                                 str(self.connection_status))
                    self.connection_notified = True
                    os.system('cls')
                    print("connection error:", self.connection_status)
                return False
        except KeyboardInterrupt:
            logging.debug(
                "check_connection: Program ended - KeyboardInterrupt")
            sys.exit(0)

    """ handlers organized from slowest to fastest """

    def brainwave_raw_handler(self, addr, *args):
        if self.check_connection():
            self.brainwave_raw = self.round_values(args[1:])

    def theta_abs_handler(self, addr, args, TP9, Fp1, Fp2, TP10):
        if self.check_connection():
            self.brainwave_theta = self.round_values([TP9, Fp1, Fp2, TP10])

    def delta_abs_handler(self, addr, args, TP9, Fp1, Fp2, TP10):
        if self.check_connection():
            self.brainwave_delta = self.round_values([TP9, Fp1, Fp2, TP10])

    def alpha_abs_handler(self, addr, args, TP9, Fp1, Fp2, TP10):
        if self.check_connection():
            self.brainwave_alpha = self.round_values([TP9, Fp1, Fp2, TP10])

    def beta_abs_handler(self, addr, args, TP9, Fp1, Fp2, TP10):
        if self.check_connection():
            self.brainwave_beta = self.round_values([TP9, Fp1, Fp2, TP10])

    def gamma_abs_handler(self, addr, args, TP9, Fp1, Fp2, TP10):
        if self.check_connection():
            self.brainwave_gamma = self.round_values([TP9, Fp1, Fp2, TP10])
        # start the progam
        logging.debug("calling run function from 'gamma_abs_handler'")
        self.run()

    def get_brainwaves(self, rounded=3):
        # values are updated at 10hz
        # create a dictionary
        brainwaves_dict = {
            "alpha": self.brainwave_alpha,
            "theta": self.brainwave_theta,
            "delta": self.brainwave_delta,
            "beta": self.brainwave_beta,
            "gamma": self.brainwave_gamma}

        # check if any lists in the dict are empty
        if [] in brainwaves_dict.values():
            return {}
        else:
            return brainwaves_dict

    def get_raw_brainwaves(self, rounded=3):
        # values are updated at 256hz
        return [round(e, rounded) for e in self.brainwave_raw]

    def create_server(self, ip_address, port):
        # set up the server arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("--ip",
                            default=ip_address,
                            help="The ip to listen on")
        parser.add_argument("--port",
                            type=int,
                            default=port,
                            help="The port to listen on")
        args = parser.parse_args(args=[])

        # map information to listen for
        dp = dispatcher.Dispatcher()
        dp.map("/muse/elements/horseshoe",
               self.connection_handler,
               "connection")

        dp.map("/muse/eeg",
               self.brainwave_raw_handler,
               "eeg")

        dp.map("/muse/elements/theta_absolute",
               self.theta_abs_handler,
               "theta_absolute")

        dp.map("/muse/elements/delta_absolute",
               self.delta_abs_handler,
               "delta_absolute")

        dp.map("/muse/elements/alpha_absolute",
               self.alpha_abs_handler,
               "alpha_absolute")

        dp.map("/muse/elements/beta_absolute",
               self.beta_abs_handler,
               "beta_absolute")

        dp.map("/muse/elements/gamma_absolute",
               self.gamma_abs_handler,
               "gamma_absolute")

        # create the server
        return osc_server.ThreadingOSCUDPServer((args.ip, args.port), dp)


if __name__ == "__main__":
    ip = input("Enter Computer IP Address: ")
    print("default port set to 5000")
    headband = Headband(ip=ip)
    headband.start_server()
