"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { usePathname } from "next/navigation";
import type { Product, Size } from "@/lib/products";

export type BagItem = {
  id: string;
  slug: string;
  colour: string;
  name: string;
  size: Size;
  price: number;
  quantity: number;
  image: string;
  blurDataURL: string;
};

type Overlay = "menu" | "bag" | "search" | null;

type SiteContextValue = {
  items: BagItem[];
  count: number;
  subtotal: number;
  add: (product: Product, size: Size) => void;
  remove: (id: string) => void;
  setQuantity: (id: string, quantity: number) => void;
  overlay: Overlay;
  open: (overlay: Exclude<Overlay, null>) => void;
  close: () => void;
  toggle: (overlay: Exclude<Overlay, null>) => void;
};

const SiteContext = createContext<SiteContextValue | null>(null);

const STORAGE_KEY = "cava.bag.v1";

export function SiteProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<BagItem[]>([]);
  const [overlay, setOverlay] = useState<Overlay>(null);
  const [hydrated, setHydrated] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) setItems(JSON.parse(stored) as BagItem[]);
    } catch {
      /* storage unavailable — the bag simply starts empty */
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      /* ignore */
    }
  }, [items, hydrated]);

  // Any navigation closes whatever is open.
  useEffect(() => {
    setOverlay(null);
  }, [pathname]);

  const close = useCallback(() => setOverlay(null), []);
  const open = useCallback((next: Exclude<Overlay, null>) => setOverlay(next), []);
  const toggle = useCallback(
    (next: Exclude<Overlay, null>) =>
      setOverlay((current) => (current === next ? null : next)),
    []
  );

  const add = useCallback((product: Product, size: Size) => {
    const id = `${product.slug}-${size}`;
    setItems((current) => {
      const existing = current.find((item) => item.id === id);
      if (existing) {
        return current.map((item) =>
          item.id === id ? { ...item, quantity: Math.min(9, item.quantity + 1) } : item
        );
      }
      return [
        ...current,
        {
          id,
          slug: product.slug,
          colour: product.colour,
          name: product.name,
          size,
          price: product.price,
          quantity: 1,
          image: product.hero.src,
          blurDataURL: product.hero.blurDataURL,
        },
      ];
    });
    setOverlay("bag");
  }, []);

  const remove = useCallback((id: string) => {
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  const setQuantity = useCallback((id: string, quantity: number) => {
    setItems((current) =>
      quantity <= 0
        ? current.filter((item) => item.id !== id)
        : current.map((item) =>
            item.id === id ? { ...item, quantity: Math.min(9, quantity) } : item
          )
    );
  }, []);

  const value = useMemo<SiteContextValue>(() => {
    const count = items.reduce((total, item) => total + item.quantity, 0);
    const subtotal = items.reduce((total, item) => total + item.price * item.quantity, 0);
    return { items, count, subtotal, add, remove, setQuantity, overlay, open, close, toggle };
  }, [items, add, remove, setQuantity, overlay, open, close, toggle]);

  return <SiteContext.Provider value={value}>{children}</SiteContext.Provider>;
}

export function useSite() {
  const context = useContext(SiteContext);
  if (!context) throw new Error("useSite must be used inside <SiteProvider>");
  return context;
}
