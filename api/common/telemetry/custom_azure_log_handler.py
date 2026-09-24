import logging
import threading

from opencensus.ext.azure.log_exporter import AzureLogHandler


class CustomAzureLogHandler(AzureLogHandler):
    def createLock(self):
        """
        Acquire a thread lock for serializing access to the underlying I/O.
        """
        self.lock = threading.RLock()
        logging._register_at_fork_reinit_lock(self)
