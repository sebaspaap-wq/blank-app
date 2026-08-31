import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { MobileCta } from "@/components/layout/MobileCta";
import { CookieConsent } from "@/components/layout/CookieConsent";
import { company, site } from "@/content/site";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
  // Only the weights the design system actually uses.
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: `${site.name} — ${site.tagline}`,
    template: `%s — ${site.name}`,
  },
  description: site.description,
  applicationName: site.name,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: site.name,
    locale: site.locale,
    url: site.url,
    title: `${site.name} — ${site.tagline}`,
    description: site.description,
  },
  twitter: {
    card: "summary_large_image",
    title: `${site.name} — ${site.tagline}`,
    description: site.description,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true, "max-image-preview": "large" },
  },
  category: "health",
};

export const viewport: Viewport = {
  themeColor: "#f7f6f2",
  colorScheme: "light",
  width: "device-width",
  initialScale: 1,
};

/** Organisation identity only — no medicinal claims in structured data. */
const organisationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: site.name,
  legalName: company.legalName,
  url: site.url,
  email: site.email,
  address: {
    "@type": "PostalAddress",
    addressCountry: "NL",
    addressLocality: "Amsterdam",
  },
  contactPoint: {
    "@type": "ContactPoint",
    contactType: "customer support",
    email: site.email,
    areaServed: ["NL", "BE"],
    availableLanguage: ["nl", "en"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang={site.lang} className={`${inter.variable} no-js`}>
      <head>
        <script
          // Progressive enhancement: scroll-reveal content is visible by default
          // and only animates once JavaScript is confirmed to be running.
          dangerouslySetInnerHTML={{
            __html: `document.documentElement.classList.remove('no-js');`,
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organisationSchema) }}
        />
      </head>
      <body className="min-h-screen bg-bone text-charcoal antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[70] focus:rounded-full focus:bg-charcoal focus:px-5 focus:py-3 focus:text-sm focus:text-bone"
        >
          Skip to content
        </a>
        <Header />
        <main id="main">{children}</main>
        <Footer />
        <MobileCta />
        <CookieConsent />
      </body>
    </html>
  );
}
