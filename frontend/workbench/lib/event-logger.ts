/* Copied from https://github.com/All-Hands-AI/OpenHands/blob/main/frontend/src/utils/event-logger.ts */

/* eslint-disable no-console */

/**
 * A utility class for logging events. This class will only log events in development mode.
 */
class EventLogger {
  private static isDevMode = process.env.NODE_ENV === 'development';

  static message(message: string): void {
    if (this.isDevMode) {
      console.warn(message);
    }
  }

  static event(event: Event, name?: string): void {
    if (this.isDevMode) {
      console.warn(name || 'EVENT', event);
    }
  }

  static warning(warning: string): void {
    if (this.isDevMode) {
      console.warn(warning);
    }
  }

  static error(error: string): void {
    if (this.isDevMode) {
      console.error(error);
    }
  }
}

export default EventLogger;

  