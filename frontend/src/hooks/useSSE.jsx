import { useState, useEffect, useRef } from "react";
import { getSSEUrl } from "../api/reviews";

export function useSSE(reviewId, { onEvent, onDone, onError } = {}) {
  const [events, setEvents] = useState([]);
  const [done, setDone] = useState(false);
  const abortRef = useRef(null);

  useEffect(() => {
    if (!reviewId) return;

    const controller = new AbortController();
    abortRef.current = controller;

    const token = localStorage.getItem("token");
    const url = getSSEUrl(reviewId);

    (async () => {
      try {
        const resp = await fetch(url, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });

        if (!resp.ok) {
          onError?.(`HTTP ${resp.status}`);
          return;
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done: streamDone, value } = await reader.read();
          if (streamDone) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop();

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));
              setEvents((prev) => [...prev, event]);
              onEvent?.(event);
              if (event.status === "completed" || event.status === "failed") {
                setDone(true);
                onDone?.(event);
                return;
              }
            } catch {
              // skip malformed line
            }
          }
        }
      } catch (err) {
        if (err.name !== "AbortError") onError?.(err.message);
      }
    })();

    return () => controller.abort();
  }, [reviewId]);

  return { events, done };
}
