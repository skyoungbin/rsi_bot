import logging 

class EventManager:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_type, listener):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)

    def unsubscribe(self, event_type, listener):
        if event_type in self.listeners:
            self.listeners[event_type].remove(listener)

    def publish(self, event_type, data):
        logging.debug(f'Publishing event: {event_type}')
        if event_type in self.listeners:
            logging.debug(f'Listeners found for event: {event_type}')
            for listener in self.listeners[event_type]:
                logging.debug(f'Calling listener: {listener}')
                listener(data)
        else:
            logging.warning(f'No listeners found for event: {event_type}')