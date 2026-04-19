import { useEffect, useRef } from "react";

/**
 * Hook personnalisé pour debounce une fonction
 * @param fn - Fonction à débouncer
 * @param delay - Délai en millisecondes (défaut: 500ms)
 */
export function useDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 500
): T {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const debouncedFn = ((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      fn(...args);
    }, delay);
  }) as T;

  return debouncedFn;
}
