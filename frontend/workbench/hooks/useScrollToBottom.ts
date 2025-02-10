/* Copied from https://github.com/All-Hands-AI/OpenHands/blob/main/frontend/src/hooks/useScrollToBottom.ts */

import { RefObject, useEffect, useState } from 'react';

export function useScrollToBottom(scrollRef: RefObject<HTMLDivElement>) {
  const [autoScroll, setAutoScroll] = useState(true);
  const [hitBottom, setHitBottom] = useState(true);

  const onChatBodyScroll = (el: HTMLElement) => {
    const bottomHeight = el.scrollTop + el.clientHeight;
    const isHitBottom = bottomHeight >= el.scrollHeight - 10;
    setHitBottom(isHitBottom);
    setAutoScroll(isHitBottom);
  };

  function scrollDomToBottom() {
    const dom = scrollRef.current;
    if (dom) {
      requestAnimationFrame(() => {
        setAutoScroll(true);
        dom.scrollTo({ top: dom.scrollHeight, behavior: 'auto' });
      });
    }
  }

  useEffect(() => {
    if (autoScroll) {
      scrollDomToBottom();
    }
  });

  return {
    scrollRef,
    autoScroll,
    setAutoScroll,
    scrollDomToBottom,
    hitBottom,
    setHitBottom,
    onChatBodyScroll,
  };
}
