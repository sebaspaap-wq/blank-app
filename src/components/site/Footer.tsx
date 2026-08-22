import Link from "next/link";
import NewsletterForm from "./NewsletterForm";

const COLUMNS = [
  {
    title: "SHOP",
    links: [
      { label: "Collection", href: "/collection" },
      { label: "Sand", href: "/collection/sand" },
      { label: "Ivory", href: "/collection/ivory" },
      { label: "Cacao", href: "/collection/cacao" },
    ],
  },
  {
    title: "ABOUT",
    links: [
      { label: "Our Story", href: "/about" },
      { label: "Journal", href: "/journal" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    title: "SERVICE",
    links: [
      { label: "Shipping", href: "/service/shipping" },
      { label: "Returns", href: "/service/returns" },
      { label: "Size Guide", href: "/service/size-guide" },
      { label: "Care", href: "/service/care" },
    ],
  },
];

const SOCIAL = [
  {
    label: "Instagram",
    href: "https://instagram.com",
    path: (
      <>
        <rect x="3" y="3" width="18" height="18" rx="4.5" />
        <circle cx="12" cy="12" r="4.1" />
        <circle cx="17.4" cy="6.6" r="0.6" fill="currentColor" stroke="none" />
      </>
    ),
  },
  {
    label: "Pinterest",
    href: "https://pinterest.com",
    path: (
      <>
        <circle cx="12" cy="12" r="9.2" />
        <path d="M10.1 17.6c-.35 1.4-.8 2.4-1.2 3.1" />
        <path d="M9.4 16.2c1.9 1 4.1.4 5.2-1.3 1.3-2 1-4.9-.8-6.1-1.9-1.3-4.9-.8-6.1 1.1-.9 1.4-.7 3 .3 3.7" />
      </>
    ),
  },
  {
    label: "TikTok",
    href: "https://tiktok.com",
    path: (
      <>
        <path d="M14.2 3.2v10.9a3.6 3.6 0 1 1-3.1-3.6" />
        <path d="M14.2 3.2c.4 2.3 1.9 3.9 4.3 4.1" />
      </>
    ),
  },
];

export default function Footer() {
  return (
    <footer className="on-dark relative bg-noir text-ivory">
      <div className="gutter pb-10 pt-20 md:pb-12 md:pt-32">
        <div className="grid gap-16 lg:grid-cols-[1.15fr_2fr_1.1fr] lg:gap-12">
          {/* identity */}
          <div data-reveal>
            <p className="wordmark text-[2.25rem] md:text-[2.75rem]">CAVÁ</p>
            <p className="eyebrow mt-6 opacity-45">THE ART OF SLOW LIVING</p>

            <ul className="mt-10 flex items-center gap-6">
              {SOCIAL.map((item) => (
                <li key={item.label}>
                  <a
                    href={item.href}
                    target="_blank"
                    rel="noreferrer noopener"
                    aria-label={item.label}
                    className="block opacity-45 transition-opacity duration-700 hover:opacity-100"
                    style={{ transitionTimingFunction: "var(--ease)" }}
                  >
                    <svg
                      width="19"
                      height="19"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="0.9"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      {item.path}
                    </svg>
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* navigation columns */}
          <div className="grid grid-cols-2 gap-10 sm:grid-cols-3 lg:px-8" data-reveal style={{ ["--reveal-delay" as string]: "90ms" }}>
            {COLUMNS.map((column) => (
              <nav key={column.title} aria-label={column.title}>
                <h3 className="eyebrow opacity-40">{column.title}</h3>
                <ul className="mt-7 space-y-3.5">
                  {column.links.map((link) => (
                    <li key={link.href}>
                      <Link
                        href={link.href}
                        className="body-copy inline-block text-[0.8125rem] opacity-70 transition-opacity duration-500 hover:opacity-100"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            ))}
          </div>

          {/* newsletter */}
          <div data-reveal style={{ ["--reveal-delay" as string]: "180ms" }}>
            <h3 className="eyebrow opacity-40">JOIN THE CAVÁ WORLD</h3>
            <p className="body-copy mt-7 max-w-[24rem] text-[0.8125rem] opacity-70">
              Be the first to discover new arrivals and exclusive offers.
            </p>
            <NewsletterForm />
          </div>
        </div>

        <div className="mt-20 flex flex-col gap-4 border-t border-[rgba(245,242,235,0.14)] pt-8 text-[0.6875rem] tracking-[0.14em] opacity-40 md:flex-row md:items-center md:justify-between">
          <p>© {new Date().getFullYear()} CAVÁ. ALL RIGHTS RESERVED.</p>
          <ul className="flex gap-8">
            <li>
              <Link href="/service/shipping" className="hover:opacity-100">PRIVACY</Link>
            </li>
            <li>
              <Link href="/service/returns" className="hover:opacity-100">TERMS</Link>
            </li>
            <li>DESIGNED IN EUROPE</li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
