import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";
import { reviewPlaceholder, reviewSummary, reviews } from "@/content/reviews";

function Stars({ rating }: { rating: number }) {
  return (
    <span className="inline-flex gap-0.5 text-charcoal" aria-label={`${rating} out of 5`}>
      {Array.from({ length: 5 }, (_, index) => (
        <span key={index} aria-hidden="true" className={index < rating ? "" : "text-charcoal/20"}>
          ★
        </span>
      ))}
    </span>
  );
}

/**
 * Social proof.
 *
 * The layout is finished, the content is not: nothing renders until verified
 * customer reviews exist in `src/content/reviews.ts`. No placeholder review
 * text is ever shown as if it were real.
 */
export function SocialProof() {
  const hasReviews = reviews.length > 0;

  return (
    <Section tone="deep" size="tight">
      <Container>
        <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
          <Reveal>
            <Eyebrow>Customers</Eyebrow>
            <h2 className="mt-5 text-title">
              {hasReviews ? "What people say" : reviewPlaceholder.title}
            </h2>
            {hasReviews && reviewSummary.average !== null ? (
              <p className="mt-5 flex items-center gap-3 text-[0.9375rem] text-charcoal/65">
                <Stars rating={Math.round(reviewSummary.average)} />
                {reviewSummary.average.toFixed(1)} average
                {reviewSummary.count ? ` · ${reviewSummary.count} verified reviews` : null}
              </p>
            ) : (
              <p className="mt-5 max-w-sm text-[0.9375rem] leading-relaxed text-charcoal/65">
                {reviewPlaceholder.body}
              </p>
            )}
          </Reveal>

          {hasReviews ? (
            <div className="grid gap-5 sm:grid-cols-2">
              {reviews.slice(0, 4).map((review, index) => (
                <Reveal key={review.id} delay={index * 80}>
                  <figure className="h-full rounded-[18px] bg-white p-7 shadow-[var(--shadow-card)]">
                    <Stars rating={review.rating} />
                    <blockquote className="mt-5 text-[0.9375rem] leading-relaxed text-charcoal/75">
                      {review.body}
                    </blockquote>
                    <figcaption className="mt-6 text-mono uppercase text-label">
                      {review.author}
                      {review.verified ? " · Verified QUITTER customer" : null}
                    </figcaption>
                  </figure>
                </Reveal>
              ))}
            </div>
          ) : (
            <Reveal delay={80}>
              <div className="flex h-full min-h-[13rem] flex-col justify-between rounded-[18px] border border-dashed border-charcoal/15 p-8">
                <p className="text-mono uppercase text-label">Reserved for verified reviews</p>
                <p className="mt-6 max-w-md text-[0.9375rem] leading-relaxed text-charcoal/65">
                  Reviews appear here automatically once verified customers have finished a
                  programme. Nothing in this space is written by us.
                </p>
              </div>
            </Reveal>
          )}
        </div>
      </Container>
    </Section>
  );
}
