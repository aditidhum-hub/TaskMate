/**
 * Safe Mathematical Expression Evaluator (No eval() or Function constructor)
 * Implements a recursive-descent parser for arithmetic: +, -, *, /, %, ^, (), and basic Math functions.
 * Protects against code injection and arbitrary execution.
 */

type TokenType = 'NUMBER' | 'OPERATOR' | 'LPAREN' | 'RPAREN' | 'IDENTIFIER';

interface Token {
  type: TokenType;
  value: string;
}

export function tokenizeMath(input: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;
  const str = input.trim();

  while (i < str.length) {
    const char = str[i];

    if (/\s/.test(char)) {
      i++;
      continue;
    }

    if (/[0-9.]/.test(char)) {
      let num = '';
      while (i < str.length && /[0-9.]/.test(str[i])) {
        num += str[i];
        i++;
      }
      tokens.push({ type: 'NUMBER', value: num });
      continue;
    }

    if (/[+\-*/%^]/.test(char)) {
      tokens.push({ type: 'OPERATOR', value: char });
      i++;
      continue;
    }

    if (char === '(') {
      tokens.push({ type: 'LPAREN', value: char });
      i++;
      continue;
    }

    if (char === ')') {
      tokens.push({ type: 'RPAREN', value: char });
      i++;
      continue;
    }

    if (/[a-zA-Z_]/.test(char)) {
      let ident = '';
      while (i < str.length && /[a-zA-Z0-9_]/.test(str[i])) {
        ident += str[i];
        i++;
      }
      tokens.push({ type: 'IDENTIFIER', value: ident.toLowerCase() });
      continue;
    }

    throw new Error(`Unexpected character in expression: '${char}'`);
  }

  return tokens;
}

export function evaluateSafeMath(expr: string): { result: number; expression: string } {
  const sanitized = expr.replace(/,/g, '').replace(/\$/g, '').trim();
  const tokens = tokenizeMath(sanitized);
  let pos = 0;

  function peek(): Token | undefined {
    return tokens[pos];
  }

  function consume(expectedType?: TokenType): Token {
    const token = tokens[pos++];
    if (!token) {
      throw new Error('Unexpected end of expression');
    }
    if (expectedType && token.type !== expectedType) {
      throw new Error(`Expected token type ${expectedType} but got ${token.type} ('${token.value}')`);
    }
    return token;
  }

  // Expression -> Term ((+ | -) Term)*
  function parseExpression(): number {
    let value = parseTerm();
    while (peek() && peek()!.type === 'OPERATOR' && (peek()!.value === '+' || peek()!.value === '-')) {
      const op = consume().value;
      const right = parseTerm();
      if (op === '+') value += right;
      else if (op === '-') value -= right;
    }
    return value;
  }

  // Term -> Power ((* | / | %) Power)*
  function parseTerm(): number {
    let value = parsePower();
    while (
      peek() &&
      peek()!.type === 'OPERATOR' &&
      (peek()!.value === '*' || peek()!.value === '/' || peek()!.value === '%')
    ) {
      const op = consume().value;
      const right = parsePower();
      if (op === '*') value *= right;
      else if (op === '/') {
        if (right === 0) throw new Error('Division by zero is undefined');
        value /= right;
      } else if (op === '%') {
        value %= right;
      }
    }
    return value;
  }

  // Power -> Factor (^ Factor)*
  function parsePower(): number {
    let value = parseFactor();
    if (peek() && peek()!.type === 'OPERATOR' && peek()!.value === '^') {
      consume();
      const exponent = parsePower(); // right-associative
      value = Math.pow(value, exponent);
    }
    return value;
  }

  // Factor -> NUMBER | (Expr) | unary -/+ | MathFunction(Expr)
  function parseFactor(): number {
    const current = peek();
    if (!current) throw new Error('Unexpected end of input inside factor');

    if (current.type === 'OPERATOR' && (current.value === '-' || current.value === '+')) {
      const op = consume().value;
      const val = parseFactor();
      return op === '-' ? -val : val;
    }

    if (current.type === 'NUMBER') {
      const token = consume('NUMBER');
      const val = parseFloat(token.value);
      if (isNaN(val)) throw new Error(`Invalid numeric token: '${token.value}'`);
      return val;
    }

    if (current.type === 'IDENTIFIER') {
      const funcName = consume('IDENTIFIER').value;
      consume('LPAREN');
      const arg = parseExpression();
      consume('RPAREN');

      switch (funcName) {
        case 'sqrt':
          if (arg < 0) throw new Error('Square root of negative number is not real');
          return Math.sqrt(arg);
        case 'abs':
          return Math.abs(arg);
        case 'round':
          return Math.round(arg);
        case 'floor':
          return Math.floor(arg);
        case 'ceil':
          return Math.ceil(arg);
        case 'sin':
          return Math.sin(arg);
        case 'cos':
          return Math.cos(arg);
        case 'tan':
          return Math.tan(arg);
        case 'log':
        case 'ln':
          return Math.log(arg);
        case 'pi':
          return Math.PI;
        default:
          throw new Error(`Unknown mathematical function or constant '${funcName}'`);
      }
    }

    if (current.type === 'LPAREN') {
      consume('LPAREN');
      const val = parseExpression();
      consume('RPAREN');
      return val;
    }

    throw new Error(`Unexpected token '${current.value}' in expression`);
  }

  const result = parseExpression();
  if (pos < tokens.length) {
    throw new Error(`Unparsed extra tokens at position ${pos}: '${tokens[pos].value}'`);
  }

  return { result: Number(result.toFixed(6)), expression: sanitized };
}

/**
 * Safe Relative and Absolute Date-Time Resolver
 * Handles "today", "tomorrow", "next tuesday", "in 5 days", "3 weeks from now", etc.
 */
export function resolveDateTime(query?: string, anchorDate: Date = new Date()): {
  iso: string;
  formatted: string;
  dayOfWeek: string;
  parsedOffset?: string;
  relativeDescription?: string;
} {
  const daysMap: Record<string, number> = {
    sunday: 0,
    monday: 1,
    tuesday: 2,
    wednesday: 3,
    thursday: 4,
    friday: 5,
    saturday: 6,
  };

  const target = new Date(anchorDate.getTime());
  const q = (query || '').toLowerCase().trim();

  let relativeDescription = 'Current date and time';

  if (q.includes('tomorrow')) {
    target.setDate(target.getDate() + 1);
    relativeDescription = 'Tomorrow';
  } else if (q.includes('yesterday')) {
    target.setDate(target.getDate() - 1);
    relativeDescription = 'Yesterday';
  } else if (/in\s+(\d+)\s+days?/.test(q)) {
    const match = q.match(/in\s+(\d+)\s+days?/);
    if (match) {
      const days = parseInt(match[1], 10);
      target.setDate(target.getDate() + days);
      relativeDescription = `${days} days from now`;
    }
  } else if (/in\s+(\d+)\s+weeks?/.test(q)) {
    const match = q.match(/in\s+(\d+)\s+weeks?/);
    if (match) {
      const weeks = parseInt(match[1], 10);
      target.setDate(target.getDate() + weeks * 7);
      relativeDescription = `${weeks} weeks from now`;
    }
  } else if (/in\s+(\d+)\s+hours?/.test(q)) {
    const match = q.match(/in\s+(\d+)\s+hours?/);
    if (match) {
      const hours = parseInt(match[1], 10);
      target.setHours(target.getHours() + hours);
      relativeDescription = `${hours} hours from now`;
    }
  } else {
    // Check "next [day]"
    for (const [dayName, dayIndex] of Object.entries(daysMap)) {
      if (q.includes(dayName)) {
        const currentDay = target.getDay();
        let diff = dayIndex - currentDay;
        if (diff <= 0 || q.includes('next')) {
          diff += 7;
        }
        target.setDate(target.getDate() + diff);
        relativeDescription = `Next ${dayName.charAt(0).toUpperCase() + dayName.slice(1)}`;
        break;
      }
    }
  }

  const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const dayOfWeek = daysOfWeek[target.getDay()];

  return {
    iso: target.toISOString(),
    formatted: target.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    dayOfWeek,
    relativeDescription,
  };
}

/**
 * Sanitizes errors so that internal database traces or stack traces do not leak to customers (FR-14).
 */
export function sanitizeCustomerError(err: unknown): {
  customerMessage: string;
  internalDetails: string;
} {
  const raw = err instanceof Error ? err.message : String(err);
  const stack = err instanceof Error ? err.stack || '' : '';

  let customerMessage = 'The autonomous agent encountered an issue processing your request. Please try again.';

  if (raw.includes('Division by zero')) {
    customerMessage = 'Calculation error: Division by zero is mathematically undefined.';
  } else if (raw.includes('Unexpected character') || raw.includes('Invalid numeric')) {
    customerMessage = `Mathematical expression syntax error: ${raw}`;
  } else if (raw.includes('rate limit') || raw.includes('429')) {
    customerMessage = 'System notice: Tenant rate limit reached. Please wait a few seconds before retrying.';
  } else if (raw.includes('Tenant not found') || raw.includes('unauthorized')) {
    customerMessage = 'Security exception: Tenant authorization validation failed.';
  }

  return {
    customerMessage,
    internalDetails: `${raw}\n${stack}`.trim(),
  };
}
