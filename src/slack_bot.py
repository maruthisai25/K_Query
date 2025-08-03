from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
import logging
from typing import Dict
import aiohttp
import os
from .config import Config

logger = logging.getLogger(__name__)

class SlackBot:
    def __init__(self):
        self.config = Config()
        self.app = AsyncApp(
            token=self.config.SLACK_BOT_TOKEN,
            signing_secret=self.config.SLACK_SIGNING_SECRET
        )
        self.handler = AsyncSlackRequestHandler(self.app)
        # Use environment variable or service discovery
        self.chat_api_url = os.getenv("CHAT_API_URL", "http://localhost:8000/chat")
        
        # Register slash command handler
        self.app.command("/devops")(self.handle_devops_command)
        
        # Register message handler for DMs
        self.app.message()(self.handle_direct_message)
    
    async def handle_devops_command(self, ack, respond, command):
        """Handle /devops slash command"""
        await ack()
        
        try:
            user_query = command.get("text", "").strip()
            if not user_query:
                await respond("Please provide a question after the command. Example: `/devops why are my pods crashing?`")
                return
            
            # Show typing indicator
            await respond("🤔 Let me check that for you...")
            
            # Call the chat API
            response = await self._get_chat_response(user_query)
            
            # Format response for Slack
            formatted_response = self._format_slack_response(response)
            await respond(formatted_response)
            
        except Exception as e:
            logger.error(f"Error handling devops command: {str(e)}")
            await respond("Sorry, I encountered an error processing your request. Please try again.")
    
    async def handle_direct_message(self, message, say):
        """Handle direct messages to the bot"""
        try:
            # Only respond to DMs, not channel messages
            if message.get("channel_type") != "im":
                return
            
            user_query = message.get("text", "").strip()
            if not user_query:
                return
            
            # Get response from chat API
            response = await self._get_chat_response(user_query)
            
            # Format and send response
            formatted_response = self._format_slack_response(response)
            await say(formatted_response)
            
        except Exception as e:
            logger.error(f"Error handling direct message: {str(e)}")
            await say("Sorry, I encountered an error processing your message. Please try again.")
    
    async def _get_chat_response(self, query: str) -> Dict:
        """Get response from the chat API"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"message": query}
                async with session.post(self.chat_api_url, json=payload) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Chat API error: {response.status}")
                        return {"response": "Sorry, I'm having trouble processing your request right now."}
        except Exception as e:
            logger.error(f"Error calling chat API: {str(e)}")
            return {"response": "Sorry, I'm having trouble connecting to my brain right now."}
    
    def _format_slack_response(self, response: Dict) -> Dict:
        """Format response for Slack with blocks"""
        response_text = response.get("response", "No response generated.")
        sources = response.get("sources", [])
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚙️ *DevOps Automation*\n\n{response_text}"
                }
            }
        ]
        
        # Add sources if available
        if sources:
            source_text = "\n".join([f"• {source}" for source in sources if source])
            if source_text:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📚 *Sources:*\n{source_text}"
                    }
                })
        
        return {"blocks": blocks}
    
    def get_handler(self):
        """Get the FastAPI handler for Slack events"""
        return self.handler