import generated from "./images.generated.json";

export type CavaImage = {
  src: string;
  width: number;
  height: number;
  blurDataURL: string;
  alt: string;
};

type Generated = Record<
  string,
  { src: string; width: number; height: number; blurDataURL: string }
>;

const raw = generated as unknown as Generated;

function build(key: string, alt: string): CavaImage {
  const entry = raw[key];
  return { ...entry, alt };
}

export const IMAGES = {
  cacaoPool: build(
    "cava-cacao-pool",
    "CAVÁ Signature Robe in Cacao, worn open beside a Mediterranean pool"
  ),
  sandTerrace: build(
    "cava-sand-terrace",
    "CAVÁ Signature Robe in Sand, on a sunlit terrace above the sea"
  ),
  sandPoolside: build(
    "cava-sand-poolside",
    "CAVÁ Signature Robe in Sand, worn open beside an infinity pool"
  ),
  ivoryPoolside: build(
    "cava-ivory-poolside",
    "CAVÁ Signature Robe in Ivory, worn open on a terrace above the sea"
  ),
  ivoryInterior: build(
    "cava-ivory-interior",
    "CAVÁ Signature Robe in Ivory, in a villa interior at morning light"
  ),
  cacaoSunset: build(
    "cava-cacao-sunset",
    "CAVÁ Signature Robe in Cacao, on a terrace at sunset"
  ),
} as const;
