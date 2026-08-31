import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { PageHeader } from "./PageHeader";
import type { LegalPage } from "@/content/legal";
import { mandatoryNotice } from "@/content/medical";

/**
 * Renders any page from `src/content/legal.ts`. Structure is fixed; wording is
 * content, so counsel can drop in final text without touching components.
 */
export function LegalPageView({ page }: { page: LegalPage }) {
  return (
    <>
      <PageHeader eyebrow="Information" title={page.title} intro={page.intro} />

      <Section tone="bone" size="tight">
        <Container>
          <div className="grid gap-12 lg:grid-cols-[0.55fr_1.45fr] lg:gap-16">
            <aside className="lg:sticky lg:top-28 lg:self-start">
              <Eyebrow>On this page</Eyebrow>
              <ul className="mt-6 space-y-2">
                {page.sections.map((section) => (
                  <li key={section.heading}>
                    <a
                      href={`#${slugify(section.heading)}`}
                      className="text-[0.9375rem] text-charcoal/65 underline-offset-4 transition-colors hover:text-charcoal hover:underline"
                    >
                      {section.heading}
                    </a>
                  </li>
                ))}
              </ul>
              <p className="mt-8 text-mono uppercase text-label">
                Updated: {page.updated}
              </p>
            </aside>

            <div className="max-w-2xl">
              {page.sections.map((section) => (
                <section
                  key={section.heading}
                  id={slugify(section.heading)}
                  className="scroll-mt-28 border-t border-charcoal/10 py-10 first:border-t-0 first:pt-0"
                >
                  <h2 className="text-title">{section.heading}</h2>

                  {section.paragraphs?.map((paragraph) => (
                    <p
                      key={paragraph}
                      className="mt-5 text-[0.9375rem] leading-relaxed text-charcoal/65"
                    >
                      {paragraph}
                    </p>
                  ))}

                  {section.bullets ? (
                    <ul className="mt-6 space-y-3">
                      {section.bullets.map((bullet) => (
                        <li
                          key={bullet}
                          className="flex gap-4 text-[0.9375rem] leading-relaxed text-charcoal/65"
                        >
                          <span
                            aria-hidden="true"
                            className="mt-2.5 block size-1 shrink-0 rounded-full bg-taupe"
                          />
                          {bullet}
                        </li>
                      ))}
                    </ul>
                  ) : null}

                  {section.rows ? (
                    <dl className="mt-6 divide-y divide-charcoal/10 border-y border-charcoal/10">
                      {section.rows.map((row) => (
                        <div key={row.label} className="grid gap-1 py-4 sm:grid-cols-[0.6fr_1.4fr] sm:gap-6">
                          <dt className="text-mono uppercase text-label">{row.label}</dt>
                          <dd className="text-[0.9375rem] text-charcoal/75">{row.value}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : null}
                </section>
              ))}

              <p className="mt-10 border-t border-charcoal/10 pt-10 text-xs leading-relaxed text-charcoal/65">
                {mandatoryNotice}
              </p>
            </div>
          </div>
        </Container>
      </Section>
    </>
  );
}

const slugify = (value: string): string =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
