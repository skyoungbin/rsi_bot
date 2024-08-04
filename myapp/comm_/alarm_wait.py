import logging
import threading


class AlarmWait():

    def __init__(self):
        # 믹스인이 상태를 관리해야 하는 특별한 경우에는 __init__ 메소드를 정의할 수 있습니다.
        self.timer = None
        self.wait_msg = None

    def set_wait(self, value):
        logging.debug('start set_wait')

        self.wait_msg = value

        if self.timer is None:
            #self.timer.cancel()  # 이미 실행 중인 타이머가 있다면 취소합니다.
            self.timer = threading.Timer(1, self.reset_wait)  # 10분 후에 reset_wait 호출
            self.timer.start()

    def reset_wait(self):
        logging.debug('start reset_wait')

        self.wait_msg = None
        self.timer = None

    
    def __getstate__(self):
        state = self.__dict__.copy()

        del state['timer']
        del state['wait_msg']

        return state

    def __setstate__(self, state):

        self.__dict__.update(state)

        self.timer = None
        self.wait_msg = None
