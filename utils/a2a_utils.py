"""A2A protocol utilities for agent communication."""

import httpx
import asyncio
import uuid
from typing import Optional

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    Part,
    TextPart,
    MessageSendParams,
    Message,
    Role,
    SendMessageRequest,
    SendMessageResponse,
)


async def get_agent_card(url: str) -> Optional[AgentCard]:
    """
    Retrieve the agent card from an A2A agent at the given URL.

    Args:
        url: The base URL of the A2A agent

    Returns:
        The agent card if available, None otherwise
    """
    httpx_client = httpx.AsyncClient()
    resolver = A2ACardResolver(httpx_client=httpx_client, base_url=url)
    card: Optional[AgentCard] = await resolver.get_agent_card()
    return card


async def wait_agent_ready(url: str, timeout: int = 30) -> bool:
    """
    Wait until an A2A agent is ready by checking its agent card.

    Args:
        url: The base URL of the A2A agent
        timeout: Maximum number of seconds to wait

    Returns:
        True if agent becomes ready, False if timeout
    """
    retry_cnt = 0
    while retry_cnt < timeout:
        retry_cnt += 1
        try:
            card = await get_agent_card(url)
            if card is not None:
                return True
            else:
                print(f"Agent card not available yet, retrying {retry_cnt}/{timeout}...")
        except Exception as e:
            print(f"Error checking agent readiness: {e}")
        await asyncio.sleep(1)
    return False


async def send_message(
    url: str,
    message: str,
    task_id: Optional[str] = None,
    context_id: Optional[str] = None,
    timeout: float = 300.0
) -> SendMessageResponse:
    """
    Send a message to an A2A agent.

    Args:
        url: The base URL of the A2A agent
        message: The text message to send
        task_id: Optional task ID for tracking
        context_id: Optional context ID for multi-turn conversations
        timeout: Request timeout in seconds (default 300s for long-running tasks)

    Returns:
        The response from the agent
    """
    card = await get_agent_card(url)
    httpx_client = httpx.AsyncClient(timeout=timeout)
    client = A2AClient(httpx_client=httpx_client, agent_card=card)

    message_id = uuid.uuid4().hex
    params = MessageSendParams(
        message=Message(
            role=Role.user,
            parts=[Part(TextPart(text=message))],
            message_id=message_id,
            task_id=task_id,
            context_id=context_id,
        )
    )
    request_id = uuid.uuid4().hex
    req = SendMessageRequest(id=request_id, params=params)
    response = await client.send_message(request=req)
    return response


def parse_tags(text: str) -> dict[str, str]:
    """
    Parse XML-style tags from text.

    Args:
        text: Text containing XML-style tags like <tag>content</tag>

    Returns:
        Dictionary mapping tag names to their content
    """
    import re
    result = {}
    pattern = r'<(\w+)>(.*?)</\1>'
    matches = re.findall(pattern, text, re.DOTALL)
    for tag_name, content in matches:
        result[tag_name] = content.strip()
    return result
