import React, { useEffect, useRef, useState } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";

export type ToastOptions = {
  text: string;
  color?: string;
  duration?: number;
};

type ToastListener = (options: ToastOptions) => void;

const listeners = new Set<ToastListener>();

const subscribeToast = (listener: ToastListener): (() => void) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};

export const showToast = (text: string, color: string = "#333333", duration: number = 2500): void => {
  const payload: ToastOptions = { text, color, duration };
  listeners.forEach((listener) => listener(payload));
};

export const ToastHost: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [text, setText] = useState("");
  const [backgroundColor, setBackgroundColor] = useState("#333333");
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(20)).current;
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const unsubscribe = subscribeToast(({ text: nextText, color, duration }) => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }

      setText(nextText);
      setBackgroundColor(color || "#333333");
      setVisible(true);

      Animated.parallel([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 180,
          useNativeDriver: true,
        }),
        Animated.timing(translateY, {
          toValue: 0,
          duration: 180,
          useNativeDriver: true,
        }),
      ]).start();

      timerRef.current = setTimeout(() => {
        Animated.parallel([
          Animated.timing(opacity, {
            toValue: 0,
            duration: 180,
            useNativeDriver: true,
          }),
          Animated.timing(translateY, {
            toValue: 20,
            duration: 180,
            useNativeDriver: true,
          }),
        ]).start(() => {
          setVisible(false);
        });
      }, duration || 2500);
    });

    return () => {
      unsubscribe();
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [opacity, translateY]);

  if (!visible) {
    return null;
  }

  return React.createElement(
    View,
    { pointerEvents: "none", style: styles.container },
    React.createElement(
      Animated.View,
      {
        style: [
          styles.toast,
          {
            backgroundColor,
            opacity,
            transform: [{ translateY }],
          },
        ],
      },
      React.createElement(Text, { style: styles.text }, text)
    )
  );
};

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    left: 0,
    right: 0,
    top: 60,
    alignItems: "center",
    zIndex: 9999,
    minHeight: 40,
  },
  toast: {
    minWidth: 280,
    maxWidth: "92%",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  text: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "600",
  },
});
