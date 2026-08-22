import Link from "next/link";
import type { ComponentProps } from "react";

type Props = {
  href: string;
  children: React.ReactNode;
  className?: string;
  cursor?: string;
} & Omit<ComponentProps<typeof Link>, "href" | "className" | "children">;

export default function ArrowLink({ href, children, className = "", ...rest }: Props) {
  return (
    <Link href={href} className={`link-line nav-label ${className}`} {...rest}>
      <span>{children}</span>
      <span aria-hidden className="arrow">
        →
      </span>
    </Link>
  );
}
