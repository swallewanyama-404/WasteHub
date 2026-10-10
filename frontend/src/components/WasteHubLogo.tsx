import { Link } from "react-router-dom";

export function WasteHubMark({ size = 42 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      aria-hidden="true"
      className="brand-mark"
    >
      <defs>
        <linearGradient id="wh-green" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#7ddc45" />
          <stop offset="100%" stopColor="#0b7a46" />
        </linearGradient>
      </defs>
      <path
        d="M32 3C17 3 7 14 7 28c0 18 25 33 25 33s25-15 25-33C57 14 47 3 32 3Z"
        fill="url(#wh-green)"
      />
      <path d="M18 22h22l7 8v12H18V22Z" fill="#fff" opacity=".96" />
      <path d="M40 26h7l6 7v9H40V26Z" fill="#f8fff9" />
      <circle cx="27" cy="43" r="5" fill="#063d2d" />
      <circle cx="46" cy="43" r="5" fill="#063d2d" />
      <circle cx="27" cy="43" r="2.2" fill="#fff" />
      <circle cx="46" cy="43" r="2.2" fill="#fff" />
      <path d="M22 31c4-7 10-9 16-9-3 6-7 11-16 12" fill="#79d640" />
      <path d="M20 37c8-2 14-7 18-14" stroke="#0b7a46" strokeWidth="2" fill="none" />
      <circle cx="12" cy="31" r="3" fill="#ffc928" />
      <circle cx="55" cy="36" r="3" fill="#ffc928" />
    </svg>
  );
}

export function WasteHubLogo({
  to = "/",
  compact = false,
}: {
  to?: string;
  compact?: boolean;
}) {
  return (
    <Link to={to} className={compact ? "brand-lockup compact" : "brand-lockup"}>
      <WasteHubMark size={compact ? 36 : 44} />
      <span className="brand-word">
        Waste<span>Hub</span>
      </span>
    </Link>
  );
}
