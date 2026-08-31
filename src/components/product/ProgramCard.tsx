"use client";

import { cx, formatPrice } from "@/lib/format";
import {
  individualValueCents,
  savingCents,
  totalBoxes,
  type Program,
} from "@/content/programs";

export function ProgramCard({
  program,
  selected,
  onSelect,
}: {
  program: Program;
  selected: boolean;
  onSelect: (program: Program) => void;
}) {
  const boxes = totalBoxes(program);
  const saving = savingCents(program);
  const contents = program.contents
    .map((line) => `${line.boxes}× ${line.strengthMg} mg`)
    .join("  ·  ");

  return (
    <button
      type="button"
      onClick={() => onSelect(program)}
      aria-pressed={selected}
      className={cx(
        "group relative flex h-full flex-col rounded-[20px] p-7 text-left transition-all duration-500 ease-[var(--ease-quit)] sm:p-9",
        selected
          ? "bg-charcoal text-bone shadow-[var(--shadow-lift)]"
          : "bg-white text-charcoal shadow-[var(--shadow-card)] hover:-translate-y-1 hover:shadow-[var(--shadow-lift)]",
      )}
    >
      {program.popular ? (
        <span
          className={cx(
            "absolute right-7 top-7 rounded-full px-3 py-1.5 text-mono uppercase sm:right-9 sm:top-9",
            selected ? "bg-bone/15 text-bone" : "bg-charcoal/[0.06] text-charcoal/65",
          )}
        >
          Most popular
        </span>
      ) : null}

      <p className={cx("text-mono uppercase", selected ? "text-taupe" : "text-label")}>
        {program.durationDays} days
      </p>

      <h3 className="mt-5 text-title">{program.name}</h3>
      <p className={cx("mt-2 text-[0.9375rem]", selected ? "text-bone/60" : "text-charcoal/65")}>
        {program.audience}
      </p>

      <div
        className={cx(
          "mt-7 border-t pt-6",
          selected ? "border-bone/15" : "border-charcoal/10",
        )}
      >
        <p className="text-[2rem] font-semibold leading-none tracking-[-0.035em]">
          {formatPrice(program.priceCents)}
        </p>
        <p className={cx("mt-3 text-sm", selected ? "text-bone/55" : "text-charcoal/65")}>
          {boxes} boxes · {contents}
        </p>
        {saving > 0 ? (
          <p className={cx("mt-1.5 text-sm", selected ? "text-taupe" : "text-label")}>
            {formatPrice(individualValueCents(program))} bought separately — you keep{" "}
            {formatPrice(saving)}
          </p>
        ) : null}
      </div>

      <span
        className={cx(
          "mt-8 inline-flex h-11 items-center justify-center rounded-full px-6 text-[0.9375rem] font-medium transition-colors duration-300",
          selected
            ? "bg-bone text-charcoal"
            : "border border-charcoal/20 text-charcoal group-hover:border-charcoal/60",
        )}
      >
        {selected ? `${program.name} selected` : `Select ${program.name}`}
      </span>
    </button>
  );
}
