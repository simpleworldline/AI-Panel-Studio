import type { WsServerEvent, WsClientCommand } from '../types/ws';
import { keysToSnake, keysToCamel } from '../utils/transform';

type EventHandler = (event: WsServerEvent) => void;

export class StudioWebSocket {
  private ws: WebSocket | null = null;
  private discussionId: string;
  private sessionId: string;
  private handler: EventHandler;
  private reconnectAttempt = 0;
  private maxReconnect = 3;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closed = false;

  constructor(discussionId: string, sessionId: string, handler: EventHandler) {
    this.discussionId = discussionId;
    this.sessionId = sessionId;
    this.handler = handler;
  }

  connect() {
    if (this.ws) return;
    this.closed = false;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/discussions/${this.discussionId}?session_id=${this.sessionId}`;
    this.ws = new WebSocket(url);
    this.ws.onmessage = (ev) => {
      try {
        // snake_case → camelCase (后端 Python 输出 snake_case)
        const raw = JSON.parse(ev.data);
        const event = keysToCamel(raw) as WsServerEvent;
        this.handler(event);
      } catch {
        // ignore malformed messages
      }
    };
    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
    };
    this.ws.onclose = () => {
      this.ws = null;
      if (!this.closed) this.scheduleReconnect();
    };
    this.ws.onerror = () => {
      // onclose will fire after this
    };
  }

  send(command: WsClientCommand) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      // camelCase → snake_case (发送到后端 Python)
      this.ws.send(JSON.stringify(keysToSnake(command)));
    }
  }

  close() {
    this.closed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null; // prevent reconnect
      this.ws.close();
      this.ws = null;
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempt >= this.maxReconnect) return;
    const delay = Math.pow(2, this.reconnectAttempt) * 1000;
    this.reconnectAttempt++;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.closed) this.connect();
    }, delay);
  }
}
