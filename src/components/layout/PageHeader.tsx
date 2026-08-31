import { Container, Eyebrow } from "@/components/ui/Section";
import { cx } from "@/lib/format";

export function PageHeader({
  eyebrow,
  title,
  intro,
  className,
}: {
  eyebrow: string;
  title: string;
  intro?: string;
  className?: string;
}) {
  return (
    <header className={cx("bg-bone pb-14 pt-32 sm:pb-20 sm:pt-40", className)}>
      <Container>
        <Eyebrow className="rise">{eyebrow}</Eyebrow>
        <h1 className="rise mt-6 max-w-3xl text-headline">{title}</h1>
        {intro ? (
          <p className="rise mt-7 max-w-2xl text-lede text-charcoal/65">{intro}</p>
        ) : null}
      </Container>
    </header>
  );
}
