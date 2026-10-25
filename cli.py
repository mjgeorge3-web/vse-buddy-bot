"""Interactive command-line test runner for VŠE Buddy Bot.

Allows interactive question-answering in the terminal with live score inspection.
"""

from bot import BuddyBot


def main():
    print("==================================================")
    print("🎓 VŠE Buddy Bot - Interactive Terminal Mode")
    print("Type your question and press Enter. Type 'exit' or 'quit' to stop.")
    print("==================================================\n")

    bot = BuddyBot()
    history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\nGoodbye! Hodně štěstí při studiu na VŠE!")
                break

            print("\n🤖 Buddy Bot is thinking...")
            result = bot.answer(user_input, history=history)

            print(f"\n[Mode: {result['mode']} | Score: {result['top_score']} | Latency: {result['latency_ms']} ms]")
            print("-" * 60)
            print(result["answer"])
            print("-" * 60)

            # Update conversational history
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": result["answer"]})

        except KeyboardInterrupt:
            print("\nSession ended.")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
