import Link from "next/link";
import RevealText from "@/components/ui/RevealText";

export default function NotFound() {
  return (
    <div className="flex min-h-[80svh] flex-col items-center justify-center gutter text-center">
      <p className="eyebrow opacity-40">404</p>
      <RevealText
        as="h1"
        lines={["NOTHING HERE,", "ONLY QUIET."]}
        className="font-serif-display mt-8 text-[clamp(2.25rem,7vw,5rem)]"
      />
      <div className="mt-12">
        <Link href="/" className="link-line nav-label">
          <span>RETURN TO CAVÁ</span>
          <span aria-hidden className="arrow">→</span>
        </Link>
      </div>
    </div>
  );
}
