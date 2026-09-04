"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { getTranslation } from "@/lib/translations";

type TextSize = "normal" | "large" | "larger";

interface AccessibilityContextType {
  highContrast: boolean;
  toggleHighContrast: () => void;
  textSize: TextSize;
  increaseTextSize: () => void;
  decreaseTextSize: () => void;
  resetAccessibility: () => void;
  language: string;
  setLanguage: (lang: string) => void;
  t: (key: string) => string;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

export function AccessibilityProvider({ children }: { children: React.ReactNode }) {
  const [highContrast, setHighContrast] = useState(false);
  const [textSize, setTextSize] = useState<TextSize>("normal");
  const [language, setLanguage] = useState("en");

  // Load saved preferences from localStorage on mount
  useEffect(() => {
    try {
      const savedContrast = localStorage.getItem("gov_high_contrast");
      if (savedContrast === "true") setHighContrast(true);

      const savedTextSize = localStorage.getItem("gov_text_size") as TextSize;
      if (savedTextSize) setTextSize(savedTextSize);

      const savedLang = localStorage.getItem("gov_language");
      if (savedLang) setLanguage(savedLang);
    } catch {
      // Ignore local storage errors in private browsing
    }
  }, []);

  // Update DOM classes for accessibility
  useEffect(() => {
    const root = document.documentElement;

    if (highContrast) {
      root.classList.add("high-contrast");
    } else {
      root.classList.remove("high-contrast");
    }

    root.classList.remove("text-size-normal", "text-size-large", "text-size-larger");
    root.classList.add(`text-size-${textSize}`);

    try {
      localStorage.setItem("gov_high_contrast", String(highContrast));
      localStorage.setItem("gov_text_size", textSize);
      localStorage.setItem("gov_language", language);
    } catch {}
  }, [highContrast, textSize, language]);

  const toggleHighContrast = () => setHighContrast((prev) => !prev);

  const increaseTextSize = () => {
    if (textSize === "normal") setTextSize("large");
    else if (textSize === "large") setTextSize("larger");
  };

  const decreaseTextSize = () => {
    if (textSize === "larger") setTextSize("large");
    else if (textSize === "large") setTextSize("normal");
  };

  const resetAccessibility = () => {
    setHighContrast(false);
    setTextSize("normal");
  };

  const t = (key: string) => getTranslation(language, key);

  return (
    <AccessibilityContext.Provider
      value={{
        highContrast,
        toggleHighContrast,
        textSize,
        increaseTextSize,
        decreaseTextSize,
        resetAccessibility,
        language,
        setLanguage,
        t,
      }}
    >
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error("useAccessibility must be used within an AccessibilityProvider");
  }
  return context;
}

export function useTranslation() {
  const { t, language, setLanguage } = useAccessibility();
  return { t, language, setLanguage };
}

