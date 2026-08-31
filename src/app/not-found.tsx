import { ButtonLink } from "@/components/ui/Button";
import { Container, Eyebrow } from "@/components/ui/Section";

export default function NotFound() {
  return (
    <Container className="flex min-h-[70vh] flex-col justify-center py-32">
      <Eyebrow>404</Eyebrow>
      <h1 className="mt-6 max-w-xl text-headline">This page took a different route.</h1>
      <p className="mt-6 max-w-md text-lede text-charcoal/65">
        The link is gone or was never here. The programme is where it always was.
      </p>
      <div className="mt-10 flex flex-wrap gap-3">
        <ButtonLink href="/programs" size="lg" arrow>
          Start my 90 days
        </ButtonLink>
        <ButtonLink href="/" variant="outline" size="lg">
          Back to home
        </ButtonLink>
      </div>
    </Container>
  );
}
