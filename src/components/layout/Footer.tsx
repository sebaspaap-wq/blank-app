import Link from "next/link";
import { Container } from "@/components/ui/Section";
import { Logo } from "./Logo";
import { company, footerNav, site } from "@/content/site";
import { ageNotice, mandatoryNotice } from "@/content/medical";

export function Footer() {
  return (
    <footer className="bg-charcoal text-bone">
      <Container>
        <div className="grid gap-14 py-20 lg:grid-cols-[1.1fr_2fr] lg:gap-16 lg:py-24">
          <div>
            <Logo className="text-bone" />
            <p className="mt-7 max-w-xs text-lede text-bone/55">{site.tagline}</p>
            <p className="mt-8 text-[0.9375rem] text-bone/55">
              {site.email}
              <br />
              {site.supportHours}
            </p>
          </div>

          <div className="grid gap-10 sm:grid-cols-3">
            {footerNav.map((group) => (
              <div key={group.title}>
                <h2 className="text-mono uppercase text-taupe">{group.title}</h2>
                <ul className="mt-6 space-y-3">
                  {group.items.map((item) => (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className="text-[0.9375rem] text-bone/60 underline-offset-4 transition-colors duration-300 hover:text-bone hover:underline"
                      >
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-bone/12 py-10">
          <p className="max-w-4xl text-xs leading-relaxed text-bone/55">
            {mandatoryNotice} {ageNotice} QUITTER 2 mg and 4 mg medicated chewing gum are
            non-prescription medicines. Registration and manufacturer details are published
            on our{" "}
            <Link href="/legal" className="underline underline-offset-4 hover:text-bone">
              legal page
            </Link>
            . Suspected side effects can be reported via{" "}
            <Link href="/pharmacovigilance" className="underline underline-offset-4 hover:text-bone">
              our pharmacovigilance page
            </Link>{" "}
            or to {company.sideEffectReportingName}.
          </p>

          <div className="mt-8 flex flex-col gap-4 text-xs text-bone/55 sm:flex-row sm:items-center sm:justify-between">
            <p>
              © {new Date().getFullYear()} {company.legalName} · KvK {company.kvk} · VAT{" "}
              {company.vat}
            </p>
            <p>Amsterdam, The Netherlands</p>
          </div>
        </div>
      </Container>
    </footer>
  );
}
