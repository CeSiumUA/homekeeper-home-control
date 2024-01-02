import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import validators
import logging
from helpers.dbaccess import MongoDbAccess
import helpers.topics
import random
from helpers.env import Env
from helpers.interfaces import MqttPublisherInterface, DeviceManagerInterface, TelegramMessageSenderInterface

class TlBot(TelegramMessageSenderInterface):

    YOUTUBE_DOWNLOAD = 0
    POWER_STATE_SELECTOR = 1
    POWER_STATE_AFTER_SELECT = 2
    STATS_AFTER_DEVICE_SELECT = 3

    def __init__(self, publisher: MqttPublisherInterface, device_manager: DeviceManagerInterface, logger: logging.Logger):
        self.__token = Env.get_tl_token()
        self.__chat_id = Env.get_tl_chat_id()
        self.__publisher = publisher
        self.__device_manager = device_manager
        self.__logger = logger

    async def __video_download_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__logger.info("got YouTube download request")
        await update.message.reply_text("Enter a video url")
        return self.YOUTUBE_DOWNLOAD
    
    async def __video_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        url = update.message.text
        self.__logger.info("got YouTube url %s\n", url)
        if not validators.url(url):
            self.__logger.error("url %s is invalid\n", url)
            await update.message.reply_text("Invalid url, try again")
            return self.YOUTUBE_DOWNLOAD
        self.__publisher.publish(topic=helpers.topics.VIDEO_DOWNLOAD, payload=url, qos=2)
        await update.message.reply_text("Video download queued")
        return ConversationHandler.END

    async def __get_ip_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__logger.info("got ip address determination request")
        self.__publisher.publish(topic=helpers.topics.GET_IP_ADDRESS, payload=None, qos=2)
        await update.message.reply_text("Getting IP address...")
        return ConversationHandler.END
    
    async def __power_the_device(self, update: Update, context: CallbackContext):
        self.__logger.info("got power request")
        args = context.args
        if len(args) == 2:
            device_name = args[0]
            state = True if args[1].lower() == 'on' else False
            self.__device_manager.device_direct_command_handler(device_name, state)
            await update.message.reply_text(f"Device {device_name} set to {state}")
            return ConversationHandler.END
        
        keyboard = [[]]
        with MongoDbAccess() as mongo_client:
            for device in mongo_client.get_devices_names():
                device_name = device[mongo_client.DEVICE_NAME_FIELD]
                keyboard[0].append(InlineKeyboardButton(device_name, callback_data=device_name))

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text="Choose device", reply_markup=reply_markup
        )
        return self.POWER_STATE_SELECTOR

    async def __power_select_device_state(self, update: Update, context: CallbackContext):
        self.__logger.info('got device state request')
        query = update.callback_query
        await query.answer()
        
        device_name = query.data

        json_data_on = json.dumps({"device_name": device_name, "state": True})
        json_data_off = json.dumps({"device_name": device_name, "state": False})
        json_data_no_forced = json.dumps({"device_name": device_name, "forced": False})

        with MongoDbAccess() as mongo_client:
            stored_device = mongo_client.get_device_by_name(device_name)
            if MongoDbAccess.DEVICE_IS_POWER_FORCED_FIELD in stored_device:
                is_device_state_forced = stored_device[MongoDbAccess.DEVICE_IS_POWER_FORCED_FIELD]
            else:
                is_device_state_forced = False

        keyboard = [
            [
                InlineKeyboardButton("On", callback_data=json_data_on),
                InlineKeyboardButton("Off", callback_data=json_data_off),
            ]
        ]

        if is_device_state_forced:
            keyboard[0].append(InlineKeyboardButton("Disable forced state", callback_data=json_data_no_forced))

        reply_markup = InlineKeyboardMarkup(keyboard)

        current_state = 'On' if stored_device[MongoDbAccess.DEVICE_POWER_ON_FIELD] else 'Off'

        await query.edit_message_text(
            text=f"Choose a state for {device_name}. Current state: {current_state}", reply_markup=reply_markup
        )
        return self.POWER_STATE_AFTER_SELECT
    
    async def __power_after_state_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__logger.info('got device after state select request')
        
        query = update.callback_query
        await query.answer()

        json_data = update.callback_query.data
        data = json.loads(json_data)
        device_name = data['device_name']
        if 'forced' in data:
            with MongoDbAccess() as mongo_client:
                mongo_client.update_device_forced_state(device_name=device_name, is_forced=data['forced'])
            await query.edit_message_text(f"Device {device_name} removed from forced state")
        else:
            state = data['state']
            self.__device_manager.device_direct_command_handler(device_name=device_name, state=state)
            await query.edit_message_text(f"Device {device_name} set to {state}")

        return ConversationHandler.END

    async def __stats_device_selector(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__logger.info('got device stats select request')

        keyboard = [[]]
        with MongoDbAccess() as mongo_client:
            for device in mongo_client.get_devices_names():
                device_name = device[mongo_client.DEVICE_NAME_FIELD]
                keyboard[0].append(InlineKeyboardButton(device_name, callback_data=device_name))

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text="Choose device", reply_markup=reply_markup
        )

        return self.STATS_AFTER_DEVICE_SELECT

    async def __stats_after_device_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.__logger.info('got stats after device select request')
        
        query = update.callback_query
        await query.answer()

        device_name = query.data

        with MongoDbAccess() as mongo_client:
            stored_device = mongo_client.get_device_by_name(device_name)

        reply_text = 'Device stats:\n'
        if MongoDbAccess.DEVICE_NAME_FIELD in stored_device:
            reply_text += f'Device name: {stored_device[MongoDbAccess.DEVICE_NAME_FIELD]}\n'
        if MongoDbAccess.DEVICE_IS_DARK_FIELD in stored_device:
            is_dark = 'Yes' if stored_device[MongoDbAccess.DEVICE_IS_DARK_FIELD] else 'No'
            reply_text += f'Is device in dark: {is_dark}\n'
        if MongoDbAccess.DEVICE_IS_DEVICE_SLEEP in stored_device:
            is_sleep = 'Yes' if stored_device[MongoDbAccess.DEVICE_IS_DEVICE_SLEEP] else 'No'
            reply_text += f'Is device sleep: {is_sleep}\n'
        if MongoDbAccess.DEVICE_TYPE_FIELD in stored_device:
            reply_text += f'Device type: {MongoDbAccess.DEVICE_TYPE_FIELD}\n'
        if MongoDbAccess.DEVICE_TEMPERATURE_FIELD in stored_device:
            reply_text += f'Device temperature: {MongoDbAccess.DEVICE_TEMPERATURE_FIELD}\n'
        if MongoDbAccess.DEVICE_IS_POWER_FORCED_FIELD in stored_device:
            if stored_device[MongoDbAccess.DEVICE_IS_POWER_FORCED_FIELD]:
                reply_text += 'Device is in power forced state\n'
            else:
                reply_text += 'Device is not power-forced\n'
        if MongoDbAccess.DEVICE_TOTAL_ENERGY_FIELD in stored_device:
            reply_text += f'Device total energy: {stored_device[MongoDbAccess.DEVICE_TOTAL_ENERGY_FIELD]}\n'

        await query.edit_message_text(reply_text)
        return ConversationHandler.END

    async def __cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return ConversationHandler.END
    
    async def __send_scheduled_message(self, context: ContextTypes.DEFAULT_TYPE):
        job = context.job
        await context.bot.send_message(job.chat_id, text=job.data)

    def send_telegram_message(self, message: str):
        job_queue = self.__app.job_queue
        job_queue.run_once(self.__send_scheduled_message, when=1, data=message, chat_id=self.__chat_id, name=f'send-message-{random.randint(0, 1000)}')

    def start_bot(self):
        self.__app = Application.builder().token(token=self.__token).build()

        conversation_handler = ConversationHandler(
            entry_points=[
                CommandHandler("ytdownload", self.__video_download_start, filters=filters.Chat(self.__chat_id)),
                CommandHandler("ipaddress", self.__get_ip_address, filters=filters.Chat(self.__chat_id)),
                CommandHandler("power", self.__power_the_device, filters=filters.Chat(self.__chat_id)),
                CommandHandler("stats", self.__stats_device_selector, filters=filters.Chat(self.__chat_id))
            ],
            states={
                self.YOUTUBE_DOWNLOAD: [MessageHandler(filters=filters.TEXT, callback=self.__video_download)],
                self.POWER_STATE_SELECTOR: [CallbackQueryHandler(self.__power_select_device_state)],
                self.POWER_STATE_AFTER_SELECT: [CallbackQueryHandler(self.__power_after_state_select)],
                self.STATS_AFTER_DEVICE_SELECT: [CallbackQueryHandler(self.__stats_after_device_select)]
            },
            fallbacks=[CommandHandler("cancel", self.__cancel)]
        )
        self.__app.add_handler(conversation_handler)
        self.__app.run_polling()