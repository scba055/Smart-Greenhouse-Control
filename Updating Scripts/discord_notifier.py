import asyncio
import discord
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import config

# Setup logging
logger = logging.getLogger(__name__)

class GreenhouseDiscordNotifier:
    """Discord notifier for greenhouse monitoring system"""
    
    def __init__(self):
        self.bot = None
        self.channel = None
        self.is_ready = False
        self._setup_intents()
    
    def _setup_intents(self):
        """Setup Discord bot intents"""
        intents = discord.Intents.default()
        intents.message_content = True  # Required for message content access
        self.bot = discord.Client(intents=intents)
        
        @self.bot.event
        async def on_ready():
            """Bot ready event handler"""
            logger.info(f'Discord bot logged in as {self.bot.user}')
            self.channel = self.bot.get_channel(int(config.DISCORD_CHANNEL_ID))
            if self.channel:
                self.is_ready = True
                logger.info(f'Connected to Discord channel: {self.channel.name}')
            else:
                logger.error(f'Could not find Discord channel with ID: {config.DISCORD_CHANNEL_ID}')
    
    async def start_bot(self):
        """Start the Discord bot"""
        try:
            await self.bot.start(config.DISCORD_BOT_TOKEN)
        except discord.LoginFailure:
            logger.error("Failed to login to Discord. Check your bot token.")
            raise
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}")
            raise
    
    async def send_success_notification(self, timestamp: str, filename: str, 
                                      file_size: str) -> bool:
        """
        Send success notification to Discord
        
        Args:
            timestamp: Photo timestamp
            filename: Photo filename
            file_size: File size string
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not config.DISCORD_ENABLED or not config.DISCORD_NOTIFY_SUCCESS:
            return True
        
        if not self.is_ready:
            logger.warning("Discord bot not ready, cannot send notification")
            return False
        
        try:
            # Create embed for better formatting
            embed = discord.Embed(
                title="📸 Greenhouse Photo Captured",
                color=config.DISCORD_EMBED_COLOR,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="🕐 Time", value=timestamp, inline=True)
            embed.add_field(name="📁 Filename", value=filename, inline=True)
            embed.add_field(name="💾 File Size", value=file_size, inline=True)
            
            
            # Add thumbnail if you have a default image
            # embed.set_thumbnail(url="your_greenhouse_icon_url")
            
            await self.channel.send(embed=embed)
            logger.info("Success notification sent to Discord")
            return True
            
        except Exception as e:
            logger.error(f"Error sending success notification to Discord: {e}")
            return False
    
    async def send_error_notification(self, timestamp: str, error_message: str) -> bool:
        """
        Send error notification to Discord
        
        Args:
            timestamp: Error timestamp
            error_message: Error description
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not config.DISCORD_ENABLED or not config.DISCORD_NOTIFY_ERROR:
            return True
        
        if not self.is_ready:
            logger.warning("Discord bot not ready, cannot send error notification")
            return False
        
        try:
            # Create embed for error
            embed = discord.Embed(
                title="❌ Greenhouse Photo Error",
                color=config.DISCORD_ERROR_COLOR,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="🕐 Time", value=timestamp, inline=True)
            embed.add_field(name="🔴 Error", value=error_message, inline=False)
            
            await self.channel.send(embed=embed)
            logger.info("Error notification sent to Discord")
            return True
            
        except Exception as e:
            logger.error(f"Error sending error notification to Discord: {e}")
            return False
    
    async def send_system_notification(self, message: str, is_error: bool = False) -> bool:
        """
        Send system notification to Discord
        
        Args:
            message: System message
            is_error: Whether this is an error message
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not config.DISCORD_ENABLED or not self.is_ready:
            return True
        
        try:
            color = config.DISCORD_ERROR_COLOR if is_error else config.DISCORD_EMBED_COLOR
            embed = discord.Embed(
                title="🤖 System Notification",
                description=message,
                color=color,
                timestamp=datetime.now()
            )
            
            await self.channel.send(embed=embed)
            logger.info("System notification sent to Discord")
            return True
            
        except Exception as e:
            logger.error(f"Error sending system notification to Discord: {e}")
            return False
    
    async def close(self):
        """Close the Discord bot connection"""
        if self.bot and not self.bot.is_closed():
            await self.bot.close()
            logger.info("Discord bot connection closed")

# Synchronous wrapper functions for use in main application
def send_photo_success_notification(timestamp: str, filename: str, 
                                  file_size: str) -> bool:
    """
    Synchronous wrapper for sending success notification
    """
    try:
        # Create new event loop for this operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        notifier = GreenhouseDiscordNotifier()
        
        async def _send():
            try:
                # Start bot and wait for ready
                bot_task = asyncio.create_task(notifier.start_bot())
                
                # Wait for bot to be ready (max 10 seconds)
                for _ in range(50):  # 50 * 0.2 = 10 seconds
                    if notifier.is_ready:
                        break
                    await asyncio.sleep(0.2)
                
                if not notifier.is_ready:
                    logger.error("Discord bot failed to become ready within timeout")
                    return False
                
                # Send notification
                success = await notifier.send_success_notification(
                    timestamp, filename, file_size
                )
                
                # Wait a moment for message to send
                await asyncio.sleep(1)
                
                return success
                
            finally:
                await notifier.close()
        
        result = loop.run_until_complete(_send())
        loop.close()
        return result
        
    except Exception as e:
        logger.error(f"Error in send_photo_success_notification: {e}")
        return False

def send_photo_error_notification(timestamp: str, error_message: str) -> bool:
    """
    Synchronous wrapper for sending error notification
    """
    try:
        # Create new event loop for this operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        notifier = GreenhouseDiscordNotifier()
        
        async def _send():
            try:
                # Start bot and wait for ready
                bot_task = asyncio.create_task(notifier.start_bot())
                
                # Wait for bot to be ready (max 10 seconds)
                for _ in range(50):  # 50 * 0.2 = 10 seconds
                    if notifier.is_ready:
                        break
                    await asyncio.sleep(0.2)
                
                if not notifier.is_ready:
                    logger.error("Discord bot failed to become ready within timeout")
                    return False
                
                # Send notification
                success = await notifier.send_error_notification(timestamp, error_message)
                
                # Wait a moment for message to send
                await asyncio.sleep(1)
                
                return success
                
            finally:
                await notifier.close()
        
        result = loop.run_until_complete(_send())
        loop.close()
        return result
        
    except Exception as e:
        logger.error(f"Error in send_photo_error_notification: {e}")
        return False

def send_system_notification(message: str, is_error: bool = False) -> bool:
    """
    Synchronous wrapper for sending system notification
    """
    try:
        # Create new event loop for this operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        notifier = GreenhouseDiscordNotifier()
        
        async def _send():
            try:
                # Start bot and wait for ready
                bot_task = asyncio.create_task(notifier.start_bot())
                
                # Wait for bot to be ready (max 10 seconds)
                for _ in range(50):  # 50 * 0.2 = 10 seconds
                    if notifier.is_ready:
                        break
                    await asyncio.sleep(0.2)
                
                if not notifier.is_ready:
                    logger.error("Discord bot failed to become ready within timeout")
                    return False
                
                # Send notification
                success = await notifier.send_system_notification(message, is_error)
                
                # Wait a moment for message to send
                await asyncio.sleep(1)
                
                return success
                
            finally:
                await notifier.close()
        
        result = loop.run_until_complete(_send())
        loop.close()
        return result
        
    except Exception as e:
        logger.error(f"Error in send_system_notification: {e}")
        return False
    

