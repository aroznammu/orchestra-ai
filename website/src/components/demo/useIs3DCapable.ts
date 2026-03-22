"use client";

import { useState, useEffect } from "react";

function detectWebGL2(): boolean {
  try {
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl2");
    return gl !== null;
  } catch {
    return false;
  }
}

export default function useIs3DCapable(minWidth = 1024): boolean {
  const [capable, setCapable] = useState(false);

  useEffect(() => {
    const isDesktop = window.innerWidth >= minWidth;
    const hasWebGL = detectWebGL2();
    setCapable(isDesktop && hasWebGL);
  }, [minWidth]);

  return capable;
}
