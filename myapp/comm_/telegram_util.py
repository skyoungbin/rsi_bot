# 메세지를 보내는 함수 정의 
async def send_msg(self, msg):
    await self.bot.sendMessage(chat_id=self.chat_id, text=msg) 