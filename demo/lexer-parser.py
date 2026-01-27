class JSONLexer:
    """
    A Finite State Automaton.

    Defining characteristic:
    - Only ONE piece of mutable state: `self.state`
    - No stack, no recursion tracking, no unbounded memory
    - Transitions are purely: (current_state, input_char) → next_state
    """

    # All possible states (finite!)
    STATE_START = "START"
    STATE_IN_STRING = "IN_STRING"
    STATE_IN_STRING_ESCAPE = "IN_STRING_ESCAPE"
    STATE_IN_NUMBER = "IN_NUMBER"
    STATE_IN_KEYWORD = "IN_KEYWORD"  # for true, false, null

    def __init__(self):
        self.state = self.STATE_START
        self.buffer = ""  # accumulates current token's characters

    def feed(self, char: str) -> list[str]:
        """
        Feed one character, return list of terminals emitted (usually 0 or 1).

        This is the FSA transition function:
            (state, char) → (new_state, emitted_terminals)
        """
        emitted = []

        if self.state == self.STATE_START:
            if char == "{":
                emitted.append(("LBRACE", "{"))
                # state stays START
            elif char == "}":
                emitted.append(("RBRACE", "}"))
            elif char == "[":
                emitted.append(("LBRACKET", "["))
            elif char == "]":
                emitted.append(("RBRACKET", "]"))
            elif char == ":":
                emitted.append(("COLON", ":"))
            elif char == ",":
                emitted.append(("COMMA", ","))
            elif char == '"':
                self.state = self.STATE_IN_STRING
                self.buffer = ""
            elif char.isdigit() or char == "-":
                self.state = self.STATE_IN_NUMBER
                self.buffer = char
            elif char in "tfn":  # start of true, false, null
                self.state = self.STATE_IN_KEYWORD
                self.buffer = char
            elif char.isspace():
                pass  # ignore whitespace

        elif self.state == self.STATE_IN_STRING:
            if char == "\\":
                self.state = self.STATE_IN_STRING_ESCAPE
                self.buffer += char
            elif char == '"':
                emitted.append(("STRING", self.buffer))
                self.buffer = ""
                self.state = self.STATE_START
            else:
                self.buffer += char

        elif self.state == self.STATE_IN_STRING_ESCAPE:
            self.buffer += char
            self.state = self.STATE_IN_STRING

        elif self.state == self.STATE_IN_NUMBER:
            if char.isdigit() or char in ".eE+-":
                self.buffer += char
            else:
                emitted.append(("NUMBER", self.buffer))
                self.buffer = ""
                self.state = self.STATE_START
                # Re-process this char in START state
                emitted.extend(self.feed(char))

        elif self.state == self.STATE_IN_KEYWORD:
            if char.isalpha():
                self.buffer += char
            else:
                # Emit the keyword
                if self.buffer == "true":
                    emitted.append(("TRUE", True))
                elif self.buffer == "false":
                    emitted.append(("FALSE", False))
                elif self.buffer == "null":
                    emitted.append(("NULL", None))
                self.buffer = ""
                self.state = self.STATE_START
                emitted.extend(self.feed(char))

        return emitted

    def flush(self) -> list[str]:
        """
        Flush any pending token at end of input.
        Called when there are no more characters to feed.
        """
        emitted = []
        if self.state == self.STATE_IN_NUMBER:
            emitted.append(("NUMBER", self.buffer))
            self.buffer = ""
            self.state = self.STATE_START
        elif self.state == self.STATE_IN_KEYWORD:
            if self.buffer == "true":
                emitted.append(("TRUE", True))
            elif self.buffer == "false":
                emitted.append(("FALSE", False))
            elif self.buffer == "null":
                emitted.append(("NULL", None))
            self.buffer = ""
            self.state = self.STATE_START
        return emitted


class JSONParser:
    """
    A Pushdown Automaton.

    Defining characteristic:
    - Has a STACK (`self.stack`) in addition to state
    - Transitions are: (current_state, input_terminal, stack_top) → (new_state, stack_operation)
    - Stack operations: push, pop, or neither
    - The stack gives it "memory" of nesting depth
    """

    STATE_EXPECT_VALUE = "EXPECT_VALUE"
    STATE_EXPECT_VALUE_OR_END = (
        "EXPECT_VALUE_OR_END"  # For arrays - can be empty or have values
    )
    STATE_EXPECT_KEY_OR_END = "EXPECT_KEY_OR_END"
    STATE_EXPECT_KEY = "EXPECT_KEY"  # After comma - only key allowed, no trailing comma
    STATE_EXPECT_COLON = "EXPECT_COLON"
    STATE_EXPECT_COMMA_OR_END = "EXPECT_COMMA_OR_END"
    STATE_DONE = "DONE"

    # Stack symbols
    STACK_OBJECT = "OBJECT"  # we're inside an object
    STACK_ARRAY = "ARRAY"  # we're inside an array
    STACK_BOTTOM = "BOTTOM"  # bottom of stack marker

    def __init__(self):
        self.state = self.STATE_EXPECT_VALUE
        self.stack = [self.STACK_BOTTOM]  # ← THIS IS WHAT MAKES IT A PDA

    def feed(self, terminal: tuple) -> bool:
        """
        Feed one terminal (from lexer), return True if valid, False if error.

        This is the PDA transition function:
            (state, terminal, stack_top) → (new_state, stack_operation)
        """
        token_type, token_value = terminal
        stack_top = self.stack[-1]

        if self.state == self.STATE_EXPECT_VALUE:
            if token_type == "LBRACE":
                self.stack.append(self.STACK_OBJECT)  # ← PUSH
                self.state = self.STATE_EXPECT_KEY_OR_END
                return True
            elif token_type == "LBRACKET":
                self.stack.append(self.STACK_ARRAY)  # ← PUSH
                self.state = (
                    self.STATE_EXPECT_VALUE_OR_END
                )  # array can be empty or have values
                return True
            elif token_type in ("STRING", "NUMBER", "TRUE", "FALSE", "NULL"):
                # Simple value - what's next depends on what we're inside
                self._after_value()
                return True
            else:
                return False  # unexpected terminal

        elif self.state == self.STATE_EXPECT_VALUE_OR_END:
            # We're inside an array, expecting a value or ]
            if token_type == "RBRACKET":
                self.stack.pop()  # ← POP (empty array)
                self._after_value()
                return True
            elif token_type == "LBRACE":
                self.stack.append(self.STACK_OBJECT)  # ← PUSH
                self.state = self.STATE_EXPECT_KEY_OR_END
                return True
            elif token_type == "LBRACKET":
                self.stack.append(self.STACK_ARRAY)  # ← PUSH
                self.state = self.STATE_EXPECT_VALUE_OR_END
                return True
            elif token_type in ("STRING", "NUMBER", "TRUE", "FALSE", "NULL"):
                self._after_value()
                return True
            else:
                return False

        elif self.state == self.STATE_EXPECT_KEY_OR_END:
            # We're inside an object, expecting a key string or }
            if token_type == "STRING":
                self.state = self.STATE_EXPECT_COLON
                return True
            elif token_type == "RBRACE":
                self.stack.pop()  # ← POP
                self._after_value()
                return True
            else:
                return False

        elif self.state == self.STATE_EXPECT_KEY:
            # After a comma in an object - MUST have a key, no trailing comma allowed
            if token_type == "STRING":
                self.state = self.STATE_EXPECT_COLON
                return True
            else:
                return False  # Trailing comma not allowed!

        elif self.state == self.STATE_EXPECT_COLON:
            if token_type == "COLON":
                self.state = self.STATE_EXPECT_VALUE
                return True
            else:
                return False

        elif self.state == self.STATE_EXPECT_COMMA_OR_END:
            if token_type == "COMMA":
                # What comes after comma depends on stack
                if stack_top == self.STACK_OBJECT:
                    self.state = (
                        self.STATE_EXPECT_KEY
                    )  # Must have key after comma, no trailing comma
                elif stack_top == self.STACK_ARRAY:
                    self.state = self.STATE_EXPECT_VALUE
                return True
            elif token_type == "RBRACE" and stack_top == self.STACK_OBJECT:
                self.stack.pop()  # ← POP
                self._after_value()
                return True
            elif token_type == "RBRACKET" and stack_top == self.STACK_ARRAY:
                self.stack.pop()  # ← POP
                self._after_value()
                return True
            else:
                return False

        return False

    def _after_value(self):
        """Determine state after consuming a complete value."""
        stack_top = self.stack[-1]
        if stack_top == self.STACK_BOTTOM:
            self.state = self.STATE_DONE
        else:
            self.state = self.STATE_EXPECT_COMMA_OR_END

    def is_complete(self) -> bool:
        """Check if we've parsed a complete valid JSON."""
        return self.state == self.STATE_DONE and len(self.stack) == 1


def validate_json(text: str) -> bool:
    """
    Run lexer (FSA) → parser (PDA) pipeline.
    """
    lexer = JSONLexer()
    parser = JSONParser()

    for char in text:
        terminals = lexer.feed(char)
        for terminal in terminals:
            if not parser.feed(terminal):
                return False  # parser rejected

    # Flush any remaining tokens (e.g., numbers or keywords at end of input)
    for terminal in lexer.flush():
        if not parser.feed(terminal):
            return False

    return parser.is_complete()


# Test it
def test(json_str, expected, description):
    result = validate_json(json_str)
    status = "✓" if result == expected else "✗"
    print(f"{status} {description}: got {result}, expected {expected}")
    if result != expected:
        print(f"    Input: {json_str!r}")


test('{"name": "Alice", "nested": {"x": 1}}', True, "valid nested object")
test('{"name": "Alice"', False, "unclosed object")
test('{"name": "Alice",}', False, "trailing comma in object")

# Additional test cases
test("[1, 2, 3]", True, "simple array")
test("[1, 2, 3,]", False, "trailing comma in array")
test('{"a": [1, 2], "b": {"c": true}}', True, "nested structures")
test("null", True, "simple value null")
test("{}", True, "empty object")
test("[]", True, "empty array")
test("[,]", False, "invalid comma in array")

# Deeply nested test cases
test("[[[[1]]]]", True, "deeply nested arrays")
test('[{"a": [{"b": [1, 2, {"c": 3}]}]}]', True, "deeply nested mixed")
test('{"a": {"b": {"c": {"d": {"e": 5}}}}}', True, "deeply nested objects")
test("[[[[1]]]", False, "unclosed deeply nested arrays")
test('[{"a": [1, 2}]', False, "mismatched brackets in nested")
test('{"a": [1, 2], "b": [3, [4, [5]]]}', True, "complex nested arrays in object")
