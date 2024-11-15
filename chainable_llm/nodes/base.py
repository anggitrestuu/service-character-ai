# nodes/base.py
from typing import Optional, Callable, Any

from chainable_llm.transformers.base import DataTransformer
from ..core.types import (
    LLMConfig, 
    PromptConfig, 
    LLMResponse, 
    ConversationHistory,
    MessageRole,
    InputType
)
from ..llm.factory import LLMFactory
from ..core.logging import logger

class LLMNode:
    def __init__(
        self,
        llm_config: LLMConfig,
        prompt_config: PromptConfig,
        transformer: Optional[DataTransformer] = None,
        next_node: Optional['LLMNode'] = None,
        condition: Optional[Callable[[str], bool]] = None
    ):
        self.llm = LLMFactory.create(llm_config)
        self.prompt_config = prompt_config
        self.transformer = transformer
        self.next_node = next_node
        self.condition = condition
        self.conversation = ConversationHistory()

    async def _build_prompt(self, input_text: str) -> tuple[Optional[str], str]:
        """
        Build the final prompt based on the prompt configuration and input type.
        Returns a tuple of (system_prompt, user_prompt)
        """
        formatted_input = self.prompt_config.template.format(input=input_text)
        
        if self.prompt_config.input_type == InputType.SYSTEM_PROMPT:
            return formatted_input, ""
        elif self.prompt_config.input_type == InputType.APPEND_SYSTEM:
            base_system = self.prompt_config.base_system_prompt or ""
            return f"{base_system}\n{formatted_input}", ""
        else:  # InputType.USER_PROMPT
            return self.prompt_config.base_system_prompt, formatted_input

    async def process(self, input_data: Any) -> LLMResponse:
        try:
            # Transform input if transformer exists
            if self.transformer:
                input_text = await self.transformer.transform(input_data)
            else:
                input_text = str(input_data)

            # Build prompts using template
            system_prompt, user_prompt = await self._build_prompt(input_text)

            # If we have a user prompt, add it to conversation
            if user_prompt:
                self.conversation.add_message(
                    role=MessageRole.USER,
                    content=user_prompt
                )
            
            # Generate LLM response
            response = await self.llm.generate(
                system_prompt=system_prompt,
                conversation=self.conversation,
                temperature=self.llm.config.temperature,
                max_tokens=self.llm.config.max_tokens
            )

            # Add assistant response to conversation
            self.conversation.add_message(
                role=MessageRole.ASSISTANT,
                content=response.content
            )

            # Process next node if conditions are met
            if self.next_node and (not self.condition or self.condition(response.content)):
                return await self.next_node.process(response.content)

            return response

        except Exception as e:
            logger.error(
                "node_processing_error", 
                error=str(e), 
                node_id=id(self),
                input_length=len(str(input_data))
            )
            return LLMResponse(
                content="",
                metadata={
                    "error_type": type(e).__name__,
                    "node_id": id(self)
                },
                error=str(e)
            )

    async def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation = ConversationHistory()