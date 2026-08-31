import { Container, Eyebrow, Section } from "@/components/ui/Section";
import { Reveal } from "@/components/ui/Reveal";

const pillars = [
  {
    title: "One plan, not a shelf",
    body: "You do not need to work out how many boxes a quarter takes. The programme already did.",
  },
  {
    title: "One price, no renewal",
    body: "Ninety days for a fixed price. Nothing charges itself again unless you ask it to.",
  },
  {
    title: "One box at the door",
    body: "Discreet packaging, free delivery, nothing on the outside that announces itself.",
  },
  {
    title: "One finish line",
    body: "Day 90 is a real end point — and the only way to unlock QUITTER ZERO.",
  },
];

/** The 'why QUITTER' beat between the hero and the offer. */
export function Manifesto() {
  return (
    <Section tone="bone" size="default">
      <Container>
        <div className="grid gap-14 lg:grid-cols-[0.9fr_1.1fr] lg:gap-20">
          <Reveal>
            <Eyebrow>Why QUITTER</Eyebrow>
            <h2 className="mt-5 max-w-lg text-headline">
              Quitting is a journey. Most products sell you a box.
            </h2>
            <p className="mt-7 max-w-md text-lede text-charcoal/65">
              QUITTER is the same nicotine replacement medicine you already know, organised
              the way people actually quit: as a programme with a start, a middle and an end.
            </p>
          </Reveal>

          <div className="grid gap-px overflow-hidden rounded-[20px] bg-charcoal/10 sm:grid-cols-2">
            {pillars.map((pillar, index) => (
              <Reveal key={pillar.title} delay={index * 80} className="bg-bone">
                <div className="h-full bg-bone p-8 sm:p-10">
                  <h3 className="text-[1.0625rem] font-semibold tracking-[-0.015em]">
                    {pillar.title}
                  </h3>
                  <p className="mt-3 text-[0.9375rem] leading-relaxed text-charcoal/65">
                    {pillar.body}
                  </p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </Container>
    </Section>
  );
}
