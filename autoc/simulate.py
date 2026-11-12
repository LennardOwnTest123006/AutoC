"""Simulate typing through the engine (used by `autoc correct` and the tests)."""


def type_text(engine, text: str) -> str:
    screen = []
    for ch in text:
        if ch == "\b":
            act = engine.key_backspace()
            if act:
                del screen[len(screen) - act.backspaces:]
                screen.extend(act.text)
            elif screen:
                screen.pop()
            continue
        act = engine.key_special("enter") if ch == "\n" else engine.key_char(ch)
        if act:
            del screen[len(screen) - act.backspaces:]
            screen.extend(act.text)
            if act.then == "enter":
                screen.append("\n")
            elif act.then == "tab":
                screen.append("\t")
        else:
            screen.append(ch)
    return "".join(screen)
