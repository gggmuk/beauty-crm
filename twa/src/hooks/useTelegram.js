import { useEffect, useState } from 'react';

const tg = window.Telegram?.WebApp;

export function useTelegram() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
      if (tg.initDataUnsafe?.user) {
        setUser(tg.initDataUnsafe.user);
      }
    }
  }, []);

  const onClose = () => {
    tg?.close();
  };

  const showMainButton = (text, onClick) => {
    if (!tg?.MainButton) return;
    tg.MainButton.text = text;
    tg.MainButton.show();
    tg.MainButton.onClick(onClick);
  };

  const hideMainButton = () => {
    tg?.MainButton?.hide();
  };

  return {
    tg,
    user,
    onClose,
    showMainButton,
    hideMainButton,
    initData: tg?.initData,
  };
}
