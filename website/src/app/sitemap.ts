import type { MetadataRoute } from "next";

const BASE = "https://www.useorchestra.dev";

const pages = [
  { url: "/", priority: 1.0, changeFrequency: "weekly" as const },
  { url: "/features", priority: 0.9, changeFrequency: "monthly" as const },
  { url: "/pricing", priority: 0.9, changeFrequency: "monthly" as const },
  { url: "/security", priority: 0.7, changeFrequency: "monthly" as const },
  { url: "/faq", priority: 0.7, changeFrequency: "monthly" as const },
  { url: "/contact", priority: 0.6, changeFrequency: "monthly" as const },
  { url: "/demo", priority: 0.8, changeFrequency: "monthly" as const },
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  return pages.map((page) => ({
    url: `${BASE}${page.url}`,
    lastModified: new Date(),
    changeFrequency: page.changeFrequency,
    priority: page.priority,
  }));
}
