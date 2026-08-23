import { useEffect, useRef } from 'react';

export default function useWebSocket(path, onMessage) {
  const socketRef = useRef(null);
  const handlerRef = useRef(onMessage);
  const reconnectTimerRef = useRef(null);
  const shouldReconnectRef = useRef(true);

  useEffect(() => {
    handlerRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    if (!path) return;
    shouldReconnectRef.current = true;

    const connect = () => {
      const token = localStorage.getItem('access');
      if (!token) return;

      // VITE_WS_URL should be like:
      //   dev:  ws://127.0.0.1:8000
      //   prod: wss://netdesk-ptcx.onrender.com
      const wsBase = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000';
      const url = `${wsBase}/ws/${path}?token=${encodeURIComponent(token)}`;

      const ws = new WebSocket(url);
      socketRef.current = ws;

      ws.onopen = () => console.log('[WS] connected:', path);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handlerRef.current?.(data);
        } catch (err) {
          console.warn('[WS] bad JSON', err);
        }
      };

      ws.onclose = (event) => {
        console.log('[WS] closed:', path, event.code);
        socketRef.current = null;
        if (shouldReconnectRef.current && event.code !== 4001) {
          reconnectTimerRef.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = (err) => console.warn('[WS] error:', err);
    };

    connect();

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [path]);
}