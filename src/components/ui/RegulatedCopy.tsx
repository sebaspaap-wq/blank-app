import { cx } from "@/lib/format";
import type { RegulatedBlock } from "@/content/medical";

/**
 * Renders a block of regulated copy from `src/content/medical.ts`.
 *
 * The wording lives in content, never in a component, so approved text can
 * replace a placeholder in one edit. Blocks still awaiting approval are marked
 * in non-production builds only — visitors never see internal status.
 */
export function RegulatedCopy({
  block,
  className,
  headingLevel: Heading = "h3",
}: {
  block: RegulatedBlock;
  className?: string;
  headingLevel?: "h2" | "h3" | "h4";
}) {
  const unapproved =
    block.status === "awaiting-approval" && process.env.NODE_ENV !== "production";

  return (
    <div
      className={cx(
        "max-w-2xl",
        unapproved && "rounded-lg outline outline-1 outline-dashed outline-taupe/60",
        className,
      )}
      data-copy-status={block.status}
      data-copy-id={block.id}
    >
      <Heading className="text-[1.125rem] font-semibold tracking-[-0.02em]">
        {block.title}
      </Heading>
      {block.body.map((paragraph) => (
        <p
          key={paragraph}
          className="mt-4 text-[0.9375rem] leading-relaxed text-charcoal/65"
        >
          {paragraph}
        </p>
      ))}
      {unapproved ? (
        <p className="mt-4 text-mono uppercase text-label">
          Placeholder — awaiting approved copy
        </p>
      ) : null}
    </div>
  );
}
