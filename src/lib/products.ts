import { IMAGES, type CavaImage } from "./images";

export type Size = "XS" | "S" | "M" | "L" | "XL";

export const SIZES: Size[] = ["XS", "S", "M", "L", "XL"];

export type Product = {
  slug: string;
  colour: string;
  name: string;
  subtitle: string;
  price: number;
  swatch: string;
  description: string;
  /** Campaign frame used on the product page. */
  hero: CavaImage;
  /** Second frame on the product page — a detail crop, or a second look. */
  secondary: CavaImage;
  secondaryPosition: string;
  secondaryZoom?: number;
  /** Frame used wherever the product appears in a listing. */
  card: CavaImage;
  cardPosition: string;
  details: string[];
  material: string[];
  care: string[];
  index: string;
};

export const PRODUCTS: Product[] = [
  {
    slug: "sand",
    colour: "SAND",
    name: "The Signature Robe",
    subtitle: "Cotton terry · Warm sand",
    price: 149,
    swatch: "#c8b6a2",
    index: "01",
    description:
      "The signature CAVÁ robe, designed for slow mornings, quiet afternoons and evenings that linger.",
    hero: IMAGES.sandTerrace,
    secondary: IMAGES.sandPoolside,
    secondaryPosition: "object-[50%_30%]",
    card: IMAGES.sandTerrace,
    cardPosition: "object-[50%_40%]",
    details: [
      "Shawl collar with tonal piping",
      "Self-tie belt and interior fastening",
      "Two patch pockets, side vents",
      "Relaxed, unisex fit — mid-thigh length",
      "Discreet tonal CAVÁ embroidery at the chest",
    ],
    material: [
      "550 gsm long-staple cotton terry, woven in Portugal",
      "Garment washed for immediate softness",
      "Machine wash at 40°C with like colours",
      "Tumble dry low to restore the pile — do not bleach",
    ],
    care: [],
  },
  {
    slug: "ivory",
    colour: "IVORY",
    name: "The Signature Robe",
    subtitle: "Cotton terry · Soft ivory",
    price: 149,
    swatch: "#f0ebe0",
    index: "02",
    description:
      "The signature CAVÁ robe, designed for slow mornings, quiet afternoons and evenings that linger.",
    hero: IMAGES.ivoryInterior,
    secondary: IMAGES.ivoryPoolside,
    secondaryPosition: "object-[50%_28%]",
    card: IMAGES.ivoryInterior,
    cardPosition: "object-[50%_38%]",
    details: [
      "Shawl collar with tonal piping",
      "Self-tie belt and interior fastening",
      "Two patch pockets, side vents",
      "Relaxed, unisex fit — mid-thigh length",
      "Discreet tonal CAVÁ embroidery at the chest",
    ],
    material: [
      "550 gsm long-staple cotton terry, woven in Portugal",
      "Garment washed for immediate softness",
      "Machine wash at 40°C with like colours",
      "Tumble dry low to restore the pile — do not bleach",
    ],
    care: [],
  },
  {
    slug: "cacao",
    colour: "CACAO",
    name: "The Signature Robe",
    subtitle: "Cotton terry · Deep cacao",
    price: 149,
    swatch: "#3a2920",
    index: "03",
    description:
      "The signature CAVÁ robe, designed for slow mornings, quiet afternoons and evenings that linger.",
    hero: IMAGES.cacaoSunset,
    secondary: IMAGES.cacaoPool,
    secondaryPosition: "object-[54%_30%]",
    card: IMAGES.cacaoPool,
    cardPosition: "object-[54%_30%]",
    details: [
      "Shawl collar with tonal piping",
      "Self-tie belt and interior fastening",
      "Two patch pockets, side vents",
      "Relaxed, unisex fit — mid-thigh length",
      "Discreet tonal CAVÁ embroidery at the chest",
    ],
    material: [
      "550 gsm long-staple cotton terry, woven in Portugal",
      "Garment washed for immediate softness",
      "Machine wash at 40°C with like colours",
      "Tumble dry low to restore the pile — do not bleach",
    ],
    care: [],
  },
];

export function getProduct(slug: string): Product | undefined {
  return PRODUCTS.find((p) => p.slug === slug);
}

export function formatPrice(value: number): string {
  return `€${value.toLocaleString("de-DE")}`;
}
