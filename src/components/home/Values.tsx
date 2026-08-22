const VALUES = [
  {
    title: "PREMIUM QUALITY",
    copy: "Crafted from the finest materials for ultimate comfort.",
    icon: (
      <>
        <path d="M20 5 L33 20 L20 35 L7 20 Z" />
        <path d="M13.5 20 h13" />
      </>
    ),
  },
  {
    title: "TIMELESS DESIGN",
    copy: "Minimal, elegant and made to last beyond seasons.",
    icon: (
      <>
        <circle cx="20" cy="20" r="14" />
        <path d="M20 10.5 V20 l6.5 4" />
      </>
    ),
  },
  {
    title: "MADE TO FEEL",
    copy: "Thoughtfully designed for your everyday rituals.",
    icon: (
      <>
        <path d="M6 17c3.5-4 6.5-4 10 0s6.5 4 10 0 6.5-4 8-2" />
        <path d="M6 25c3.5-4 6.5-4 10 0s6.5 4 10 0 6.5-4 8-2" />
      </>
    ),
  },
  {
    title: "SLOW LIVING",
    copy: "For the moments that belong to you.",
    icon: (
      <>
        <path d="M5 27h30" />
        <path d="M9 27a11 11 0 0 1 22 0" />
        <path d="M20 6v3.5M31.5 10.5l-2.4 2.4M8.5 10.5l2.4 2.4" />
      </>
    ),
  },
];

export default function Values() {
  return (
    <section className="on-dark bg-noir py-24 text-ivory md:py-36">
      <div className="gutter">
        <div className="grid gap-y-16 md:grid-cols-2 lg:grid-cols-4 lg:gap-x-0">
          {VALUES.map((value, index) => (
            <div
              key={value.title}
              data-reveal
              style={{ ["--reveal-delay" as string]: `${index * 110}ms` }}
              className={[
                "lg:px-10",
                index === 0 ? "lg:pl-0" : "",
                index === VALUES.length - 1 ? "lg:pr-0" : "",
                index !== 0 ? "lg:border-l lg:border-[rgba(245,242,235,0.14)]" : "",
              ].join(" ")}
            >
              <svg
                width="40"
                height="40"
                viewBox="0 0 40 40"
                fill="none"
                stroke="currentColor"
                strokeWidth="0.75"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden
                className="opacity-70"
              >
                {value.icon}
              </svg>

              <h3 className="eyebrow mt-9">{value.title}</h3>
              <p className="body-copy mt-5 max-w-[17rem] text-[0.8125rem] opacity-50">
                {value.copy}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
