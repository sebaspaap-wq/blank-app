"use client";

import MenuOverlay from "./MenuOverlay";
import SearchOverlay from "./SearchOverlay";
import CartDrawer from "./CartDrawer";
import CustomCursor from "./CustomCursor";

export default function Overlays() {
  return (
    <>
      <MenuOverlay />
      <SearchOverlay />
      <CartDrawer />
      <CustomCursor />
    </>
  );
}
