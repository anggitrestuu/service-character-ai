# examples/basic_chain.py

# how to start:
# python -m examples.basic_chain

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from dotenv import load_dotenv
from chainable_llm.core.types import LLMConfig, PromptConfig, InputType
from chainable_llm.nodes.base import LLMNode
from chainable_llm.transformers.implementations import TextNormalizer


async def main():
    # Load environment variables
    load_dotenv()

    # Validate API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not openai_key or not anthropic_key:
        raise ValueError("Missing API keys in environment variables")

    try:
        # Create a summarization node
        summarizer = LLMNode(
            llm_config=LLMConfig(
                provider="anthropic",
                api_key=anthropic_key,
                model="claude-3-5-sonnet-20240620",
                temperature=0.3,
                max_tokens=1000,  # Specify reasonable max_tokens
            ),
            prompt_config=PromptConfig(
                input_type=InputType.USER_PROMPT,
                base_system_prompt="You are helpful assistant.",
                template="{input}",
            ),
            transformer=TextNormalizer(),
        )

        # # Create an analysis node
        analyzer = LLMNode(
            llm_config=LLMConfig(
                provider="openai",
                api_key=openai_key,
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=1000,
            ),
            prompt_config=PromptConfig(
                input_type=InputType.USER_PROMPT,
                base_system_prompt="You are an insightful analyst.",
                template="{input}",
            ),
            transformer=TextNormalizer(),
            stream_callback=stream_callback,
        )

        # Test input
        test_input = """
        Selamat pagi, apa kabar?
        """

        # stream
        stream_callback = lambda chunk: print(chunk.content)

        await analyzer.process(test_input, stream_callback=stream_callback)

        # Process the chain
        # result = await analyzer.process(test_input)

        # # Print results
        # print("\nInput Text:")
        # print(test_input)
        # print("\nFinal Result:")
        # print(result.content)

        # if result.error:
        #     print("\nError occurred:", result.error)

        # # Print conversation histories
        # print("\nAnalyzer Conversation:")
        # for msg in analyzer.conversation.messages:
        #     print(f"{msg.role.value}: {msg.content}")

        # print("\nSummarizer Conversation:")
        # for msg in summarizer.conversation.messages:
        #     print(f"{msg.role.value}: {msg.content}")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
