/** The 90-day journey. Milestones are motivational, not medical. */

export type Milestone = {
  day: string;
  label: string;
  title: string;
  body: string;
  /** Position on the progress line, 0–1. */
  progress: number;
};

export const timeline: Milestone[] = [
  {
    day: "Day 01",
    label: "Start",
    title: "The decision is made.",
    body: "Your programme arrives. You open box one and set your date. Nothing to work out, nothing to buy again this month.",
    progress: 0,
  },
  {
    day: "Day 30",
    label: "Keep going",
    title: "The routine takes over.",
    body: "The first month is the loudest. By day 30 the plan is doing the remembering for you.",
    progress: 0.33,
  },
  {
    day: "Day 60",
    label: "Almost there",
    title: "Less of it, more of you.",
    body: "Two thirds through. The programme steps down while your days carry on as normal.",
    progress: 0.66,
  },
  {
    day: "Day 90",
    label: "You did it.",
    title: "Ninety days, finished.",
    body: "The last box closes. You started this on one decision and you carried it for a quarter of a year.",
    progress: 1,
  },
];

export const timelineOutro = {
  label: "Unlocked",
  title: "QUITTER ZERO",
  body: "Your completion package. Not for sale. Only for people who finish.",
} as const;

export const howItWorksSteps = [
  {
    number: "01",
    title: "Choose your programme",
    body: "Light, Regular or Intense. Ninety days, one price, one delivery.",
  },
  {
    number: "02",
    title: "Receive QUITTER",
    body: "Everything you need for the full programme, in one plain box at your door.",
  },
  {
    number: "03",
    title: "Complete 90 days",
    body: "Follow the plan through day 90 — and unlock QUITTER ZERO.",
  },
] as const;
