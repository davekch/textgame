A textadventure game as a telegram chatbot
============================================

This is an example of a chatbot on telegram that acts as an adventure game.

Suppose you have all your custom stuff defined in ``mystuff.py``.

.. code-block:: python

   from mystuff import rooms, items, monsters, MyPlayer, MyWorld, MyParser

   from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

   class Game:

        def __init__(self):

            world = MyWorld(rooms=rooms, items=items, monsters=monsters)
            player = MyPlayer(world, world.room("start"))

            self.parser = MyParser(player)

        def play(self, command):
            return self.parser.understand(command.lower())


   class GameBot:

       def __init__(self):
           # save games with all players
           self.games = {}

       def start(self, bot, update):
           # start a new game
           self.games[update.message.chat_id] = Game()

       def respond(self, bot, update):
           # get the game with this player
           game = self.games[chat_id]
           # give the player's message as input to the game
           response = game.play(update.message.text)
           bot.send_message( chat_id=chat_id, text=response )

       def main(self):
           # main routine for the bot

           token = "mytoken"
           updater = Updater(token)
           dp = updater.dispatcher

           # define the behaviour of the bot
           dp.add_handler(CommandHandler("start", self.start))
           dp.add_handler(MessageHandler(Filters.text, self.respond))

           updater.start_polling()
           updater.idle()

   # create the chat bot and run it!
   if __name__ == "__main__":

        gamebot = GameBot()
        gamebot.main()
