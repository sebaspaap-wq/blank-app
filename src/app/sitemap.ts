import type { MetadataRoute } from "next";
import { site } from "@/content/site";
import { legalSlugs } from "@/content/legal";

const marketingRoutes = ["", "/programs", "/how-it-works", "/quitter-zero", "/faq"];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  return [
    ...marketingRoutes.map((route) => ({
      url: `${site.url}${route}`,
      lastModified: now,
      changeFrequency: "monthly" as const,
      priority: route === "" ? 1 : 0.8,
    })),
    ...legalSlugs.map((slug) => ({
      url: `${site.url}/${slug}`,
      lastModified: now,
      changeFrequency: "yearly" as const,
      priority: 0.3,
    })),
  ];
}
