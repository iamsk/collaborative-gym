import { clsx, type ClassValue } from 'clsx';
import { customAlphabet } from 'nanoid';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export const nanoid = customAlphabet(
  '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
  7
);

export async function fetcher<JSON = any>(
  input: RequestInfo,
  init?: RequestInit
): Promise<JSON> {
  const res = await fetch(input, init);

  if (!res.ok) {
    const json = await res.json();
    if (json.error) {
      const error = new Error(json.error) as Error & { status: number };
      error.status = res.status;
      throw error;
    } else {
      throw new Error('An unexpected error occurred');
    }
  }

  return res.json();
}

export function formatDate(input: string | number | Date): string {
  const date = new Date(input);
  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

export const formatNumber = (value: number): string =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);

export const runAsyncFnWithoutBlocking = (
  fn: (...args: any[]) => Promise<any>
): void => {
  fn();
};

export const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

export const getStringFromBuffer = (buffer: ArrayBuffer): string =>
  Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

export enum ResultCode {
  InvalidCredentials = 'INVALID_CREDENTIALS',
  InvalidSubmission = 'INVALID_SUBMISSION',
  UserAlreadyExists = 'USER_ALREADY_EXISTS',
  UnknownError = 'UNKNOWN_ERROR',
  UserCreated = 'USER_CREATED',
  UserLoggedIn = 'USER_LOGGED_IN',
}

export const getMessageFromCode = (resultCode: string): string | undefined => {
  switch (resultCode) {
    case ResultCode.InvalidCredentials:
      return 'Invalid credentials!';
    case ResultCode.InvalidSubmission:
      return 'Invalid submission, please try again!';
    case ResultCode.UserAlreadyExists:
      return 'User already exists, please log in!';
    case ResultCode.UserCreated:
      return 'User created, welcome!';
    case ResultCode.UnknownError:
      return 'Something went wrong, please try again!';
    case ResultCode.UserLoggedIn:
      return 'Logged in!';
  }
};

export function format(date: Date, formatString: string): string {
  const year = date.getFullYear();
  const month = date.getMonth();
  const day = date.getDate();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');

  const monthNames = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];

  return formatString
    .replace('yyyy', year.toString())
    .replace('yy', String(year).slice(-2))
    .replace('LLL', monthNames[month])
    .replace('MM', String(month + 1).padStart(2, '0'))
    .replace('dd', String(day).padStart(2, '0'))
    .replace('d', day.toString())
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds);
}

export function parseISO(dateString: string): Date {
  return new Date(dateString);
}

export function subMonths(date: Date, amount: number): Date {
  const newDate = new Date(date);
  newDate.setMonth(newDate.getMonth() - amount);
  return newDate;
}

interface EventActionHistory {
  args?: {
    LLM_API_KEY?: string;
    [key: string]: unknown;
  };
  extras?: {
    open_page_urls: string[];
    active_page_index: number;
    dom_object: Record<string, unknown>;
    axtree_object: Record<string, unknown>;
    extra_element_properties: Record<string, unknown>;
    last_browser_action: string;
    last_browser_action_error: unknown;
    focused_element_bid: string;
  };
  [key: string]: unknown;
}

export const removeUnwantedKeys = (
  data: EventActionHistory[]
): EventActionHistory[] => {
  const UNDESIRED_KEYS = [
    'open_page_urls',
    'active_page_index',
    'dom_object',
    'axtree_object',
    'extra_element_properties',
    'last_browser_action',
    'last_browser_action_error',
    'focused_element_bid',
  ];

  return data.map((item) => {
    const newItem = { ...item };
    if (newItem.extras) {
      const newExtras = { ...newItem.extras };
      UNDESIRED_KEYS.forEach((key) => {
        delete newExtras[key as keyof typeof newExtras];
      });
      newItem.extras = newExtras;
    }
    return newItem;
  });
};

export const removeApiKey = (
  data: EventActionHistory[]
): EventActionHistory[] =>
  data.map((item) => {
    const newItem = { ...item };
    if (newItem.args?.LLM_API_KEY) {
      const newArgs = { ...newItem.args };
      delete newArgs.LLM_API_KEY;
      newItem.args = newArgs;
    }
    return newItem;
  });

export const getExtension = (code: string): string => {
  if (code.includes('.')) {
    return code.split('.').pop() || '';
  }
  return '';
};

/**
 * Format a timestamp to a human-readable format.
 *
 * @example
 * formatTimestamp('2021-10-10T10:10:10.000') // "10/10/2021, 10:10:10"
 * formatTimestamp('2021-10-10T22:10:10.000') // "10/10/2021, 22:10:10"
 */
export const formatTimestamp = (timestamp: string): string =>
  new Date(timestamp).toLocaleString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
