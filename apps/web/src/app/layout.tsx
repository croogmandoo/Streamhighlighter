import type { Metadata } from "next";

import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "StreamHighlighter — VODs into Shorts, automatically",
  description:
    "Connect Twitch/YouTube, and let AI cut your VODs into publish-ready Shorts, Reels, and TikToks plus a tightened re-cut.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
